# PowerShell script to unregister the Autonomous AI Agent from Windows Startup
$TaskName = "AutonomousTakeoffLeadAgent"
$StartupFolder = [System.Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder "$TaskName.lnk"

Write-Host "======================================================================" -ForegroundColor Yellow
Write-Host "  AUTONOMOUS AI BACKGROUND AGENT - REMOVING AUTO-START" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Yellow

# Remove from Startup folder
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "[+] Removed Startup Shortcut: $ShortcutPath" -ForegroundColor Green
}

# Remove from Registry
try {
    $RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    if (Get-ItemProperty -Path $RegPath -Name $TaskName -ErrorAction SilentlyContinue) {
        Remove-ItemProperty -Path $RegPath -Name $TaskName -Force
        Write-Host "[+] Removed Registry Auto-Run Key." -ForegroundColor Green
    }
} catch {
    # Ignore
}

# Remove Task Scheduler task if any exists
$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[+] Removed Scheduled Task: $TaskName" -ForegroundColor Green
}

Write-Host ""
Write-Host "[SUCCESS] Auto-start entries removed cleanly." -ForegroundColor Green
Write-Host ""
