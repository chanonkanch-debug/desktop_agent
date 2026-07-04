Dim fso, folder, python, appPy, sh, cmd
Set fso    = CreateObject("Scripting.FileSystemObject")
folder     = fso.GetParentFolderName(WScript.ScriptFullName)
python     = folder & "\venv\Scripts\python.exe"
appPy      = folder & "\app.py"
cmd        = Chr(34) & python & Chr(34) & " " & Chr(34) & appPy & Chr(34)
Set sh     = CreateObject("WScript.Shell")
sh.Run cmd, 0, False   ' 0 = hidden window, False = don't wait
