param([switch]$Remove)
$ErrorActionPreference = 'Stop'
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'JARVIS.lnk'
if ($Remove) {
    if (Test-Path $shortcutPath) { Remove-Item -LiteralPath $shortcutPath }
    Write-Host 'JARVIS otomatik baslatma kaldirildi.'
    exit
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $python)) { throw 'Once KURULUM.bat dosyasini calistirin.' }
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($shortcutPath)
$link.TargetPath = $python
$link.Arguments = '"' + (Join-Path $PSScriptRoot 'main.py') + '"'
$link.WorkingDirectory = $PSScriptRoot
$link.Description = 'JARVIS v0.1'
$link.Save()
Write-Host 'JARVIS kullanici oturumu acildiginda baslayacak. Proje klasorunu tasimayin.'
