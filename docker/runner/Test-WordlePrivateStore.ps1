[CmdletBinding()]
param([Alias("StorePath")][string]$InspectPath,[Alias("StoreId")][string]$InspectId,[Alias("SyntheticFixture")][switch]$InspectFixture,[Alias("StorageApproved")][switch]$InspectApproved,[Alias("BackupProcedureReference")][string]$InspectBackup)
$ErrorActionPreference='Stop'

function Assert-WordleAclPolicy {
    param($OwnerSid,$OperatorSid,[bool]$Canonical,[bool]$DaclPresent,$Rules)
    if(-not $Canonical -or -not $DaclPresent -or $OwnerSid -ne $OperatorSid){throw 'ACL_OWNER_OR_DESCRIPTOR'}
    $trusted=@($OperatorSid,'S-1-5-18','S-1-5-32-544')
    $operatorControl=$false
    foreach($rule in @($Rules)){
        # Conservative supported subset, not an AccessCheck implementation.
        # Inherited ACEs are evaluated by identity/rights, never rejected for inheritance alone.
        if($rule.Type -ne 'Allow' -or $rule.Sid -notin $trusted){throw 'ACL_UNSUPPORTED_OR_UNAPPROVED_PRINCIPAL'}
        if($rule.Sid -eq $OperatorSid -and -not $rule.InheritOnly -and ($rule.Rights -band 2032127) -eq 2032127){$operatorControl=$true}
    }
    if(-not $operatorControl){throw 'ACL_OPERATOR_FULL_CONTROL_REQUIRED'}
}

function Get-WordleStorePreflight {
    param([string]$Path,[string]$ExpectedId,[bool]$Fixture,[bool]$Approved,[string]$BackupReference)
    $stage='PATH'
    try {
        if(-not $IsWindows -or -not [IO.Path]::IsPathFullyQualified($Path) -or $Path.StartsWith('\\')){throw 'ABSOLUTE_LOCAL_WINDOWS_PATH_REQUIRED'}
        $item=Get-Item -LiteralPath $Path -Force
        if(-not $item.PSIsContainer){throw 'EXISTING_DIRECTORY_REQUIRED'}
        $canonical=[IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
        $drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($canonical))
        if(-not $drive.IsReady -or $drive.DriveType -ne [IO.DriveType]::Fixed -or $drive.DriveFormat -ne 'NTFS'){throw 'LOCAL_FIXED_NTFS_REQUIRED'}
        $repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
        if($canonical.Equals($repo,[StringComparison]::OrdinalIgnoreCase) -or $canonical.StartsWith($repo+'\',[StringComparison]::OrdinalIgnoreCase) -or $repo.StartsWith($canonical+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'STORE_MUST_BE_EXTERNAL'}
        $cursor=$item
        while($null -ne $cursor){
            if(($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'REPARSE_POINT_REJECTED'}
            $cursor=$cursor.Parent
        }
        $stage='IDENTITY'
        $uuid=[guid]::Empty
        if(-not [guid]::TryParseExact($ExpectedId,'D',[ref]$uuid)){throw 'EXPLICIT_UUID_REQUIRED'}
        $marker=Join-Path $canonical '.wordle-private-store.json'
        $objects=@($item)
        # Metadata only on descendants. Reparse points are rejected before recursion.
        $pending=[Collections.Generic.Queue[IO.DirectoryInfo]]::new();$pending.Enqueue($item)
        while($pending.Count -gt 0){
            $directory=$pending.Dequeue()
            foreach($child in @(Get-ChildItem -LiteralPath $directory.FullName -Force)){
                if(($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'REPARSE_POINT_REJECTED'}
                $objects+=,$child
                if($child.PSIsContainer){$pending.Enqueue($child)}
            }
        }
        foreach($name in @('plans','selections','evidence','backups')){
            if(-not(Test-Path -LiteralPath (Join-Path $canonical $name) -PathType Container)){throw 'MISSING_REQUIRED_DIRECTORY'}
        }
        $stage='ACL'
        $operator=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        $fingerprints=[Collections.Generic.List[string]]::new()
        foreach($object in $objects){
            $acl=Get-Acl -LiteralPath $object.FullName
            $raw=[Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)
            if($null -eq $raw.DiscretionaryAcl){throw 'NULL_DACL_REJECTED'}
            foreach($ace in $raw.DiscretionaryAcl){
                if($ace.AceType -ne [Security.AccessControl.AceType]::AccessAllowed){throw 'UNSUPPORTED_ACE_REJECTED'}
            }
            $rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])|ForEach-Object{
                [pscustomobject]@{Sid=$_.IdentityReference.Value;Type=$_.AccessControlType.ToString();Rights=[int64]$_.FileSystemRights;InheritOnly=(($_.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0)}
            })
            Assert-WordleAclPolicy -OwnerSid $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -OperatorSid $operator -Canonical $acl.AreAccessRulesCanonical -DaclPresent ($null -ne $raw.DiscretionaryAcl) -Rules $rules
            $relative=[IO.Path]::GetRelativePath($canonical,$object.FullName)
            $sddl=$acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Owner)
            $fingerprints.Add($relative+':'+$sddl)
        }
        $stage='MARKER'
        # Only the contractual marker is read; variables/backend/credentials are never opened.
        $data=Get-Content -LiteralPath $marker -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
        $expected=@{format=[long]1;repository='lromerob/wordle';store_id=$ExpectedId;durable_acknowledged=$true}
        if($Fixture){$expected.durable_acknowledged=$false;$expected.synthetic_fixture=$true}
        if($data.Count -ne $expected.Count){throw 'MARKER_STRUCTURE_MISMATCH'}
        foreach($key in $expected.Keys){
            if(-not $data.ContainsKey($key) -or $data[$key].GetType() -ne $expected[$key].GetType() -or $data[$key] -cne $expected[$key]){throw 'MARKER_IDENTITY_OR_APPROVAL_MISMATCH'}
        }
        if(-not $Fixture -and (-not $Approved -or [string]::IsNullOrWhiteSpace($BackupReference))){throw 'HUMAN_STORAGE_AND_BACKUP_APPROVAL_REQUIRED'}
        $aclHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes((($fingerprints|Sort-Object) -join "`n")))).ToLowerInvariant()
        return [pscustomobject]@{status='PASS';path_checked=$true;acl_checked=$true;policy='owner-system-administrators-v1';host_path=$canonical;store_id=$ExpectedId;fixture_only=$Fixture;marker_sha256=(Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash.ToLowerInvariant();acl_sha256=$aclHash;reason='Supported conservative local ACL policy satisfied; not AccessCheck or continuous monitoring.'}
    } catch {
        return [pscustomobject]@{status='BLOCKED';stage=$stage;reason='Store preflight failed at '+$stage+'; no approval issued.'}
    }
}

if($MyInvocation.InvocationName -ne '.'){
    $result=Get-WordleStorePreflight -Path $InspectPath -ExpectedId $InspectId -Fixture $InspectFixture.IsPresent -Approved $InspectApproved.IsPresent -BackupReference $InspectBackup
    $result|ConvertTo-Json -Compress
    if($result.status -ne 'PASS'){exit 2}
}
