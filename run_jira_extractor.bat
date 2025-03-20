@echo off
setlocal EnableDelayedExpansion

:: Change to the script's directory
cd /d "%~dp0"

:: Read from .env file
if not exist ".env" (
    echo Error: .env file not found
    pause
    exit /b 1
)

:: Load environment variables from .env
for /f "tokens=1,* delims==" %%A in (.env) do (
    if not "%%A"=="" (
        if not "%%B"=="" (
            :: Remove any comments and trim spaces
            for /f "tokens=1,* delims=#" %%X in ("%%B") do (
                set "%%A=%%X"
            )
        )
    )
)

:: Check if required environment variables are set
if not defined JIRA_URL (
    echo Error: JIRA_URL not set in .env file
    pause
    exit /b 1
)
if not defined JIRA_USERNAME (
    echo Error: JIRA_USERNAME not set in .env file
    pause
    exit /b 1
)
if not defined JIRA_API_TOKEN (
    echo Error: JIRA_API_TOKEN not set in .env file
    pause
    exit /b 1
)
if not defined JIRA_JQL (
    echo Error: JIRA_JQL not set in .env file
    pause
    exit /b 1
)

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if the script exists
if not exist "jira_extractor_script.py" (
    echo Error: jira_extractor_script.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Create jira_tickets directory if it doesn't exist
if not exist "jira_tickets" (
    mkdir "jira_tickets"
    echo Created jira_tickets directory
)

:: Display configuration (for debugging)
echo Using configuration:
echo JIRA_URL: %JIRA_URL%
echo JIRA_USERNAME: %JIRA_USERNAME%
echo JIRA_JQL: %JIRA_JQL%

:: Run the script
echo Running Jira Ticket Extractor...
python jira_extractor_script.py --url "%JIRA_URL%" --username "%JIRA_USERNAME%" --api-token "%JIRA_API_TOKEN%" --jql "%JIRA_JQL%"

if %errorlevel% neq 0 (
    echo Error occurred while running the script
    echo Exit code: %errorlevel%
    pause
    exit /b 1
)

echo Script completed successfully
echo Check the jira_tickets directory for extracted data
pause 