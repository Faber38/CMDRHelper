# Run with Windows PowerShell 5.1. No Python, winget, downloads or Pester needed.
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$originalLocation = Get-Location
. (Join-Path $repo 'install-windows.ps1')
$nativePythonCommand = ${function:Invoke-PythonCommand}
$nativeWingetInstall = ${function:Invoke-WingetInstall}
$nativeConfirmation = ${function:Confirm-PythonInstall}
$nativeCandidates = ${function:Get-PythonCandidates}
$sandbox = Join-Path $PSScriptRoot ('.installer-tests-' + [guid]::NewGuid().ToString('N'))
$script:fixture = Join-Path $sandbox 'CMDR Helper (Test) ä & !'
$script:basePython = Join-Path $sandbox 'Python 313\python.exe'
$script:venvDir = Join-Path $fixture 'venv'
$script:venvPython = Join-Path $venvDir 'Scripts\python.exe'
$script:marker = Join-Path $fixture 'backup\update_repair_required.json'
$script:passed = 0

function Assert {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERT: $Message" }
}

function Reset-Scenario {
    $script:state = @{
        BaseAvailable = $false; VenvHealthy = $false; Consent = $true
        WingetAvailable = $true; WingetExit = 0; DiscoverAfterInstall = $true
        FailCommand = ''; ProbeMismatch = $false; ProbeRejected = $false
        CandidateCalls = 0; Prompts = 0; WingetCalls = 0
        Calls = New-Object 'System.Collections.Generic.List[string]'
    }
    New-Item -ItemType Directory -Path (Split-Path $venvPython), (Split-Path $marker) -Force | Out-Null
    Set-Content -LiteralPath $venvPython -Value ''
    if (Test-Path -LiteralPath $marker) { Remove-Item -LiteralPath $marker }
}

