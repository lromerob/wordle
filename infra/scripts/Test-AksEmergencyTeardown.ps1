# No Pester dependency. All native invocation is replaced before exercising any mode.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Invoke-AksEmergencyTeardown.ps1')
$script:Sub='11111111-1111-4111-8111-111111111111'
$script:Tenant='22222222-2222-4222-8222-222222222222'
$script:User='33333333-3333-4333-8333-333333333333'
$originalRoot=$script:Root
$originalLocal=$env:LOCALAPPDATA
$temp=Join-Path ([IO.Path]::GetTempPath()) ('wordle-emergency-tests-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $temp
$passed=0
function Tools($Explicit){
    if($script:Case -eq 'terraform-missing'){throw 'TERRAFORM_MISSING'}
    if($script:Case -eq 'az-missing'){throw 'AZURE_CLI_MISSING'}
    return @{tf='MOCK_TERRAFORM';az='MOCK_AZURE'}
}
function Consent($Prompt){
    if($Prompt -like '*SOLO*'){return 'PLAN WORDLE AKS'}
    if($script:Case -eq 'wrong-confirmation'){return ''}
    if($script:Case -eq 'tampered-plan'){[IO.File]::WriteAllText($script:SavedPlan,'tampered')}
    return 'DESTRUIR WORDLE AKS'
}
function Native([string]$Tool,[string[]]$Arguments){
    # No fallback to &, Start-Process, subprocess, Azure or Terraform.
    $script:Calls+=($Tool+' '+($Arguments -join ' '))
    if($Tool -notin @('MOCK_TERRAFORM','MOCK_AZURE')){throw 'UNMOCKED_TOOL'}
    $a=$Arguments
    if($Tool -eq 'MOCK_TERRAFORM'){
        switch($a[0]){
            'version' {
                $v=if($script:Case -eq 'wrong-version'){'0.0.0'}else{'1.9.8'}
                return (@{terraform_version=$v;provider_selections=@{'registry.terraform.io/hashicorp/azurerm'='4.50.0'};ignored='SYNTHETIC_SENSITIVE_SENTINEL'}|ConvertTo-Json -Depth 8 -Compress)
            }
            'state' {
                if($script:Case -eq 'state-inaccessible'){throw 'STATE_UNAVAILABLE'}
                if($script:Applied -or $script:Case -in @('empty','empty-orphan')){return ''}
                if($script:Case -eq 'unexpected-state'){return 'azurerm_storage_account.foreign'}
                return 'azurerm_resource_group.wordle'
            }
            'validate' {return 'valid'}
            'plan' {
                if($script:Case -eq 'plan-lock'){throw 'STATE_LOCKED'}
                $script:SavedPlan=($a|Where-Object{$_ -like '-out=*'}).Substring(5)
                [IO.File]::WriteAllText($script:SavedPlan,'offline-plan')
                return 'Plan: 1 to destroy'
            }
            'show' {
                $address='azurerm_resource_group.wordle';$id='/subscriptions/'+$script:Sub+'/resourceGroups/rg-wordle-academic';$actions=@('delete')
                if($script:Case -eq 'backend-plan'){$id='/subscriptions/'+$script:Sub+'/resourceGroups/rg-wordle-state'}
                if($script:Case -eq 'unexpected-plan'){$address='azurerm_storage_account.foreign'}
                if($script:Case -eq 'unexpected-actions'){$actions=@('update')}
                return (@{resource_changes=@(@{address=$address;mode='managed';change=@{actions=$actions;before=@{id=$id}}})}|ConvertTo-Json -Depth 12 -Compress)
            }
            'apply' {
                if($script:Case -eq 'destroy-failure'){throw 'TOOL_FAILED'}
                $script:Applied=$true;return 'done'
            }
            default {throw 'UNMOCKED_TERRAFORM_COMMAND'}
        }
    }
    if($a[0] -eq 'account'){
        if($script:Case -eq 'mfa'){throw 'AUTHENTICATION_REQUIRED'}
        if($script:Case -eq 'network'){throw 'CONNECTIVITY_FAILURE'}
        $sub=$script:Sub;$tenant=$script:Tenant
        if($script:Case -eq 'wrong-subscription'){$sub='wrong'}
        if($script:Case -eq 'wrong-tenant'){$tenant='wrong'}
        return (@{id=$sub;tenantId=$tenant;state='Enabled';user=@{type='user'}}|ConvertTo-Json -Compress)
    }
    if($a[0] -eq 'ad'){return (@{id=$script:User}|ConvertTo-Json -Compress)}
    if($a[0] -eq 'resource'){
        if(($script:Case -in @('orphan','empty-orphan') -or ($script:Case -eq 'partial-cleanup' -and $script:Applied))){
            return (@(@{id='/subscriptions/'+$script:Sub+'/resourceGroups/rg-wordle-academic/providers/Microsoft.Compute/disks/orphan';resourceGroup='rg-wordle-academic'})|ConvertTo-Json -Compress)
        }
        return '[]'
    }
    if($a[0] -eq 'group'){
        if($a[1] -eq 'show'){return '{"name":"rg-wordle-state"}'}
        if($script:Applied -and $script:Case -ne 'partial-cleanup'){return '[]'}
        if($script:Case -eq 'empty'){return '[]'}
        return '[{"name":"rg-wordle-academic"}]'
    }
    if($a[0] -eq 'aks'){return '[]'}
    if($a[0] -eq 'storage'){
        switch($a[1]){
            'account' {return '{"name":"stwordlesynthetic"}'}
            'container' {return '{"name":"tfstate"}'}
            'blob' {
                $status=if($script:Case -eq 'backend-lock'){'locked'}else{'unlocked'}
                return (@{metadata=@{};properties=@{etag='etag';lease=@{status=$status;state='available'}}}|ConvertTo-Json -Depth 8 -Compress)
            }
        }
    }
    throw 'UNMOCKED_AZURE_COMMAND'
}
$cases=@(
    @('tools-preflight','PREFLIGHT OK',$false),@('terraform-missing','ERROR',$false),
    @('wrong-version','ERROR',$false),@('az-missing','ERROR',$false),
    @('wrong-tenant','ERROR',$false),@('wrong-subscription','ERROR',$false),
    @('wrong-backend','ERROR',$false),@('state-inaccessible','ERROR',$false),
    @('empty','CLEAN',$true),@('expected-state','PREFLIGHT OK',$false),
    @('unexpected-state','ERROR',$true),@('backend-plan','ERROR',$true),
    @('backend-lock','ERROR',$true),@('mfa','ERROR',$false),@('network','ERROR',$false),
    @('wrong-confirmation','ERROR',$true),@('correct-confirmation','CLEAN',$true),
    @('destroy-failure','ERROR',$true),@('partial-cleanup','PARTIAL CLEANUP',$true),
    @('clean','CLEAN',$true),@('orphan','ERROR',$true),@('secret-logs','CLEAN',$true),
    @('unexpected-plan','ERROR',$true),@('unexpected-actions','ERROR',$true),
    @('tampered-plan','ERROR',$true),@('empty-orphan','PARTIAL CLEANUP',$true)
)
try{
    foreach($c in $cases){
        $script:Case=$c[0];$script:Calls=@();$script:Applied=$false
        $root=Join-Path $temp $script:Case;$script:Root=$root
        $null=New-Item -ItemType Directory -Path $root
        $dir=Join-Path $temp ($script:Case+'-work');$null=New-Item -ItemType Directory -Path (Join-Path $dir '.terraform') -Force
        $env:LOCALAPPDATA=Join-Path $root 'local'
        $backend=@{resource_group_name='rg-wordle-state';storage_account_name='stwordlesynthetic';container_name='tfstate';key='wordle/aks-demo.tfstate';tenant_id=$script:Tenant;subscription_id=$script:Sub;use_azuread_auth=$true}
        if($script:Case -eq 'wrong-backend'){$backend.key='wrong.tfstate'}
        [IO.File]::WriteAllText((Join-Path $dir '.terraform/terraform.tfstate'),(@{backend=@{type='azurerm';config=$backend}}|ConvertTo-Json -Depth 8))
        Copy-Item -LiteralPath (Join-Path $originalRoot 'infra/terraform/variables.tf') -Destination (Join-Path $dir 'variables.tf')
        [IO.File]::WriteAllText((Join-Path $dir '.terraform.lock.hcl'),'offline-lock')
        $target=Join-Path $temp ($script:Case+'-target.json')
        $cfg=@{subscription_id=$script:Sub;tenant_id=$script:Tenant;operator_object_id=$script:User;resource_group_name='rg-wordle-academic';node_resource_group_name='rg-wordle-academic-nodes';cluster_name='aks-wordle-academic';vnet_name='vnet-wordle-academic';subnet_name='snet-aks';identity_name='id-wordle-aks';backend_resource_group='rg-wordle-state';backend_account='stwordlesynthetic';backend_container='tfstate';backend_key='wordle/aks-demo.tfstate'}
        [IO.File]::WriteAllText($target,($cfg|ConvertTo-Json))
        # Work copy is external even to this fixture's fake source checkout.
        $input=Join-Path $temp ($script:Case+'-variables.json')
        $vars=@{subscription_id=$script:Sub;tenant_id=$script:Tenant;resource_group_name='rg-wordle-academic';node_resource_group_name='rg-wordle-academic-nodes';cluster_name='aks-wordle-academic'}
        [IO.File]::WriteAllText($input,($vars|ConvertTo-Json))
        $result='ERROR'
        try{$result=Start-Emergency ([bool]$c[2]) $input '' $target $dir}catch{
            # Fixture errors only: no native output or real credentials.
            $result='ERROR'
        }
        if($result -ne $c[1]){throw "FAIL $($c[0]): expected $($c[1]), observed $result"}
        $applies=@($script:Calls|Where-Object{$_ -like 'MOCK_TERRAFORM apply *'}).Count
        if($script:Case -notin @('correct-confirmation','destroy-failure','partial-cleanup','clean','secret-logs') -and $applies){throw "UNEXPECTED APPLY $script:Case"}
        if($script:Case -eq 'correct-confirmation' -and $applies -ne 1){throw 'Apply mock not exercised'}
        if(@($script:Calls|Where-Object{$_ -match ' force-unlock| init | destroy |az group delete'}).Count){throw 'Forbidden command emitted'}
        $logs=@(Get-ChildItem -LiteralPath $root -Filter audit.jsonl -Recurse)
        foreach($log in $logs){
            $raw=Get-Content -Raw -LiteralPath $log.FullName
            if($raw -match 'SYNTHETIC_SENSITIVE_SENTINEL|offline-plan|offline-lock|token|password|client_secret|terraform.tfstate|variables.json'){throw 'Sensitive log'}
        }
        if(@(Get-ChildItem -LiteralPath $root -Filter '*.tfplan' -Recurse).Count){throw 'Temporary plan retained'}
        $passed++;Write-Host "PASS $script:Case (OFFLINE)"
    }

    $prefix='/subscriptions/'+$script:Sub+'/resourceGroups/rg-wordle-academic'
    $paths=@('', '/providers/Microsoft.Network/virtualNetworks/vnet-wordle-academic', '/providers/Microsoft.Network/virtualNetworks/vnet-wordle-academic/subnets/snet-aks', '/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-wordle-aks', '/providers/Microsoft.Network/virtualNetworks/vnet-wordle-academic/subnets/snet-aks/providers/Microsoft.Authorization/roleAssignments/11111111-1111-4111-8111-111111111111', '/providers/Microsoft.ContainerService/managedClusters/aks-wordle-academic')
    $changes=@()
    for($j=0;$j -lt 6;$j++){
        $before=@{id=$prefix+$paths[$j]}
        if($j -eq 4){$before.scope=$prefix+$paths[2]}
        $changes+=@{address=$script:Addresses[$j];mode='managed';change=@{actions=@('delete');before=$before}}
    }
    $plan=@{resource_changes=$changes}|ConvertTo-Json -Depth 12|ConvertFrom-Json
    $inventory=@{resources=@();groups=@()}
    if(@(CheckPlan $plan $script:Addresses $inventory).Count -ne 6){throw 'Full deployment plan not accepted'}
    $passed++;Write-Host 'PASS complete-six-resource-plan (OFFLINE)'
    $subset=$script:Addresses[0..2];$plan=@{resource_changes=$changes[0..2]}|ConvertTo-Json -Depth 12|ConvertFrom-Json
    if(@(CheckPlan $plan $subset $inventory).Count -ne 3){throw 'Partial deployment plan not accepted'}
    $passed++;Write-Host 'PASS partial-three-resource-plan (OFFLINE)'

    Write-Host "$passed / 28 offline cases passed; zero native processes."
}finally{
    $script:Root=$originalRoot;$env:LOCALAPPDATA=$originalLocal
    # Only this test's verified temporary tree, never repository or cloud resources.
    $resolved=[IO.Path]::GetFullPath($temp)
    if($resolved.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -and
       [IO.Path]::GetFileName($resolved).StartsWith('wordle-emergency-tests-')){
        Remove-Item -LiteralPath $resolved -Recurse
    }else{throw 'Unsafe test cleanup path'}
}
