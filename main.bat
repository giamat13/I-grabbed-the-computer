@echo off
setlocal enabledelayedexpansion
title Mouse Locker

:: שלב הגדרת שם וסיסמה
:setup
cls
echo [LOCKER SETUP]
set /p "u_name=What is your name? "
echo.
set /p "pass1=Set Password: "
set /p "pass2=Confirm Password: "

if not "%pass1%"=="%pass2%" (
    cls
    echo Passwords do not match! Try again.
    timeout /t 2 >nul
    goto setup
)

:: הקפצת הודעת המערכת
msg * %u_name% CAUGHT THE COMPUTER!

:: הפעלת נעילת העכבר (ללא חלון נסתר כדי למנוע תקיעה)
start /b powershell -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.Windows.Forms; while($true) { [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point(0,0); Start-Sleep -Milliseconds 50 }" >nul 2>&1

:unlock_attempt
cls
echo ===================================================
echo   %u_name% CAUGHT THE COMPUTER!
echo ===================================================
echo.
echo The mouse is locked. Enter password to release.
echo.
set /p "attempt=Enter Password: "

if "%attempt%"=="%pass1%" (
    :: שחרור העכבר
    taskkill /f /im powershell.exe >nul 2>&1
    echo.
    echo ACCESS GRANTED!
    echo Mouse Released.
    timeout /t 2 >nul
    exit
) else (
    echo.
    echo [!] WRONG PASSWORD!
    :: הקפצה חוזרת של ההודעה למי שמנסה לפרוץ
    msg * ACCESS DENIED - WRONG PASSWORD!
    ping 127.0.0.1 -n 2 >nul
    goto unlock_attempt
)