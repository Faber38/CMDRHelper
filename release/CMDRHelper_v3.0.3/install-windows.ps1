# Windows PowerShell 5.1; dot-sourcing only defines functions for automated tests.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-PythonCommand {
    param([string]$Python, [string[]]$Arguments, [switch]$Quiet)
    # Windows PowerShell can turn native stderr into terminating errors.
    $ErrorActionPreference = 'Continue'
    $global:LASTEXITCODE = 1
    try {
        if ($Quiet) {
            $output = @(& $Python @Arguments 2>$null)
        } else {
            & $Python @Arguments 2>&1 | Out-Host
            $output = @()
        }
        $code = $LASTEXITCODE
        return [pscustomobject]@{ ExitCode = $code; Output = $output }
    } catch {
        return [pscustomobject]@{ ExitCode = 1; Output = @() }
    }
}

function Test-WindowsAppsAlias {
    param([string]$Path)
    return $Path -match '(?i)\\Microsoft\\WindowsApps\\'
}

function Get-PythonProbe {
    param([string]$Python, [string]$SupportFile, [switch]$Base, [string]$VenvDir)
    if (-not [IO.Path]::IsPathRooted($Python) -or (Test-WindowsAppsAlias $Python) -or
        -not (Test-Path -LiteralPath $Python -PathType Leaf)) { return $null }
    $result = Invoke-PythonCommand $Python @('-I', '-B', $SupportFile, '--probe') -Quiet
    if ($result.ExitCode -ne 0) { return $null }
    try {
        $probe = ($result.Output -join "`n") | ConvertFrom-Json
        $actual = [IO.Path]::GetFullPath([string]$probe.executable)
        if ($actual -ine [IO.Path]::GetFullPath($Python)) { return $null }
        if ($Base -and $probe.prefix -ine $probe.base_prefix) { return $null }
        if ($Base -and (Invoke-PythonCommand $actual @('-I', '-c', 'import venv; import ensurepip') -Quiet).ExitCode -ne 0) {
            return $null
        }
        if ($VenvDir -and ($probe.prefix -ieq $probe.base_prefix -or
            [IO.Path]::GetFullPath([string]$probe.prefix) -ine $VenvDir)) { return $null }
        return $actual
    } catch { return $null }
}

