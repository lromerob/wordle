[CmdletBinding()]
param([ValidateSet('Build','Validate','Activate','Stop')][string]$Action='Validate',[string]$ConfigurationFile,
      [string]$StorePath,[string]$StoreId,[switch]$SyntheticFixture,[switch]$StorageApproved,[string]$BackupProcedureReference,[switch]$AuthorizeRegistrationAndListener)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Test-WordlePrivateStore.ps1')

function Assert-WordleRunnerConfig {
    param($Config,[string]$ApprovedPath,[string]$ApprovedId,[string]$ApprovalDirectory,[string]$Model,[string]$ExpectedCommand="validate")
    $network=if($ExpectedCommand -eq "activate"){"bridge"}else{"none"}
    $services=@($Config.services.PSObject.Properties)
    if($services.Count -ne 1 -or $services[0].Name -ne 'wordle-actions-runner'){throw 'Unexpected Compose services'}
    $service=$Config.services.'wordle-actions-runner'
    if($service.user -ne '10001:10001' -or $service.privileged -or ($null -ne $service.ports -and @($service.ports).Count -gt 0) -or $service.entrypoint -or $service.network_mode -ne $network){throw 'Unexpected runner exposure/configuration'}
    if($service.image -ne 'wordle-actions-runner:fin17-private-store-02' -or @($service.cap_drop) -notcontains 'ALL' -or @($service.security_opt) -notcontains 'no-new-privileges:true'){throw 'Unexpected runner security/image'}
    if($service.environment.WORDLE_STORE_MODEL -ne $Model -or $service.environment.WORDLE_AZURE_STORE_ID -cne $ApprovedId -or $service.environment.WORDLE_AZURE_PRIVATE_DIR -ne '/wordle-private'){throw 'Store configuration mismatch'}
    if(@($service.command).Count -ne 1 -or $service.command[0] -ne $ExpectedCommand){throw 'Unexpected runner command'}
    if($ExpectedCommand -eq 'activate' -and ($Model -ne 'windows-supervised' -or $service.environment.WORDLE_RUNNER_AUTHORIZED_ACTION -ne 'REGISTER_RUN')){throw 'Explicit production activation authorization required'}
    $volumes=@($service.volumes)
    if($volumes.Count -ne 2){throw 'Exactly two approved binds required'}
    $store=@($volumes|Where-Object target -eq '/wordle-private')
    $approval=@($volumes|Where-Object target -eq '/run/wordle-host')
    if($store.Count -ne 1 -or $approval.Count -ne 1){throw 'Approved mount targets required'}
    if($store[0].type -ne 'bind' -or $store[0].bind.create_host_path -ne $false -or $store[0].read_only){throw 'Invalid store bind'}
    if($approval[0].type -ne 'bind' -or $approval[0].read_only -ne $true -or $approval[0].bind.create_host_path -ne $false){throw 'Read-only host approval bind required'}
    $actual=[IO.Path]::GetFullPath($store[0].source).TrimEnd('\')
    $control=[IO.Path]::GetFullPath($approval[0].source).TrimEnd('\')
    if(-not $actual.Equals($ApprovedPath,[StringComparison]::OrdinalIgnoreCase) -or -not $control.Equals($ApprovalDirectory,[StringComparison]::OrdinalIgnoreCase)){throw 'Compose bind differs from approved host path'}
}

function New-WordleControlDirectory {
    $directory=[IO.DirectoryInfo]::new((Join-Path ([IO.Path]::GetTempPath()) ('wordle-host-approval-'+[guid]::NewGuid().ToString('N'))))
    if($directory.Exists){throw 'Control directory already exists'}
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl=[Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner($identity);$acl.SetAccessRuleProtection($true,$false)
    foreach($sid in @($identity.Value,'S-1-5-18','S-1-5-32-544')){
        $rule=[Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),[Security.AccessControl.FileSystemRights]::FullControl,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    # ACL is specified when creating this NEW disposable control directory. Never Set-Acl
    # on a preexisting real store, parent, configuration file or user directory.
    [IO.FileSystemAclExtensions]::Create($directory,$acl)
    return $directory.FullName
}

function Invoke-WordleRunner {
    if(-not $IsWindows){throw 'Windows host and PowerShell 7 required'}
    if(-not $ConfigurationFile -or -not [IO.Path]::IsPathFullyQualified($ConfigurationFile) -or -not(Test-Path -LiteralPath $ConfigurationFile -PathType Leaf)){throw 'Explicit existing external secret-free configuration required'}
    $repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
    $cfg=[IO.Path]::GetFullPath($ConfigurationFile)
    if($cfg.StartsWith($repo+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Configuration must be external'}
    $configItem=Get-Item -LiteralPath $cfg -Force
    $cursor=$configItem
    while($null -ne $cursor){
        if(($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Configuration redirection rejected'}
        $cursor=if($cursor.PSIsContainer){$cursor.Parent}else{$cursor.Directory}
    }
    $compose=Join-Path $PSScriptRoot 'compose.yaml'
    if($Action -eq 'Stop'){
        $raw=& docker inspect wordle-actions-runner-session 2>$null
        if($LASTEXITCODE -ne 0){Write-Host 'No named Wordle runner session exists.';return}
        $info=@($raw|ConvertFrom-Json)[0]
        if($info.Config.Labels.'com.docker.compose.project' -ne 'wordle-docker-runner' -or $info.Config.Labels.'com.docker.compose.service' -ne 'wordle-actions-runner'){throw 'Refuse to stop foreign container'}
        & docker stop --time 30 wordle-actions-runner-session
        if($LASTEXITCODE -ne 0){throw 'Runner stop failed'}
        return
    }
    if($Action -eq 'Build'){
        & docker compose --env-file $cfg --file $compose build wordle-actions-runner
        if($LASTEXITCODE -ne 0){throw 'Runner image build failed'}
        return # Build never starts a container or authorizes a store.
    }
    if($Action -eq 'Activate' -and (-not $AuthorizeRegistrationAndListener -or $SyntheticFixture)){throw 'Separate real registration/listener authorization required; fixtures forbidden'}
    $preflight=Get-WordleStorePreflight -Path $StorePath -ExpectedId $StoreId -Fixture $SyntheticFixture.IsPresent -Approved $StorageApproved.IsPresent -BackupReference $BackupProcedureReference
    if($preflight.status -ne 'PASS'){throw 'Windows preflight rejected; Docker was not started'}
    $control=New-WordleControlDirectory
    $sessionName=$null
    $sessionId=[guid]::NewGuid().ToString()
    try {
        $model=if($SyntheticFixture){'windows-supervised-test'}else{'windows-supervised'}
        $command=if($Action -eq 'Activate'){'activate'}else{'validate'}
        $network=if($Action -eq 'Activate'){'bridge'}else{'none'}
        $environment=@{WORDLE_STORE_MODEL=$model}
        if($Action -eq 'Activate'){$environment.WORDLE_RUNNER_AUTHORIZED_ACTION='REGISTER_RUN'}
        $override=@{services=@{'wordle-actions-runner'=@{network_mode=$network;command=@($command);environment=$environment;volumes=@(@{type='bind';source=$control;target='/run/wordle-host';read_only=$true;bind=@{create_host_path=$false}})}}}
        $overrideFile=Join-Path $control 'override.json'
        $override|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $overrideFile -Encoding utf8NoBOM
        $raw=& docker compose --env-file $cfg --file $compose --file $overrideFile config --format json
        if($LASTEXITCODE -ne 0){throw 'Compose render failed'}
        $config=($raw -join "`n")|ConvertFrom-Json
        Assert-WordleRunnerConfig -Config $config -ApprovedPath $preflight.host_path -ApprovedId $StoreId -ApprovalDirectory $control -Model $model -ExpectedCommand $command
        # Recheck host ACL/identity immediately before issuing this invocation's receipt.
        $latest=Get-WordleStorePreflight -Path $StorePath -ExpectedId $StoreId -Fixture $SyntheticFixture.IsPresent -Approved $StorageApproved.IsPresent -BackupReference $BackupProcedureReference
        if($latest.status -ne 'PASS' -or $latest.acl_sha256 -ne $preflight.acl_sha256 -or $latest.marker_sha256 -ne $preflight.marker_sha256 -or $latest.host_path -ne $preflight.host_path){throw 'Store changed during preflight'}
        $issued=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $receipt=@{format=1;repository='lromerob/wordle';issuer='Invoke-WordleRunner.ps1';policy=$preflight.policy;store_id=$StoreId;host_path=$preflight.host_path;container_path='/wordle-private';marker_sha256=$preflight.marker_sha256;acl_sha256=$preflight.acl_sha256;session_id=$sessionId;issued_at=$issued;expires_at=$issued+21600;fixture_only=$SyntheticFixture.IsPresent}
        $receipt|ConvertTo-Json -Compress|Set-Content -LiteralPath (Join-Path $control 'approval.json') -Encoding utf8NoBOM
        # Freeze the verified effective config; no second env interpolation may change its binds.
        $frozen=Join-Path $control 'validated-compose.json'
        $config|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $frozen -Encoding utf8NoBOM
        $sessionName=if($Action -eq 'Activate'){'wordle-actions-runner-session'}else{'wordle-runner-supervised-'+[guid]::NewGuid().ToString('N')}
        $arguments=@('compose','--file',$frozen,'run','--rm','--no-deps','-T','--name',$sessionName,'--label',"wordle.tfg.supervised=$sessionId",'wordle-actions-runner',$command)
        if($Action -eq 'Activate'){
            # FUTURE ONLY: never called by validation. Token is read AFTER all host gates.
            $registration=Read-Host 'Ephemeral Wordle registration token, separately authorized' -MaskInput
            try {$registration | & docker @arguments} finally {Remove-Variable registration -ErrorAction SilentlyContinue}
        } else {& docker @arguments}
        if($LASTEXITCODE -ne 0){throw 'Supervised local container validation failed'}
    } finally {
        if($sessionName){
            $existing=& docker inspect $sessionName 2>$null
            if($LASTEXITCODE -eq 0){
                $owned=@($existing|ConvertFrom-Json)[0]
                if($owned.Config.Labels.'wordle.tfg.supervised' -ne $sessionId){throw 'Refuse cleanup of foreign session'}
                & docker stop --time 10 $sessionName | Out-Null
                if($LASTEXITCODE -ne 0){throw 'Owned session stop failed; preserve control directory'}
                & docker rm $sessionName | Out-Null
                # --rm may already have removed it after stop; never force-remove.
            }
        }
        $target=[IO.Path]::GetFullPath($control)
        $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
        if([IO.Path]::GetDirectoryName($target) -ne $parent -or -not [IO.Path]::GetFileName($target).StartsWith('wordle-host-approval-')){throw 'Unsafe control directory cleanup'}
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
if($MyInvocation.InvocationName -ne '.'){
    try {Invoke-WordleRunner;exit 0} catch {[Console]::Error.WriteLine('Wordle runner refused: preflight/configuration/runtime failure.');exit 2}
}
