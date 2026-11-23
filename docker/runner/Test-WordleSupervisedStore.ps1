[CmdletBinding()]
param([switch]$RunDocker)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Invoke-WordleRunner.ps1')
$script:passed=0
function Assert-Case([bool]$Condition,[string]$Name){if(-not $Condition){throw ('Test failed: '+$Name)};$script:passed++}
function Assert-Rejected([scriptblock]$Code,[string]$Name){$rejected=$false;try {& $Code}catch {$rejected=$true};Assert-Case $rejected $Name}
$root=New-WordleControlDirectory
try {
    $store=Join-Path $root 'synthetic-store';$null=New-Item -ItemType Directory -Path $store
    $id='11111111-1111-4111-8111-111111111111'
    foreach($dir in @('plans','selections','evidence','backups')){$null=New-Item -ItemType Directory -Path (Join-Path $store $dir)}
    $marker=Join-Path $store '.wordle-private-store.json'
    $synthetic=@{format=1;repository='lromerob/wordle';store_id=$id;durable_acknowledged=$false;synthetic_fixture=$true}
    $synthetic|ConvertTo-Json -Compress|Set-Content -LiteralPath $marker -Encoding utf8NoBOM
    $good=Get-WordleStorePreflight -Path $store -ExpectedId $id -Fixture $true -Approved $false -BackupReference ''
    Assert-Case ($good.status -eq 'PASS') ('synthetic host preflight ('+$good.stage+')')
    $operator=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $rule=[pscustomobject]@{Sid=$operator;Type='Allow';Rights=2032127;InheritOnly=$false}
    Assert-WordleAclPolicy -OwnerSid $operator -OperatorSid $operator -Canonical $true -DaclPresent $true -Rules @($rule)
    $script:passed++
    $broad=[pscustomobject]@{Sid='S-1-1-0';Type='Allow';Rights=2032127;InheritOnly=$false}
    Assert-Rejected {Assert-WordleAclPolicy $operator $operator $true $true @($rule,$broad)} 'broad write ACE rejection'
    Assert-Rejected {Assert-WordleAclPolicy $operator $operator $true $false @($rule)} 'null DACL rejection'
    Assert-Rejected {Assert-WordleAclPolicy $operator $operator $false $true @($rule)} 'noncanonical DACL rejection'
    Assert-Rejected {Assert-WordleAclPolicy 'S-1-5-18' $operator $true $true @($rule)} 'unexpected owner rejection'
    $deny=[pscustomobject]@{Sid=$operator;Type='Deny';Rights=1;InheritOnly=$false}
    Assert-Rejected {Assert-WordleAclPolicy $operator $operator $true $true @($rule,$deny)} 'unsupported deny rejection'
    foreach($case in @(
        @{name='missing path';path=(Join-Path $root 'absent');uuid=$id},
        @{name='checkout';path=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));uuid=$id},
        @{name='wrong UUID';path=$store;uuid='22222222-2222-4222-8222-222222222222'}
    )){
        $bad=Get-WordleStorePreflight -Path $case.path -ExpectedId $case.uuid -Fixture $true -Approved $false -BackupReference ''
        Assert-Case ($bad.status -eq 'BLOCKED') $case.name
    }
    # Intentionally unsafe ACL on a NEW synthetic fixture, never a preexisting path.
    $unsafe=Join-Path $root 'unsafe-synthetic-store'
    $unsafeAcl=[Security.AccessControl.DirectorySecurity]::new()
    $unsafeAcl.SetOwner([Security.Principal.SecurityIdentifier]::new($operator));$unsafeAcl.SetAccessRuleProtection($true,$false)
    foreach($sid in @($operator,'S-1-5-18','S-1-5-32-544','S-1-1-0')){
        $unsafeAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),[Security.AccessControl.FileSystemRights]::FullControl,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
    }
    [IO.FileSystemAclExtensions]::Create([IO.DirectoryInfo]::new($unsafe),$unsafeAcl)
    foreach($dir in @('plans','selections','evidence','backups')){$null=New-Item -ItemType Directory -Path (Join-Path $unsafe $dir)}
    $synthetic|ConvertTo-Json -Compress|Set-Content -LiteralPath (Join-Path $unsafe '.wordle-private-store.json') -Encoding utf8NoBOM
    $bad=Get-WordleStorePreflight -Path $unsafe -ExpectedId $id -Fixture $true -Approved $false -BackupReference ''
    Assert-Case ($bad.status -eq 'BLOCKED' -and $bad.stage -eq 'ACL') 'real NTFS broad ACL rejection'
    $prod=Get-WordleStorePreflight -Path $store -ExpectedId $id -Fixture $false -Approved $false -BackupReference ''
    Assert-Case ($prod.status -eq 'BLOCKED') 'fixture not production approval'
    $synthetic|ConvertTo-Json -Compress|Set-Content -LiteralPath $marker -Encoding utf8NoBOM
    Rename-Item -LiteralPath $marker -NewName 'marker.suspended'
    $bad=Get-WordleStorePreflight -Path $store -ExpectedId $id -Fixture $true -Approved $false -BackupReference ''
    Assert-Case ($bad.status -eq 'BLOCKED') 'missing marker'
    Rename-Item -LiteralPath (Join-Path $store 'marker.suspended') -NewName '.wordle-private-store.json'
    Remove-Item -LiteralPath (Join-Path $store 'backups')
    $bad=Get-WordleStorePreflight -Path $store -ExpectedId $id -Fixture $true -Approved $false -BackupReference ''
    Assert-Case ($bad.status -eq 'BLOCKED') 'incomplete structure'
    $null=New-Item -ItemType Directory -Path (Join-Path $store 'backups')
    $control=Join-Path $root 'control';$null=New-Item -ItemType Directory -Path $control
    $configuration=[pscustomobject]@{services=[pscustomobject]@{'wordle-actions-runner'=[pscustomobject]@{
        user='10001:10001';command=@('validate');image='wordle-actions-runner:fin17-private-store-02';cap_drop=@('ALL');security_opt=@('no-new-privileges:true');network_mode='none';environment=[pscustomobject]@{WORDLE_STORE_MODEL='windows-supervised-test';WORDLE_AZURE_STORE_ID=$id;WORDLE_AZURE_PRIVATE_DIR='/wordle-private'};
        volumes=@([pscustomobject]@{type='bind';source=$store;target='/wordle-private';bind=[pscustomobject]@{create_host_path=$false}},[pscustomobject]@{type='bind';source=$control;target='/run/wordle-host';read_only=$true;bind=[pscustomobject]@{create_host_path=$false}})
    }}}
    Assert-WordleRunnerConfig $configuration $store $id $control 'windows-supervised-test';$script:passed++
    Assert-Rejected {Assert-WordleRunnerConfig $configuration (Join-Path $root 'different') $id $control 'windows-supervised-test'} 'different approved path'
    $configuration.services.'wordle-actions-runner'.volumes[0].source=$root
    Assert-Rejected {Assert-WordleRunnerConfig $configuration $store $id $control 'windows-supervised-test'} 'different bind mount'
    $configuration.services.'wordle-actions-runner'.volumes[0].source=$store
    $configuration.services.'wordle-actions-runner'.volumes[1].read_only=$false
    Assert-Rejected {Assert-WordleRunnerConfig $configuration $store $id $control 'windows-supervised-test'} 'writable host approval'
    $ConfigurationFile=Join-Path $root 'runner.env'
    @(('WORDLE_PRIVATE_HOST_DIR='+$store.Replace('\','/')),('WORDLE_AZURE_STORE_ID='+$id))|Set-Content -LiteralPath $ConfigurationFile -Encoding utf8NoBOM
    $StoreId=$id;$StorePath=Join-Path $root 'missing';$SyntheticFixture=[switch]$true;$Action='Validate'
    $script:dockerCalls=0
    function docker {$script:dockerCalls++;throw 'Docker must not run after failed preflight'}
    Assert-Rejected {Invoke-WordleRunner} 'failed preflight blocks launch'
    Assert-Case ($script:dockerCalls -eq 0) 'no Docker call after failed preflight'
    $StorePath=$unsafe
    Assert-Rejected {Invoke-WordleRunner} 'real broad ACL blocks launch'
    Assert-Case ($script:dockerCalls -eq 0) 'no Docker call after rejected ACL'
    Remove-Item Function:docker
    $Action='Activate';$StorePath=$store;$AuthorizeRegistrationAndListener=[switch]$false
    Assert-Rejected {Invoke-WordleRunner} 'activation requires separate authorization'
    $AuthorizeRegistrationAndListener=[switch]$true
    Assert-Rejected {Invoke-WordleRunner} 'synthetic activation forbidden'
    Assert-Case ($script:dockerCalls -eq 0) 'no activation or token request for fixture'
    $Action='Validate'
    $runtime=$null
    if($RunDocker){
        $runtimeOutput=& (Join-Path $PSScriptRoot 'Invoke-WordleRunner.ps1') -Action Validate -ConfigurationFile $ConfigurationFile -StorePath $store -StoreId $id -SyntheticFixture
        if($LASTEXITCODE -ne 0){throw 'Real supervised launcher failed'}
        $runtime=($runtimeOutput -join "`n")|ConvertFrom-Json
        Assert-Case ($runtime.store_validated -eq $true -and $runtime.store_model -eq 'windows-supervised-test' -and -not $runtime.registered) 'real Windows supervised container'
        $image='wordle-actions-runner:fin17-private-store-02'
        $refusal=& docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges=true --env WORDLE_STORE_MODEL=windows-supervised-test --env "WORDLE_AZURE_STORE_ID=$id" --mount "type=bind,source=$store,target=/wordle-private" $image validate 2>&1
        Assert-Case ($LASTEXITCODE -eq 1 -and ($refusal -join "`n").Trim() -eq 'Runner refused: ValueError') 'real container rejects env without host receipt'
        @{approved=$true;store_id=$id}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $store 'approval.json') -Encoding utf8NoBOM
        $refusal=& docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges=true --env WORDLE_STORE_MODEL=windows-supervised-test --env "WORDLE_AZURE_STORE_ID=$id" --mount "type=bind,source=$store,target=/wordle-private" $image validate 2>&1
        Assert-Case ($LASTEXITCODE -eq 1 -and ($refusal -join "`n").Trim() -eq 'Runner refused: ValueError') 'real container rejects receipt created in store'
        $held='wordle-runner-stop-test-'+[guid]::NewGuid().ToString('N')
        $label=[guid]::NewGuid().ToString('N')
        try {
            & docker run -d --name $held --label "wordle.tfg.stop-test=$label" --network none --cap-drop ALL --security-opt no-new-privileges=true $image validate-hold | Out-Null
            if($LASTEXITCODE -ne 0){throw 'Owned hold container creation failed'}
            $ready=$false
            for($attempt=0;$attempt -lt 30;$attempt++){
                $logs=& docker logs $held
                if($logs){$ready=$true;break}
                Start-Sleep -Milliseconds 300
            }
            Assert-Case $ready 'validation hold ready without listener'
            & docker stop --time 10 $held | Out-Null
            $info=@((& docker inspect $held)|ConvertFrom-Json)[0]
            Assert-Case ($info.State.ExitCode -eq 0 -and -not $info.State.Running) 'clean SIGTERM stop'
        } finally {
            $found=& docker inspect $held 2>$null
            if($LASTEXITCODE -eq 0){
                $info=@($found|ConvertFrom-Json)[0]
                if($info.Config.Labels.'wordle.tfg.stop-test' -ne $label){throw 'Refuse foreign hold cleanup'}
                if($info.State.Running){& docker stop --time 10 $held | Out-Null}
                & docker rm $held | Out-Null
            }
        }
    }
    [pscustomobject]@{host_assertions_passed=$script:passed;runtime=$runtime;synthetic_only=$true;real_durability_approval=$false;existing_acl_modified=$false}|ConvertTo-Json -Depth 8
} finally {
    $target=[IO.Path]::GetFullPath($root)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if([IO.Path]::GetDirectoryName($target) -ne $parent -or -not [IO.Path]::GetFileName($target).StartsWith('wordle-host-approval-')){throw 'Unsafe fixture cleanup'}
    Remove-Item -LiteralPath $target -Recurse -Force
}
