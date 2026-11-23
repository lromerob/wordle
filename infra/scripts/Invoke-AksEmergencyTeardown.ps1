[CmdletBinding()]
param([switch]$Preflight,[switch]$Teardown,[string]$VariablesFile,[string]$TerraformPath,[string]$TargetFile,[string]$WorkDirectory)
Set-StrictMode -Version 3.0
$ErrorActionPreference='Stop'
$script:Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
# Target and human operator are loaded ONLY from an explicit external private file.
$script:Sub=$null;$script:Tenant=$null;$script:User=$null;$script:Config=$null
function Set-EmergencyTarget([string]$File,[string]$Work) {
    if(-not $File -or -not $Work){throw 'EXTERNAL_TARGET_AND_WORKSPACE_REQUIRED'}
    foreach($p in @($File,$Work)){
        if(-not [IO.Path]::IsPathRooted($p)){throw 'ABSOLUTE_EXTERNAL_PATH_REQUIRED'}
        $full=[IO.Path]::GetFullPath($p)
        if($full -eq $script:Root -or $full.StartsWith(($script:Root+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){throw 'EXTERNAL_TARGET_AND_WORKSPACE_REQUIRED'}
        if(-not(Test-Path -LiteralPath $full) -or (Get-Item -LiteralPath $full).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'MISSING_OR_LINKED_PRIVATE_INPUT'}
    }
    $cfg=Get-Content -Raw -LiteralPath $File|ConvertFrom-Json
    $keys=@('subscription_id','tenant_id','operator_object_id','resource_group_name','node_resource_group_name','cluster_name','vnet_name','subnet_name','identity_name','backend_resource_group','backend_account','backend_container','backend_key')
    if((($cfg.PSObject.Properties.Name|Sort-Object) -join '|') -ne (($keys|Sort-Object) -join '|')){throw 'INVALID_TARGET_KEYS'}
    foreach($k in @('subscription_id','tenant_id','operator_object_id')){[void][guid]::Parse($cfg.$k)}
    foreach($k in @('resource_group_name','node_resource_group_name','cluster_name','vnet_name','identity_name','backend_resource_group')){
        if($cfg.$k -notmatch '^[a-zA-Z0-9_-]*wordle[a-zA-Z0-9_-]*$'){throw 'DEDICATED_WORDLE_TARGET_REQUIRED'}
    }
    foreach($k in @('subnet_name','backend_account','backend_container','backend_key')){
        if($cfg.$k -notmatch '^[a-zA-Z0-9_./-]+$'){throw 'INVALID_TARGET_NAME'}
    }
    if($cfg.backend_resource_group -in @($cfg.resource_group_name,$cfg.node_resource_group_name) -or
       $cfg.resource_group_name -eq $cfg.node_resource_group_name -or -not $cfg.backend_key.StartsWith('wordle/')){throw 'BACKEND_MUST_BE_INDEPENDENT'}
    $script:Config=$cfg;$script:Sub=$cfg.subscription_id;$script:Tenant=$cfg.tenant_id;$script:User=$cfg.operator_object_id
    $script:TargetPath=[IO.Path]::GetFullPath($File);$script:Dir=[IO.Path]::GetFullPath($Work)
}
$script:Addresses=@('azurerm_resource_group.wordle','azurerm_virtual_network.wordle','azurerm_subnet.aks','azurerm_user_assigned_identity.aks','azurerm_role_assignment.aks_network','azurerm_kubernetes_cluster.wordle')
function Field($o,$k,$default=$null) {
    if($null -eq $o){return $default};$p=$o.PSObject.Properties[$k]
    if($null -ne $p){return $p.Value};return $default
}
function Native([string]$Tool,[string[]]$Arguments) {
    # ONLY external-process boundary. Offline tests replace this function entirely.
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue';$lines=& $Tool @Arguments 2>&1;$code=$LASTEXITCODE
        $raw=($lines|ForEach-Object{"$_"}) -join [Environment]::NewLine
    } finally {$ErrorActionPreference=$old}
    if($code -ne 0){
        $category='TOOL_FAILED'
        if($raw -match 'AADSTS|MFA|interaction_required'){ $category='AUTHENTICATION_REQUIRED' }
        elseif($raw -match 'state lock|LeaseAlreadyPresent'){ $category='STATE_LOCKED' }
        throw "$category (exit $code). Salida sensible suprimida."
    };return $raw
}
function Resolve-WordleAzureCli {
    foreach($name in @('az','az.cmd')) {
        $application=Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_.Source) -and
                [IO.Path]::IsPathRooted($_.Source) -and
                (Test-Path -LiteralPath $_.Source -PathType Leaf) } |
            Select-Object -First 1
        if($application){return [string]$application.Source}
    }
    throw 'AZURE_CLI_MISSING'
}
function Tools($Explicit) {
    if(-not $Explicit){$Explicit=Join-Path $env:LOCALAPPDATA 'WordleTFG/tools/terraform-1.9.8/terraform.exe'}
    if(-not(Test-Path -LiteralPath $Explicit -PathType Leaf)){throw 'TERRAFORM_MISSING'}
    $azPath=Resolve-WordleAzureCli
    return @{tf=$Explicit;az=$azPath}
}
function Invoke-WordleAzureCli([string[]]$Arguments){return ((Native $script:Tools.az ($Arguments+@('--only-show-errors','-o','json')))|ConvertFrom-Json)}
function Tf([string[]]$Arguments){
    Push-Location -LiteralPath $script:Dir
    try{return Native $script:Tools.tf $Arguments}finally{Pop-Location}
}
function Context {
    $a=Invoke-WordleAzureCli @('account','show');$u=Invoke-WordleAzureCli @('ad','signed-in-user','show')
    if($a.id -ne $script:Sub -or $a.tenantId -ne $script:Tenant -or $a.state -ne 'Enabled' -or
       $a.user.type -ne 'user' -or $u.id -ne $script:User){throw 'CONTEXT_MISMATCH'}
}
function Backend {
    $m=Get-Content -Raw -LiteralPath (Join-Path $script:Dir '.terraform/terraform.tfstate')|ConvertFrom-Json
    $expected=@{resource_group_name=$script:Config.backend_resource_group;storage_account_name=$script:Config.backend_account;container_name=$script:Config.backend_container;key=$script:Config.backend_key;tenant_id=$script:Tenant;subscription_id=$script:Sub;use_azuread_auth=$true}
    if($m.backend.type -ne 'azurerm'){throw 'BACKEND_MISMATCH'}
    foreach($k in $expected.Keys){if((Field $m.backend.config $k) -ne $expected[$k]){throw 'BACKEND_MISMATCH'}}
    foreach($k in @('access_key','sas_token','client_secret','client_certificate_path','use_oidc','use_msi')){
        if(Field $m.backend.config $k){throw 'UNEXPECTED_BACKEND_AUTH'}
    }
    $rg=Invoke-WordleAzureCli @('group','show','--name',$script:Config.backend_resource_group,'--subscription',$script:Sub)
    $sa=Invoke-WordleAzureCli @('storage','account','show','--name',$script:Config.backend_account,'--resource-group',$script:Config.backend_resource_group,'--subscription',$script:Sub)
    $c=Invoke-WordleAzureCli @('storage','container','show','--account-name',$script:Config.backend_account,'--name',$script:Config.backend_container,'--auth-mode','login','--subscription',$script:Sub)
    $b=Invoke-WordleAzureCli @('storage','blob','show','--account-name',$script:Config.backend_account,'--container-name',$script:Config.backend_container,'--name',$script:Config.backend_key,'--auth-mode','login','--subscription',$script:Sub)
    if($rg.name -ne $script:Config.backend_resource_group -or $sa.name -ne $script:Config.backend_account -or $c.name -ne $script:Config.backend_container){throw 'BACKEND_MISMATCH'}
    if($b.properties.lease.status -ne 'unlocked' -or $b.properties.lease.state -ne 'available' -or (Field (Field $b 'metadata') 'terraformlockid')){throw 'STATE_LOCKED'}
    return [string]$b.properties.etag
}
function State {
    $items=@((Tf @('state','list')) -split '\r?\n'|Where-Object{$_.Trim()}|ForEach-Object{$_.Trim()})
    foreach($a in $items){if($a -notin $script:Addresses){throw 'UNEXPECTED_STATE_RESOURCE'}}
    return $items
}
function Inventory {
    $r=@(Invoke-WordleAzureCli @('resource','list','--subscription',$script:Sub))
    $g=@(Invoke-WordleAzureCli @('group','list','--subscription',$script:Sub))
    return @{resources=@($r|Where-Object{$_.resourceGroup -in @($script:Config.resource_group_name,$script:Config.node_resource_group_name)})
        groups=@($g|Where-Object{$_.name -in @($script:Config.resource_group_name,$script:Config.node_resource_group_name)})}
}
function InventoryHash($i){
    return (($i.resources|Sort-Object id|ForEach-Object{$_.id.ToLowerInvariant()}) -join '|')+
        ' GROUPS '+(($i.groups|Sort-Object name|ForEach-Object{$_.name+':'+(Field $_ 'managedBy' '')}) -join '|')
}
function Fingerprint {
    $f=@(Get-ChildItem -LiteralPath $script:Dir -File|Where-Object{$_.Name -match '\.tf$|\.tfvars(\.json)?$|\.terraform\.lock\.hcl$'})
    $f+=Get-Item -LiteralPath (Join-Path $script:Dir '.terraform/terraform.tfstate')
    $f+=Get-Item -LiteralPath $script:TargetPath
    if($script:Input){$f+=Get-Item -LiteralPath $script:Input}
    return (($f|Sort-Object FullName|ForEach-Object{$_.FullName+':'+(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}) -join '|')
}
function CheckPlan($p,[string[]]$State,$i) {
    if((Field $p 'errored' $false) -or @(Field $p 'deferred_changes' @()).Count){throw 'INCOMPLETE_PLAN'}
    $prefix=('/subscriptions/'+$script:Sub+('/resourceGroups/'+$script:Config.resource_group_name)).ToLowerInvariant()
    $suffix=@{
        'azurerm_resource_group.wordle'=''
        'azurerm_virtual_network.wordle'=('/providers/Microsoft.Network/virtualNetworks/'+$script:Config.vnet_name)
        'azurerm_subnet.aks'=('/providers/Microsoft.Network/virtualNetworks/'+$script:Config.vnet_name+'/subnets/'+$script:Config.subnet_name)
        'azurerm_user_assigned_identity.aks'=('/providers/Microsoft.ManagedIdentity/userAssignedIdentities/'+$script:Config.identity_name)
        'azurerm_kubernetes_cluster.wordle'=('/providers/Microsoft.ContainerService/managedClusters/'+$script:Config.cluster_name)
    }
    $seen=@();$ids=@()
    foreach($ch in @(Field $p 'resource_changes' @())){
        if((Field $ch 'mode' 'managed') -ne 'managed'){continue}
        if($ch.address -notin $script:Addresses){throw 'UNEXPECTED_PLAN_RESOURCE'}
        $actions=@($ch.change.actions) -join ','
        if($actions -notin @('delete','no-op')){throw 'UNEXPECTED_PLAN_ACTION'}
        if($actions -eq 'no-op'){continue}
        $id=([string](Field $ch.change.before 'id' '')).ToLowerInvariant()
        if(-not($id -eq $prefix -or $id.StartsWith($prefix+'/'))){throw 'UNSAFE_PLAN_SCOPE'}
        if($suffix.ContainsKey($ch.address)){
            if($id -ne ($prefix+$suffix[$ch.address]).ToLowerInvariant()){throw 'WRONG_RESOURCE_ID'}
        }else{
            $scope=([string](Field $ch.change.before 'scope' '')).ToLowerInvariant()
            $subnet=$prefix+'/providers/microsoft.network/virtualnetworks/'+$script:Config.vnet_name.ToLowerInvariant()+'/subnets/'+$script:Config.subnet_name.ToLowerInvariant()
            if($scope -ne $subnet -or $id -notmatch ('^'+[regex]::Escape($subnet)+'/providers/microsoft.authorization/roleassignments/[0-9a-f-]+$')){throw 'WRONG_ROLE_SCOPE'}
        }
        $seen+=$ch.address;$ids+=$id
    }
    if((($State|Sort-Object) -join '|') -ne (($seen|Sort-Object) -join '|')){throw 'STATE_PLAN_MISMATCH'}
    foreach($r in $i.resources){
        if($r.resourceGroup -eq $script:Config.resource_group_name -and $r.id.ToLowerInvariant() -notin $ids){throw 'ORPHAN_OR_FOREIGN_RESOURCE'}
    }
    $aks=$prefix+'/providers/microsoft.containerservice/managedclusters/'+$script:Config.cluster_name.ToLowerInvariant()
    foreach($g in $i.groups){
        if($g.name -eq $script:Config.node_resource_group_name -and
            ($aks -notin $ids -or ([string](Field $g 'managedBy' '')).ToLowerInvariant() -ne $aks)){throw 'UNOWNED_NODE_GROUP'}
    }
    return $ids
}
function Consent($Prompt){return Read-Host $Prompt}
function Audit($Event,$Result){
    # Fixed event/category only. Never include exceptions, stdout, inputs or state.
    $row=@{utc=[DateTime]::UtcNow.ToString('o');mode=$script:Mode;event=$Event;result=$Result}
    Add-Content -LiteralPath $script:Audit -Encoding UTF8 -Value ($row|ConvertTo-Json -Compress)
}
function Clean {
    $s=@(State);$i=Inventory;$null=Backend
    $clusters=@(Invoke-WordleAzureCli @('aks','list','--subscription',$script:Sub))
    if($s.Count -or $i.resources.Count -or $i.groups.Count -or
       @($clusters|Where-Object{$_.name -eq $script:Config.cluster_name -and $_.resourceGroup -eq $script:Config.resource_group_name}).Count){return 'PARTIAL CLEANUP'}
    # Every pre-delete ID is checked against the subscription inventory after apply.
    $all=@(Invoke-WordleAzureCli @('resource','list','--subscription',$script:Sub))
    foreach($id in $script:ObservedIds){if(@($all|Where-Object{$_.id -eq $id}).Count){return 'PARTIAL CLEANUP'}}
    return 'CLEAN'
}
function Start-Emergency([bool]$Destroy,[string]$InputFile,[string]$ExplicitTerraform,[string]$PrivateTarget,[string]$PrivateWork) {
    Set-EmergencyTarget $PrivateTarget $PrivateWork
    $script:Input=$null
    $script:ObservedIds=@();$script:Mode=if($Destroy){'TEARDOWN'}else{'PREFLIGHT'}
    $script:Tools=Tools $ExplicitTerraform
    if(Get-ChildItem Env:|Where-Object{$_.Name -match '^(TF_CLI_ARGS|TF_LOG|TF_DATA_DIR|TF_WORKSPACE|ARM_|TF_VAR_)'}){throw 'ENVIRONMENT_OVERRIDE'}
    if(@(Get-Process -Name terraform -ErrorAction SilentlyContinue).Count){throw 'CONCURRENT_TERRAFORM'}
    $folder=Join-Path $env:LOCALAPPDATA ('WordleTFG/emergency/'+[guid]::NewGuid().ToString('N'))
    $null=New-Item -ItemType Directory -Path $folder
    $script:Audit=Join-Path $folder 'audit.jsonl';$planFile=Join-Path $folder 'destroy.tfplan'
    try {
        Audit 'start' 'STARTED'
        $v=Tf @('version','-json')|ConvertFrom-Json
        if($v.terraform_version -ne '1.9.8' -or (Field $v.provider_selections 'registry.terraform.io/hashicorp/azurerm') -ne '4.50.0'){throw 'VERSION_MISMATCH'}
        Context;$null=Backend;$state=@(State);$i=Inventory
        $script:ObservedIds=@($i.resources|ForEach-Object{$_.id})
        Write-Host "WORDLE TFG - $script:Mode"
        Write-Host "Tenant: $script:Tenant; suscripcion: $script:Sub; backend aprobado OK."
        Write-Host "Recursos gestionados: $($state.Count)"
        $state|ForEach-Object{Write-Host "  $_"}
        $i.resources|ForEach-Object{Write-Host ("Azure: "+$_.id)}
        Audit 'preflight' 'VERIFIED'
        foreach($address in $state){Audit 'managed_resource' $address}
        if(-not $state.Count){$result=Clean;Audit 'finish' $result;Write-Host "$result. No se genera plan ni se destruye.";return $result}
        if(-not $Destroy){Write-Host 'PREFLIGHT OK. Aun se debe revisar plan e inventario.';return 'PREFLIGHT OK'}
        if(-not $InputFile){throw 'EXTERNAL_VARIABLES_REQUIRED'}
        $script:Input=[IO.Path]::GetFullPath($InputFile)
        if($script:Input.StartsWith(($script:Root+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)){throw 'EXTERNAL_VARIABLES_REQUIRED'}
        $vars=Get-Content -Raw -LiteralPath $script:Input|ConvertFrom-Json
        foreach($pair in @(@('subscription_id',$script:Sub),@('tenant_id',$script:Tenant),@('resource_group_name',$script:Config.resource_group_name),@('node_resource_group_name',$script:Config.node_resource_group_name),@('cluster_name',$script:Config.cluster_name))){
            if((Field $vars $pair[0]) -ne $pair[1]){throw 'VARIABLES_TARGET_MISMATCH'}
        }
        $declared=@([regex]::Matches((Get-Content -Raw -LiteralPath (Join-Path $script:Dir 'variables.tf')),'variable "([^"]+)"')|ForEach-Object{$_.Groups[1].Value})
        foreach($k in $vars.PSObject.Properties.Name){if($k -notin $declared){throw 'UNEXPECTED_VARIABLE'}}
        $fp=Fingerprint;$null=Tf @('validate','-no-color')
        if((Consent 'Para generar SOLO un plan y lease, escriba PLAN WORDLE AKS') -cne 'PLAN WORDLE AKS'){throw 'PLAN_NOT_AUTHORIZED'}
        $null=Tf @('plan','-destroy','-input=false','-no-color','-lock-timeout=60s',('-var-file='+$script:Input),('-out='+$planFile))
        $plan=Tf @('show','-json',$planFile)|ConvertFrom-Json
        $i=Inventory;$ids=@(CheckPlan $plan $state $i)
        $script:ObservedIds=@($script:ObservedIds+@($i.resources|ForEach-Object{$_.id})+$ids|Sort-Object -Unique)
        $hash=(Get-FileHash -LiteralPath $planFile -Algorithm SHA256).Hash
        $etag=Backend;$inventoryHash=InventoryHash $i;$start=[DateTime]::UtcNow
        Write-Host "ATENCION: DESTRUCCION IRREVERSIBLE de $($ids.Count) recursos Terraform."
        Write-Host "Tenant $script:Tenant / suscripcion $script:Sub. Backend EXCLUIDO."
        $ids|ForEach-Object{Write-Host "ELIMINAR: $_"}
        $i.resources|ForEach-Object{Write-Host ("REVISAR cascada/dependencia: "+$_.id)}
        Write-Host "Plan SHA256 $hash. Si ve un recurso ajeno, cancele."
        Audit 'plan' 'REVIEWABLE'
        Audit 'plan_sha256' $hash
        if((Consent 'Autorizacion del propietario: escriba DESTRUIR WORDLE AKS') -cne 'DESTRUIR WORDLE AKS'){throw 'CONFIRMATION_REJECTED'}
        if(([DateTime]::UtcNow-$start).TotalMinutes -gt 10){throw 'APPROVAL_EXPIRED'}
        Context
        if((Get-FileHash -LiteralPath $planFile -Algorithm SHA256).Hash -ne $hash -or (Fingerprint) -ne $fp){throw 'PLAN_OR_CONFIG_CHANGED'}
        if((Backend) -ne $etag -or (InventoryHash (Inventory)) -ne $inventoryHash -or
           ((@(State)|Sort-Object) -join '|') -ne (($state|Sort-Object) -join '|')){throw 'STATE_OR_INVENTORY_CHANGED'}
        if(@(Get-Process -Name terraform -ErrorAction SilentlyContinue).Count){throw 'CONCURRENT_TERRAFORM'}
        Audit 'confirmation' 'EXPLICIT_ACCEPTED'
        $null=Tf @('apply','-input=false','-lock-timeout=60s',$planFile)
        Audit 'terraform' 'FINISHED';$result=Clean;Audit 'finish' $result
        Write-Host "$result. Revisar facturacion diferida; backend conserva sus costes.";return $result
    }catch{
        Audit 'failure' 'VERIFICATION FAILED'
        Write-Warning 'VERIFICATION FAILED: detenerse. Consultar manual para MFA, estado, conectividad o recursos parciales.'
        throw
    }finally{
        if(Test-Path -LiteralPath $planFile){Remove-Item -LiteralPath $planFile}
        Write-Host "Log sanitizado: $script:Audit"
    }
}
if($MyInvocation.InvocationName -ne '.'){
    try{
        if($Preflight -and $Teardown){throw 'Elija solo un modo'}
        $result=Start-Emergency ([bool]$Teardown) $VariablesFile $TerraformPath $TargetFile $WorkDirectory
        if($result -in @('PARTIAL CLEANUP','VERIFICATION FAILED')){exit 2};exit 0
    }catch{
        Write-Error 'Operacion detenida. No repetir a ciegas. Consulte el manual; no se muestran errores crudos.'
        exit 1
    }
}
