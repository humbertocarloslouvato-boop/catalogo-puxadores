' Wrapper invisivel para o auto_backup do Ruflo
' Roda o .bat sem abrir nenhuma janela de terminal (window style = 0)
' Criado para resolver o problema do terminal piscando a cada 15 min.
Set WshShell = CreateObject("WScript.Shell")
rc = WshShell.Run("cmd /c ""C:\Users\humbe\continuous-memory\auto_backup.bat""", 0, True)
' Propaga o exit code pro Task Scheduler (antes falhava calado)
WScript.Quit rc