function Get-PythonCandidates {
    # PEP 514 registrations are visible immediately after installation, even
    # when the parent cmd.exe still has its original PATH.
    foreach ($registryRoot in @('HKCU:\Software\Python', 'HKLM:\Software\Python',
                                'HKLM:\Software\WOW6432Node\Python')) {
        foreach ($company in @(Get-ChildItem -LiteralPath $registryRoot -ErrorAction SilentlyContinue)) {
            foreach ($tag in @(Get-ChildItem -LiteralPath $company.PSPath -ErrorAction SilentlyContinue)) {
                $key = Get-Item -LiteralPath (Join-Path $tag.PSPath 'InstallPath') -ErrorAction SilentlyContinue
                if ($null -ne $key) {
                    $executable = $key.GetValue('ExecutablePath')
                    if ($executable) { [string]$executable }
                    $directory = $key.GetValue('')
                    if ($directory) { Join-Path $directory 'python.exe' }
                }
            }
        }
    }
    foreach ($root in @((Join-Path $env:LOCALAPPDATA 'Programs\Python'), $env:ProgramFiles)) {
        foreach ($directory in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
            if ($directory.Name -match '^Python3\d+(?:-amd64)?$') {
                Join-Path $directory.FullName 'python.exe'
            }
        }
    }
    # Enumerate a real legacy launcher's paths, never request an installation.
    foreach ($launcher in @(Get-Command py.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        if (Test-WindowsAppsAlias $launcher.Source) { continue }
        $listing = Invoke-PythonCommand $launcher.Source @('-0p') -Quiet
        if ($listing.ExitCode -eq 0) {
            foreach ($line in $listing.Output) {
                if ([string]$line -match '([A-Za-z]:\\.*\\python.exe)\s*$') { $Matches[1].Trim() }
            }
        }
    }
    foreach ($name in @('python.exe', 'python3.exe')) {
        foreach ($command in @(Get-Command $name -CommandType Application -All -ErrorAction SilentlyContinue)) {
            $command.Source
        }
    }
}

function Find-BasePython {
    param([string]$SupportFile)
    foreach ($candidate in @(Get-PythonCandidates | Select-Object -Unique)) {
        $python = Get-PythonProbe -Python $candidate -SupportFile $SupportFile -Base
        if ($python) { return $python }
    }
    return $null
}

function Confirm-PythonInstall {
    Write-Host ''
    Write-Host 'CMDRHelper benötigt Python 3.10 oder neuer (Windows: 64 Bit / x64).'
    Write-Host ''
    Write-Host 'Kein geeigneter Python-x64-Basisinterpreter ab Version 3.10 wurde gefunden.'
    Write-Host 'Automatisch installiert wird die festgelegte Version Python 3.14 x64.'
    Write-Host ''
    Write-Host 'Installation mit winget fuer dieses Windows-Benutzerkonto.'
    Write-Host 'Mit Ja stimmen Sie den Python- und winget-Quellenbedingungen zu.'
    Write-Host 'Anschliessend wird CMDRHelper automatisch weiter eingerichtet.'
    $answer = Read-Host 'Soll Python jetzt automatisch installiert werden? [J/N]'
    return $answer.Trim() -match '^(?i:j|ja|y|yes)$'
}

function Get-WingetPath {
    $command = Get-Command winget.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}

function Invoke-WingetInstall {
    param([string]$Winget)
    $ErrorActionPreference = 'Continue'
    $global:LASTEXITCODE = 1
    & $Winget install --id Python.Python.3.14 --exact --source winget --architecture x64 --scope user --silent --accept-source-agreements --accept-package-agreements --disable-interactivity --custom 'InstallLauncherAllUsers=0' 2>&1 | Out-Host
    return $LASTEXITCODE
}

function Assert-LocalVenv {
    param([string]$InstallRoot, [string]$VenvDir)
    if ([IO.Path]::GetFullPath($VenvDir) -ine (Join-Path $InstallRoot 'venv')) {
        throw 'Unsicheres venv-Ziel. Reparatur abgebrochen.'
    }
    # Fail closed on links, including nested junctions, before using/deleting it.
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($VenvDir)
    while ($pending.Count -gt 0) {
        $path = $pending.Pop()
        $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
        if ($null -eq $item) {
            if ($path -eq $VenvDir -and -not (Test-Path -LiteralPath $path)) { return }
            throw "Das lokale venv konnte nicht sicher geprueft werden: $path"
        }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Das lokale venv enthaelt einen Link/Reparse-Point: $path"
        }
        if ($item.PSIsContainer) {
            foreach ($child in @(Get-ChildItem -LiteralPath $path -Force)) {
                if ($child.PSIsContainer -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                    $pending.Push($child.FullName)
                }
            }
        } elseif ($path -eq $VenvDir) { throw 'Das lokale venv ist kein Verzeichnis.' }
    }
}

