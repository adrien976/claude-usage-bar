@echo off
chcp 65001 >nul
title Installation de Claude Usage Bar
echo.
echo   ==========================================
echo    Claude Usage Bar - Installation Windows
echo   ==========================================
echo.

REM --- 1. Verifier Python ---
where pythonw >nul 2>nul
if %errorlevel%==0 goto haspython
where python >nul 2>nul
if %errorlevel%==0 goto haspython

echo  Python n'est pas installe. Tentative d'installation via winget...
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
  echo.
  echo  [!] Impossible d'installer Python automatiquement.
  echo      Installe-le depuis https://www.python.org/downloads/
  echo      en cochant "Add Python to PATH", puis relance ce fichier.
  pause
  exit /b 1
)

:haspython
echo  [OK] Python detecte.
echo.

REM --- 2. Dependances ---
echo  Installation des composants (pystray, Pillow, keyring)...
python -m pip install --user --upgrade pip >nul 2>nul
python -m pip install --user pystray Pillow keyring
if %errorlevel% neq 0 (
  echo  [!] Echec de l'installation des composants.
  pause
  exit /b 1
)

REM --- 3. Copier l'application ---
set "DEST=%APPDATA%\ClaudeUsageBar"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0claude_usage_tray.pyw" "%DEST%\" >nul
echo  [OK] Application installee dans %DEST%

REM --- 4. Lancement automatique au demarrage de Windows ---
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([Environment]::GetFolderPath('Startup')+'\ClaudeUsageBar.lnk'); $p=(Get-Command pythonw -ErrorAction SilentlyContinue).Source; if(-not $p){$p=(Get-Command python).Source}; $s.TargetPath=$p; $s.Arguments='\"%DEST%\claude_usage_tray.pyw\"'; $s.WorkingDirectory='%DEST%'; $s.Save()"
echo  [OK] Lancement automatique configure.

REM --- 5. Demarrer maintenant ---
echo.
echo  Demarrage... une fenetre va te demander d'autoriser ton compte Claude.
start "" pythonw "%DEST%\claude_usage_tray.pyw"

echo.
echo  ==========================================
echo   Termine ! Cherche l'icone en bas a droite
echo   (zone de notification, pres de l'horloge).
echo  ==========================================
echo.
pause
