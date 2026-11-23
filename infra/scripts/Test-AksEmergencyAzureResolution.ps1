# Completely offline: only a temporary inert az.cmd may be executed.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Invoke-AksEmergencyTeardown.ps1')
$script:OriginalNative=(Get-Command Native).ScriptBlock
$oldPath=$env:PATH
$oldPathext=$env:PATHEXT
$temp=Join-Path ([IO.Path]::GetTempPath()) ('wordle-az-resolution-'+[guid]::NewGuid().ToString('N'))
$bin=Join-Path $temp 'fake cli with spaces'
$null=New-Item -ItemType Directory -Path $bin
$script:FakeCli=Join-Path $bin 'az.cmd'
$script:Calls=0;$script:ShadowCalls=0;$passed=0
function Native([string]$Tool,[string[]]$Arguments) {
    # Guard the original implementation: no fallback to a real CLI or Terraform.
    if([IO.Path]::GetFullPath($Tool) -ne $script:FakeCli){throw 'REAL_PROCESS_BLOCKED'}
    $script:Calls++
    return & $script:OriginalNative $Tool $Arguments
}
function Write-FakeCli([int]$Code,[string]$Text,[bool]$Stderr=$false) {
    $line='echo '+$Text
    if($Stderr){$line+=' 1>&2'}
    [IO.File]::WriteAllText($script:FakeCli,("@echo off"+[Environment]::NewLine+$line+[Environment]::NewLine+"exit /b $Code"+[Environment]::NewLine),[Text.Encoding]::ASCII)
}
function Assert-True($Condition,$Message){if(-not $Condition){throw $Message}}
function Passed($Name){$script:passed++;Write-Host "PASS $Name (OFFLINE)"}
try {
    # Only our own directory on PATH. cmd files are inert and the guard rejects all other paths.
    $env:PATH=$bin;$env:PATHEXT='.COM;.EXE;.BAT;.CMD'
    Write-FakeCli 0 '{"fixture":true}'
    function Az { $script:ShadowCalls++;throw 'SHADOW_FUNCTION_CALLED' }
    $old=Get-Command az
    Assert-True ($old.CommandType -eq 'Function' -and [string]::IsNullOrEmpty($old.Source)) 'Original incident not reproduced'
    $resolved=Resolve-WordleAzureCli
    Assert-True ($resolved -eq $script:FakeCli) 'Function selected instead of application'
    $script:Tools=@{az=$resolved;tf='FORBIDDEN_TERRAFORM'}
    $reply=Invoke-WordleAzureCli @('account','show')
    Assert-True ($reply.fixture -and $script:Calls -eq 1 -and $script:ShadowCalls -eq 0) 'Application invocation/recursion regression'
    Passed 'original-unfiltered-lookup-fails-filtered-lookup-and-invocation-succeed'
    Remove-Item Function:Az

    function ShadowAliasTarget { $script:ShadowCalls++;throw 'SHADOW_ALIAS_CALLED' }
    Set-Alias -Name az -Value ShadowAliasTarget -Scope Script
    Assert-True ((Get-Command az).CommandType -eq 'Alias') 'Alias fixture missing'
    $script:Tools.az=Resolve-WordleAzureCli
    $reply=Invoke-WordleAzureCli @('account','show')
    Assert-True ($reply.fixture -and $script:ShadowCalls -eq 0) 'Alias intercepted native invocation'
    Passed 'alias-shadow-does-not-intercept-application'
    Remove-Item Alias:az

    $application=Get-Command -Name az.cmd -CommandType Application
    Assert-True ($application.Source -eq $resolved -and $resolved.Contains(' ') -and $resolved.EndsWith('az.cmd')) 'Windows cmd/spaces fixture not exercised'
    Passed 'valid-windows-az-cmd-path-with-spaces'

    $env:PATH=Join-Path $temp 'no-cli'
    $caught=$false
    try{$null=Resolve-WordleAzureCli}catch{$caught=$_.Exception.Message -eq 'AZURE_CLI_MISSING'}
    Assert-True $caught 'Missing application was accepted'
    Passed 'application-missing-fails-closed'
    $env:PATH=$bin

    # A malformed CommandInfo must not become a successful path.
    function Get-Command { param($Name,$CommandType,$ErrorAction) [pscustomobject]@{Source='';CommandType='Application'} }
    $caught=$false
    try{$null=Resolve-WordleAzureCli}catch{$caught=$_.Exception.Message -eq 'AZURE_CLI_MISSING'}
    Assert-True $caught 'Empty Source accepted'
    Passed 'empty-source-rejected'
    Remove-Item Function:Get-Command

    function Get-Command { param($Name,$CommandType,$ErrorAction) [pscustomobject]@{Source='az.cmd';CommandType='Application'} }
    $caught=$false
    try{$null=Resolve-WordleAzureCli}catch{$caught=$_.Exception.Message -eq 'AZURE_CLI_MISSING'}
    Assert-True $caught 'Relative Source accepted'
    Passed 'relative-source-rejected'
    Remove-Item Function:Get-Command

    Write-FakeCli 7 'SYNTHETIC_SECRET_SENTINEL' $true
    $caught=$false
    try{$null=Invoke-WordleAzureCli @('account','show')}catch{
        $caught=$_.Exception.Message -match 'TOOL_FAILED \(exit 7\)' -and $_.Exception.Message -notmatch 'SYNTHETIC_SECRET_SENTINEL'
    }
    Assert-True $caught 'Native exit/stderr was hidden as success or leaked'
    Passed 'nonzero-exit-stderr-sanitized-no-success'

    Write-FakeCli 9 'AADSTS50076 SYNTHETIC_SECRET_SENTINEL' $true
    $caught=$false
    try{$null=Invoke-WordleAzureCli @('account','show')}catch{
        $caught=$_.Exception.Message -match 'AUTHENTICATION_REQUIRED \(exit 9\)' -and $_.Exception.Message -notmatch 'SYNTHETIC_SECRET_SENTINEL'
    }
    Assert-True $caught 'Authentication error propagation regression'
    Passed 'authentication-error-is-fail-closed-and-sanitized'

    Write-FakeCli 0 'invalid-json'
    $caught=$false
    try{$null=Invoke-WordleAzureCli @('account','show')}catch{$caught=$true}
    Assert-True $caught 'Malformed JSON accepted'
    Passed 'malformed-json-does-not-become-success'

    $source=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'Invoke-AksEmergencyTeardown.ps1')
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
    Assert-True ($errors.Count -eq 0) 'Syntax errors'
    $functions=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
    Assert-True (@($functions|Group-Object Name|Where-Object Count -gt 1).Count -eq 0) 'Duplicate functions'
    Assert-True (-not($functions.Name -contains 'Az')) 'Old wrapper remains'
    $commands=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst]},$true))
    Assert-True (@($commands|Where-Object { $_.GetCommandName() -ieq 'az' }).Count -eq 0) 'Ambiguous direct invocation remains'
    $wrapper=@($functions|Where-Object Name -eq 'Invoke-WordleAzureCli')[0]
    Assert-True ($wrapper.Body.Extent.Text -notmatch 'Invoke-WordleAzureCli') 'Recursive wrapper'
    Assert-True ($source.IndexOf('if(-not $Destroy)') -lt $source.IndexOf("Consent 'Para generar SOLO")) 'Preflight safety branch changed'
    Assert-True ($source.Contains("-cne 'DESTRUIR WORDLE AKS'") -and $source.Contains("-cne 'PLAN WORDLE AKS'")) 'Required consent removed'
    Passed 'static-no-old-wrapper-duplicates-recursion-or-ambiguous-az-safety-branches-preserved'
    $work=Join-Path $temp 'private-work';$null=New-Item -ItemType Directory -Path $work
    $target=Join-Path $temp 'target.json'
    $cfg=@{subscription_id='11111111-1111-4111-8111-111111111111';tenant_id='22222222-2222-4222-8222-222222222222';operator_object_id='33333333-3333-4333-8333-333333333333';resource_group_name='rg-wordle-isolated';node_resource_group_name='rg-wordle-isolated-nodes';cluster_name='aks-wordle-isolated';vnet_name='vnet-wordle-isolated';subnet_name='subnet-test';identity_name='id-wordle-isolated';backend_resource_group='rg-wordle-independent';backend_account='wordlesynthetic';backend_container='tfstate';backend_key='wordle/test.tfstate'}
    [IO.File]::WriteAllText($target,($cfg|ConvertTo-Json))
    Set-EmergencyTarget $target $work
    Assert-True ($script:Sub -eq $cfg.subscription_id -and $script:User -eq $cfg.operator_object_id -and $script:Dir -eq $work) 'Private target not applied'
    Passed 'external-private-target-and-human-operator'
    $caught=$false;try{Set-EmergencyTarget '' $work}catch{$caught=$true};Assert-True $caught 'Missing target accepted';Passed 'missing-target-rejected'
    $caught=$false;try{Set-EmergencyTarget $target $script:Root}catch{$caught=$true};Assert-True $caught 'Checkout workspace accepted';Passed 'checkout-workspace-rejected'
    $cfg.backend_resource_group=$cfg.resource_group_name
    [IO.File]::WriteAllText($target,($cfg|ConvertTo-Json))
    $caught=$false;try{Set-EmergencyTarget $target $work}catch{$caught=$true};Assert-True $caught 'Disposable backend accepted';Passed 'backend-inside-disposable-scope-rejected'
    Write-Host "$passed / 14 additional offline regressions passed; only inert fake az.cmd processes."
} finally {
    $env:PATH=$oldPath;$env:PATHEXT=$oldPathext
    $resolvedTemp=[IO.Path]::GetFullPath($temp)
    if($resolvedTemp.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -and
       [IO.Path]::GetFileName($resolvedTemp).StartsWith('wordle-az-resolution-')){
        Remove-Item -LiteralPath $resolvedTemp -Recurse
    }else{throw 'Unsafe test cleanup path'}
}
