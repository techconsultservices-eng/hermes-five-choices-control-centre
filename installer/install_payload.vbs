Option Explicit
Dim shell, fso, base, command, rc, logPath, message, silent
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
logPath = shell.ExpandEnvironmentStrings("%TEMP%\HermesFiveChoicesInstaller.log")
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & base & "\install_payload.ps1"""
silent = (shell.ExpandEnvironmentStrings("%H5_SILENT%") = "1")
If Not silent Then MsgBox "Hermes Five Choices will now install its private frozen runtime. This can take several minutes. No existing Hermes installation or credentials will be copied.", 64, "Hermes Five Choices"
rc = shell.Run(command, 0, True)
If rc = 0 Then
  If Not silent Then MsgBox "Hermes Five Choices was installed and is starting.", 64, "Hermes Five Choices"
Else
  message = "Installation did not complete. No success has been assumed." & vbCrLf & vbCrLf & "Diagnostic log: " & logPath
  If Not silent Then MsgBox message, 16, "Hermes Five Choices"
End If
