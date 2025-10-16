@echo off
echo ========================================
echo   AI Document Structurer - Python
echo ========================================
echo.
echo Starting server at: http://localhost:5000
echo.
echo *** CLOSE THIS WINDOW TO STOP THE SERVER ***
echo.

REM Start the Flask server in background and wait for it to be ready
start /B python server.py

REM Wait for server to be ready by checking if port 5000 is listening
echo Waiting for server to start...
:wait_loop
timeout /t 1 /nobreak >nul
netstat -an | find ":5000" | find "LISTENING" >nul
if errorlevel 1 goto wait_loop

REM Server is ready, now open browser
echo Server is ready! Opening browser...
start "" http://localhost:5000

REM Keep the window open to show server logs
echo.
echo Server is running. Check the console for logs.
echo Press Ctrl+C to stop the server, then any key to exit.
pause

REM Server stopped
echo.
echo Server stopped. Press any key to exit.
pause
