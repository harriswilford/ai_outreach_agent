' Windows VBScript to run Autonomous AI Background Daemon completely hidden
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = scriptDir

pyRunner = "C:\Python314\pythonw.exe"
If Not fso.FileExists(pyRunner) Then
    pyRunner = "pythonw.exe"
End If

objShell.Run """" & pyRunner & """ """ & scriptDir & "\background_daemon.py"" run", 0, False
