$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
$main = Join-Path $PSScriptRoot 'main.py'
if (-not (Test-Path $python)) { throw 'Önce KURULUM.bat dosyasını çalıştırın.' }
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'JARVIS.lnk'
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcutPath)
$link.TargetPath = $python
$link.Arguments = '"' + $main + '"'
$link.WorkingDirectory = $PSScriptRoot
$link.Description = 'JARVIS kişisel asistan'
$link.Save()
Write-Host 'Masaustune JARVIS kisayolu eklendi.'