# Every native boundary is replaced before an installation scenario can run.
function Invoke-PythonCommand {
    param([string]$Python, [string[]]$Arguments, [switch]$Quiet)
    $command = $Arguments -join ' '
    $state.Calls.Add("$Python | $command")
    $code = 0
    $output = @()
    if ($Arguments -contains '--probe') {
        if ($state.ProbeRejected -or ($Python -eq $venvPython -and -not $state.VenvHealthy)) {
            $code = 1
        } else {
            $prefix = Split-Path $basePython
            if ($Python -eq $venvPython) { $prefix = $venvDir }
            $executable = $Python
            if ($state.ProbeMismatch) { $executable = 'C:\foreign\python.exe' }
            $output = @(@{executable=$executable; prefix=$prefix; base_prefix=(Split-Path $basePython)} | ConvertTo-Json -Compress)
        }
    }
    if ($command -like '-I -m venv *') {
        Assert ($Python -eq $basePython) 'venv creation must use the discovered absolute base path'
        New-Item -ItemType Directory -Path (Split-Path $venvPython) -Force | Out-Null
        Set-Content -LiteralPath $venvPython -Value ''
        $state.VenvHealthy = $true
    }
    if ($state.FailCommand -and $command -match $state.FailCommand) { $code = 9 }
    return [pscustomobject]@{ExitCode=$code; Output=$output}
}
function Get-PythonCandidates {
    $state.CandidateCalls++
    if ($state.BaseAvailable) { return $basePython }
    return (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\python.exe')
}
function Confirm-PythonInstall { $state.Prompts++; return $state.Consent }
function Get-WingetPath { if ($state.WingetAvailable) { return 'MOCK-WINGET-ONLY' }; return $null }
function Invoke-WingetInstall {
    param([string]$Winget)
    Assert ($Winget -eq 'MOCK-WINGET-ONLY') 'real winget must never run'
    $state.WingetCalls++
    if ($state.WingetExit -eq 0 -and $state.DiscoverAfterInstall) { $state.BaseAvailable = $true }
    return $state.WingetExit
}

function Run-Installer {
    # Capture host messages too, so failure scenarios assert no success banner.
    $script:transcript = @(Invoke-CmdrHelperInstall $fixture 6>&1)
    $script:exitCode = $transcript[-1]
    $script:messages = $transcript -join "`n"
}
function Assert-Failure {
    Assert ($exitCode -ne 0) 'must return a nonzero exit code'
    Assert ($messages -notmatch 'CMDRHelper wurde erfolgreich eingerichtet\.') 'must not claim success'
}
function Test-Case {
    param([string]$Name, [scriptblock]$Body)
    Reset-Scenario
    & $Body
    $script:passed++
    Write-Host "PASS $Name"
}

try {
    New-Item -ItemType Directory -Path (Join-Path $fixture 'cmdrhelper'), (Split-Path $basePython) -Force | Out-Null
    Set-Content -LiteralPath $basePython -Value ''
    foreach ($name in @('main.py', 'requirements.txt', 'cmdrhelper\python_support.py')) {
        Copy-Item -LiteralPath (Join-Path $repo $name) -Destination (Join-Path $fixture $name)
    }
    foreach ($file in @('install-windows.ps1', 'tests\windows-installer.Tests.ps1')) {
        $tokens = $null; $parseErrors = $null
        $null = [Management.Automation.Language.Parser]::ParseFile((Join-Path $repo $file), [ref]$tokens, [ref]$parseErrors)
        Assert ($parseErrors.Count -eq 0) "PowerShell syntax: $file"
    }
    Test-Case 'Healthy venv skips base search, consent and winget' {
        $state.VenvHealthy = $true
        Run-Installer
        Assert ($exitCode -eq 0) $messages
        Assert ($state.CandidateCalls -eq 0 -and $state.Prompts -eq 0 -and $state.WingetCalls -eq 0) 'must reuse venv first'
        Assert (($state.Calls -join "`n") -match 'pip check') 'pip check is required'
        Assert (($state.Calls -join "`n") -match 'import PySide6; import PySide6.QtWidgets; import numpy; import PIL') 'all imports are required'
    }
    Test-Case 'Existing base interpreter rebuilds without consent' {
        $state.BaseAvailable = $true
        Run-Installer
        Assert ($exitCode -eq 0) $messages
        Assert ($state.Prompts -eq 0 -and $state.WingetCalls -eq 0) 'existing Python must not install Python'
    }
    Test-Case 'No Python: consent, winget, rediscovery and completion in one invocation' {
        Run-Installer
        Assert ($exitCode -eq 0) $messages
        Assert ($state.CandidateCalls -eq 2 -and $state.Prompts -eq 1 -and $state.WingetCalls -eq 1) 'must rediscover after winget'
        Assert (($state.Calls -join "`n") -notmatch '\\WindowsApps\\') 'must never execute a Store alias'
    }
    Test-Case 'Declining leaves the old venv untouched' {
        $state.Consent = $false
        Run-Installer
        Assert-Failure
        Assert ($exitCode -eq 10 -and $state.WingetCalls -eq 0) 'decline must not invoke winget'
        Assert (Test-Path -LiteralPath $venvPython) 'old venv must remain'
    }
    Test-Case 'Missing winget aborts' {
        $state.WingetAvailable = $false
        Run-Installer
        Assert-Failure
        Assert ($state.WingetCalls -eq 0 -and $messages -match 'winget ist nicht verfuegbar') 'explain missing winget'
    }
    Test-Case 'winget failure preserves venv and repair marker' {
        $state.WingetExit = -1978335189
        Set-Content -LiteralPath $marker -Value '{}'
        Run-Installer
        Assert-Failure
        Assert (Test-Path -LiteralPath $marker) 'repair marker must remain'
        Assert (Test-Path -LiteralPath $venvPython) 'old venv must remain'
        Assert ($state.CandidateCalls -eq 1) 'no continuation after winget failure'
    }
    Test-Case 'winget success without a valid discovered interpreter aborts' {
        $state.DiscoverAfterInstall = $false
        Run-Installer
        Assert-Failure
        Assert (Test-Path -LiteralPath $venvPython) 'old venv must remain'
    }
    foreach ($failure in @('-m venv ', 'pip install --upgrade', 'pip install -r', 'pip check', 'import PySide6')) {
        Test-Case "Failure at $failure preserves repair marker" {
            $state.BaseAvailable = $true
            $state.FailCommand = $failure
            Set-Content -LiteralPath $marker -Value '{}'
            Run-Installer
            Assert-Failure
            Assert (Test-Path -LiteralPath $marker) 'repair marker must remain until all checks pass'
        }
    }
    Test-Case 'Successful repair clears marker only after validation' {
        $state.BaseAvailable = $true
        $state.VenvHealthy = $true
        Set-Content -LiteralPath $marker -Value '{}'
        Run-Installer
        Assert ($exitCode -eq 0) $messages
        Assert ($state.CandidateCalls -eq 1) 'repair marker must force a rebuild'
        Assert (-not (Test-Path -LiteralPath $marker)) 'successful repair removes marker'
    }
    Test-Case 'Broken venv pip triggers rebuild' {
        $state.VenvHealthy = $true
        $state.BaseAvailable = $true
        $state.FailCommand = 'pip --version'
        Run-Installer
        Assert ($exitCode -eq 0 -and $state.CandidateCalls -eq 1) $messages
    }
    Test-Case 'Store alias and relative executable are rejected before execution' {
        $support = Join-Path $fixture 'cmdrhelper\python_support.py'
        Assert ($null -eq (Get-PythonProbe 'C:\Users\User\AppData\Local\Microsoft\WindowsApps\python.exe' $support -Base)) 'alias must be rejected'
        Assert ($null -eq (Get-PythonProbe 'python.exe' $support -Base)) 'relative path must be rejected'
        Assert ($state.Calls.Count -eq 0) 'must not execute rejected paths'
    }
    Test-Case 'Unsupported interpreter and mismatching executable are rejected' {
        $support = Join-Path $fixture 'cmdrhelper\python_support.py'
        $state.ProbeRejected = $true
        Assert ($null -eq (Get-PythonProbe $basePython $support -Base)) 'unsupported version/architecture must be rejected'
        $state.ProbeRejected = $false
        $state.ProbeMismatch = $true
        Assert ($null -eq (Get-PythonProbe $basePython $support -Base)) 'foreign executable must be rejected'
    }
    Test-Case 'Virtual environment cannot be used as base interpreter' {
        $state.VenvHealthy = $true
        Assert ($null -eq (Get-PythonProbe $venvPython (Join-Path $fixture 'cmdrhelper\python_support.py') -Base)) 'venv is not a base Python'
    }
    Test-Case 'Unsafe venv target is rejected' {
        $rejected = $false
        try { Assert-LocalVenv $fixture (Join-Path $fixture 'data') } catch { $rejected = $true }
        Assert $rejected 'must not accept a different deletion target'
    }
    Test-Case 'Missing requirements aborts before consent or mutation' {
        $requirements = Join-Path $fixture 'requirements.txt'
        Remove-Item -LiteralPath $requirements
        try {
            Run-Installer
            Assert-Failure
            Assert ($state.Prompts -eq 0 -and $state.Calls.Count -eq 0) 'preflight must run first'
        } finally { Copy-Item -LiteralPath (Join-Path $repo 'requirements.txt') -Destination $requirements }
    }
    Test-Case 'Real winget wrapper sends exact options to a harmless local stub' {
        $stub = Join-Path $sandbox 'winget-stub.cmd'
        Set-Content -LiteralPath $stub -Encoding ASCII -Value @('@echo off', '> "%~dp0winget-args.txt" echo %*', 'exit /b 23')
        $result = & $nativeWingetInstall $stub
        Assert ($result -eq 23) 'wrapper must propagate installer failure'
        $arguments = Get-Content -LiteralPath (Join-Path $sandbox 'winget-args.txt') -Raw
        foreach ($expected in @('--id Python.Python.3.14', '--architecture x64', '--scope user', '--source winget', 'InstallLauncherAllUsers=0')) {
            Assert ($arguments.Contains($expected)) "winget arguments: $expected"
        }
    }
    Test-Case 'Native Python command wrapper preserves nonzero exits in both modes' {
        foreach ($quiet in @($true, $false)) {
            $result = & $nativePythonCommand $env:ComSpec @('/d', '/c', 'exit 17') -Quiet:$quiet
            Assert ($result.ExitCode -eq 17) 'native failure must not become success'
        }
    }
    Test-Case 'Confirmation accepts only explicit yes' {
        foreach ($reply in @('', 'N', 'nein', 'perhaps', 'J', 'ja', 'YES')) {
            function Read-Host { return $reply }
            $result = @(& $nativeConfirmation 6>&1)
            Assert ($result[-1] -eq ($reply -in @('J', 'ja', 'YES'))) "consent handling: $reply"
            Assert (($result -join "`n").Contains('CMDRHelper benötigt Python 3.10 oder neuer (Windows: 64 Bit / x64).')) 'requested prompt must be readable'
        }
    }
    Test-Case 'Batch entry preserves exit code and handles special characters in its directory' {
        Copy-Item -LiteralPath (Join-Path $repo 'install.bat') -Destination (Join-Path $fixture 'install.bat')
        Set-Content -LiteralPath (Join-Path $fixture 'install-windows.ps1') -Encoding ASCII -Value 'exit 37'
        Set-Location -LiteralPath $fixture
        & $env:ComSpec /d /c 'install.bat < nul' | Out-Null
        Assert ($LASTEXITCODE -eq 37) 'batch must propagate the PowerShell exit code'
    }
    Write-Host "All $passed tests passed. No real Python or winget was executed."
} finally {
    Set-Location -LiteralPath $originalLocation.Path
    $resolvedSandbox = [IO.Path]::GetFullPath($sandbox)
    $allowedParent = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
    if (-not $resolvedSandbox.StartsWith($allowedParent, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Unsafe test cleanup path'
    }
    if (Test-Path -LiteralPath $resolvedSandbox) { Remove-Item -LiteralPath $resolvedSandbox -Recurse -Force }
}
