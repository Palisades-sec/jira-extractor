@echo off
setlocal EnableDelayedExpansion

:: Jira Configuration
set JIRA_URL=https://your-jira-instance.atlassian.net
set JIRA_USERNAME=your_email@example.com
set JIRA_API_TOKEN=your_api_token
set JIRA_JQL=project = PROJ AND created >= -30d
set GOOGLE_CREDENTIALS_FILE_PATH=path/to/your/credentials.json

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Run the script
echo Running Jira Ticket Extractor...
python jira_ticket_extractor.py --url "%JIRA_URL%" --username "%JIRA_USERNAME%" --api-token "%JIRA_API_TOKEN%" --jql "%JIRA_JQL%" --google-creds "%GOOGLE_CREDENTIALS_FILE_PATH%"

if %errorlevel% neq 0 (
    echo Error occurred while running the script
    pause
    exit /b 1
)

echo Script completed successfully
pause 