param()
$ErrorActionPreference = 'Stop'
$work = Join-Path $env:TEMP 'HermesFiveChoicesInstaller'
$log = Join-Path $env:TEMP 'HermesFiveChoicesInstaller.log'
try {
    $installed = if ($env:H5_INSTALL_TARGET) { $env:H5_INSTALL_TARGET } else { Join-Path $env:LOCALAPPDATA 'HermesFiveChoices' }
    $runtimeRoot = if ($env:H5_RUNTIME_ROOT) { $env:H5_RUNTIME_ROOT } else { Join-Path $env:LOCALAPPDATA 'HermesFiveChoicesRuntime' }
    $hermesHome = if ($env:H5_HERMES_HOME) { $env:H5_HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'HermesFiveChoicesData\hermes' }
    $existingPython = Join-Path $runtimeRoot 'hermes-agent\venv\Scripts\python.exe'
    $existingStopper = Join-Path $installed 'installer\start_services.py'
    if ((Test-Path $existingPython) -and (Test-Path $existingStopper)) {
        & $existingPython $existingStopper --app-root $installed --runtime-root $runtimeRoot --hermes-home $hermesHome --stop
        if ($LASTEXITCODE -ne 0) { throw 'Existing Five Choices services could not be stopped safely.' }
    }
    if (Test-Path $work) { Remove-Item -LiteralPath $work -Recurse -Force }
    New-Item -ItemType Directory -Path $work | Out-Null
    Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'payload.zip') -DestinationPath $work -Force
    $source = Join-Path $work 'hermes-five-choices-dashboard-0.1.0'
    if ($env:H5_PYTHON) {
        $python = $env:H5_PYTHON
    } else {
        $runtimeBundle = Join-Path $source 'runtime\hermes-five-choices-runtime-0.20.6-win64.zip'
        $bootstrapRuntime = Join-Path $work 'bootstrap-runtime'
        if (-not (Test-Path $runtimeBundle)) { throw 'The embedded frozen runtime is missing.' }
        Expand-Archive -LiteralPath $runtimeBundle -DestinationPath $bootstrapRuntime -Force
        $python = Join-Path $bootstrapRuntime 'runtime\python\python.exe'
    }
    if (-not (Test-Path $python)) { throw "The embedded bootstrap Python is missing at $python." }
    $bootstrapper = Join-Path $source 'installer\bootstrapper.py'
    $arguments = @($bootstrapper, 'install', '--source', $source)
    if ($env:H5_INSTALL_TARGET) { $arguments += @('--target', $env:H5_INSTALL_TARGET) }
    if ($env:H5_RUNTIME_ROOT) { $arguments += @('--runtime-root', $env:H5_RUNTIME_ROOT) }
    if ($env:H5_HERMES_HOME) { $arguments += @('--hermes-home', $env:H5_HERMES_HOME) }
    if ($env:H5_SKIP_PROFILES -eq '1') { $arguments += '--skip-profiles' }
    if ($env:H5_SKIP_RUNTIME -eq '1') { $arguments += '--skip-runtime' }
    & $python @arguments *>&1 | Tee-Object -FilePath $log
    if ($LASTEXITCODE -ne 0) { throw "Five Choices bootstrapper failed with exit code $LASTEXITCODE. See $log" }
    $launcher = Join-Path $installed 'start_five_choices.bat'
    if (-not (Test-Path $launcher)) { throw 'Installation completed without the expected launcher.' }
    $productDataRoot = Split-Path -Parent $hermesHome
    New-Item -ItemType Directory -Path $productDataRoot -Force | Out-Null
    $uninstaller = Join-Path $productDataRoot 'uninstall_five_choices.bat'
    Copy-Item -LiteralPath (Join-Path $installed 'installer\uninstall_five_choices.bat') -Destination $uninstaller -Force
    if ($env:H5_SKIP_SHORTCUTS -ne '1') {
        $shell = New-Object -ComObject WScript.Shell
        $desktop = [Environment]::GetFolderPath('Desktop')
        $desktopShortcut = $shell.CreateShortcut((Join-Path $desktop 'Hermes Five Choices.lnk'))
        $desktopShortcut.TargetPath = $launcher
        $desktopShortcut.WorkingDirectory = $installed
        $desktopShortcut.Description = 'Open Hermes Five Choices'
        $desktopShortcut.Save()
        $startMenu = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\Hermes Five Choices'
        New-Item -ItemType Directory -Path $startMenu -Force | Out-Null
        foreach ($entry in @(
            @('Hermes Five Choices.lnk', $launcher, 'Open Hermes Five Choices'),
            @('Connect Account.lnk', (Join-Path $installed 'installer\setup_account.bat'), 'Connect a provider account'),
            @('Run Diagnostics.lnk', (Join-Path $installed 'installer\diagnostics.bat'), 'Verify runtime, profiles and services'),
            @('Uninstall Hermes Five Choices.lnk', $uninstaller, 'Uninstall while preserving data')
        )) {
            $shortcut = $shell.CreateShortcut((Join-Path $startMenu $entry[0]))
            $shortcut.TargetPath = $entry[1]
            $shortcut.WorkingDirectory = $installed
            $shortcut.Description = $entry[2]
            $shortcut.Save()
        }
        $startup = [Environment]::GetFolderPath('Startup')
        $startupShortcut = $shell.CreateShortcut((Join-Path $startup 'Hermes Five Choices.lnk'))
        $startupShortcut.TargetPath = (Join-Path $installed 'start_background.bat')
        $startupShortcut.WorkingDirectory = $installed
        $startupShortcut.Description = 'Start Hermes Five Choices services after sign-in'
        $startupShortcut.WindowStyle = 7
        $startupShortcut.Save()
    }
    if ($env:H5_SKIP_SETUP -ne '1') {
        Start-Process -FilePath (Join-Path $installed 'installer\setup_account.bat') -Wait
    }
    if ($env:H5_NO_LAUNCH -ne '1') { Start-Process -FilePath $launcher }
    exit 0
}
catch {
    $_ | Out-String | Set-Content -LiteralPath $log -Encoding UTF8
    exit 1
}