function Invoke-CmdrHelperInstall {
    param([string]$InstallRoot)
    try {
        $InstallRoot = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
        Set-Location -LiteralPath $InstallRoot
        $venv = Join-Path $InstallRoot 'venv'
        $venvPython = Join-Path $venv 'Scripts\python.exe'
        $support = Join-Path $InstallRoot 'cmdrhelper\python_support.py'
        $requirements = Join-Path $InstallRoot 'requirements.txt'
        $marker = Join-Path $InstallRoot 'backup\update_repair_required.json'
        Write-Host '=========================================='
        Write-Host '       CMDRHelper - Installation'
        Write-Host '=========================================='
        Write-Host "Installationsordner: $InstallRoot"
        foreach ($required in @($support, $requirements, (Join-Path $InstallRoot 'main.py'))) {
            if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
                throw "Installationsdatei fehlt: $required. Bitte das vollstaendige ZIP entpacken."
            }
        }
        Write-Host '[1/6] Lokale virtuelle Umgebung wird geprueft...'
        Assert-LocalVenv $InstallRoot $venv
        $healthy = $false
        if (-not (Test-Path -LiteralPath $marker)) {
            if (Get-PythonProbe $venvPython $support -VenvDir $venv) {
                $healthy = (Invoke-PythonCommand $venvPython @('-I', '-m', 'pip', '--version') -Quiet).ExitCode -eq 0
            }
        }
        if ($healthy) {
            Write-Host 'Das lokale venv ist gesund und wird weiterverwendet.'
        } else {
            Write-Host '[2/6] Unterstuetzter Python-x64-Basisinterpreter wird gesucht...'
            $python = Find-BasePython $support
            if (-not $python) {
                if (-not (Confirm-PythonInstall)) {
                    Write-Host 'Installation abgebrochen: Die Python-Installation wurde nicht bestaetigt.'
                    return 10
                }
                $winget = Get-WingetPath
                if (-not $winget) {
                    throw 'winget ist nicht verfuegbar. Dieser Installationsschritt benoetigt den Windows App Installer mit winget.'
                }
                Write-Host 'Python 3.14 x64 wird mit winget installiert. Bitte warten...'
                $wingetExit = Invoke-WingetInstall $winget
                if ($wingetExit -ne 0) {
                    throw "winget konnte Python nicht erfolgreich installieren (Exitcode $wingetExit). Beachten Sie die winget-Meldung oben."
                }
                $python = Find-BasePython $support
                if (-not $python) {
                    throw 'winget wurde beendet, aber ein startbarer unterstuetzter Python-x64-Basisinterpreter wurde danach nicht gefunden.'
                }
            }
            Write-Host "Basisinterpreter: $python"
            Write-Host 'Das lokale venv wird neu erstellt. Persoenliche Daten bleiben erhalten.'
            # Only remove an old venv after a usable base interpreter is available.
            Assert-LocalVenv $InstallRoot $venv
            if (Test-Path -LiteralPath $venv) { Remove-Item -LiteralPath $venv -Recurse -Force }
            if ((Invoke-PythonCommand $python @('-I', '-m', 'venv', $venv)).ExitCode -ne 0) {
                throw 'Das lokale venv konnte nicht erstellt werden.'
            }
        }
        Write-Host '[3/6] Lokaler venv-Interpreter wird geprueft...'
        if (-not (Get-PythonProbe $venvPython $support -VenvDir $venv)) {
            throw 'Das lokale venv ist nicht mit unterstuetztem Python x64 startbar.'
        }
        Write-Host "Verwendeter Interpreter: $venvPython"
        Write-Host '[4/6] pip wird im lokalen venv aktualisiert...'
        if ((Invoke-PythonCommand $venvPython @('-I', '-m', 'pip', 'install', '--upgrade', 'pip')).ExitCode -ne 0) {
            throw 'pip konnte im lokalen venv nicht aktualisiert werden.'
        }
        Write-Host '[5/6] Abhaengigkeiten werden im lokalen venv installiert...'
        if ((Invoke-PythonCommand $venvPython @('-I', '-m', 'pip', 'install', '-r', $requirements)).ExitCode -ne 0) {
            throw 'Nicht alle Abhaengigkeiten konnten installiert werden.'
        }
        Write-Host '[6/6] Paketkonsistenz und Imports werden geprueft...'
        if ((Invoke-PythonCommand $venvPython @('-I', '-m', 'pip', 'check')).ExitCode -ne 0) {
            throw 'pip check hat unvereinbare oder fehlende Abhaengigkeiten gefunden.'
        }
        if ((Invoke-PythonCommand $venvPython @('-I', '-c', 'import PySide6; import PySide6.QtWidgets; import numpy; import PIL')).ExitCode -ne 0) {
            throw 'Die Importpruefung fuer PySide6, QtWidgets, numpy oder PIL ist fehlgeschlagen.'
        }
        if (Test-Path -LiteralPath $marker) { Remove-Item -LiteralPath $marker -Force }
        Write-Host ''
        Write-Host 'CMDRHelper wurde erfolgreich eingerichtet.'
        Write-Host ('Start: "' + (Join-Path $InstallRoot 'start.bat') + '"')
        return 0
    } catch {
        Write-Host "[FEHLER] $($_.Exception.Message)"
        Write-Host 'CMDRHelper wurde nicht erfolgreich eingerichtet. install.bat kann erneut gestartet werden.'
        return 1
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    exit (Invoke-CmdrHelperInstall -InstallRoot $PSScriptRoot)
}
