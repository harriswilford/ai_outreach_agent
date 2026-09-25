# PowerShell script to register the Autonomous AI Agent to run on Windows Startup
$TaskName = "AutonomousTakeoffLeadAgent"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VbsPath = Join-Path $ScriptDir "start_background_agent.vbs"
$StartupFolder = [System.Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder "$TaskName.lnk"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  AUTONOMOUS AI BACKGROUND AGENT - WINDOWS AUTO-START SETUP" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Method 1: Windows User Startup Folder (No Admin Rights Needed)
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "wscript.exe"
    $Shortcut.Arguments = "`"$VbsPath`""
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.WindowStyle = 7 # Minimized/Hidden
    $Shortcut.Description = "Autonomous AI Takeoff Lead Acquisition Agent"
    $Shortcut.Save()
    Write-Host "[+] Startup Shortcut created in: $ShortcutPath" -ForegroundColor Green
    $Success = $true
} catch {
    Write-Host "[!] Failed to create Startup Shortcut: $_" -ForegroundColor Yellow
}

# Method 2: Current User Registry Run Key
try {
    $RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    Set-ItemProperty -Path $RegPath -Name $TaskName -Value "wscript.exe `"$VbsPath`"" -Force
    Write-Host "[+] Windows User Auto-Run Registry Key configured successfully." -ForegroundColor Green
    $Success = $true
} catch {
    Write-Host "[!] Registry auto-run note: $_" -ForegroundColor Yellow
}

if ($Success) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host " [SUCCESS] Auto-Start Registered Successfully!" -ForegroundColor Green
    Write-Host " The AI Agent will now launch silently in the background on every PC boot." -ForegroundColor Green
    Write-Host " To remove auto-start at any time, run: .\unregister_windows_startup_task.ps1" -ForegroundColor Gray
    Write-Host "======================================================================" -ForegroundColor Green
} else {
    Write-Host "[!] Could not configure auto-start." -ForegroundColor Red
}
Write-Host ""
