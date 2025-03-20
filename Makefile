# Jira Configuration
JIRA_URL = https://your-jira-instance.atlassian.net
JIRA_USERNAME = your_email@example.com
JIRA_API_TOKEN = your_api_token
JIRA_JQL = "project = PROJ AND created >= -30d"
GOOGLE_CREDENTIALS_FILE_PATH = path/to/your/credentials.json

# Python command
PYTHON = python3

.PHONY: check-python run-extractor help

# Default target
all: check-python run-extractor

# Help command
help:
	@echo "Available commands:"
	@echo "  make run        - Run the Jira ticket extractor"
	@echo "  make check     - Check if Python is installed"
	@echo "  make help      - Show this help message"

# Check if Python is installed
check-python:
	@which $(PYTHON) > /dev/null || (echo "Python is not installed"; exit 1)

# Run the Jira ticket extractor
run-extractor: check-python
	@echo "Running Jira Ticket Extractor..."
	@$(PYTHON) jira_ticket_extractor.py \
		--url "$(JIRA_URL)" \
		--username "$(JIRA_USERNAME)" \
		--api-token "$(JIRA_API_TOKEN)" \
		--jql $(JIRA_JQL) \
		--google-creds "$(GOOGLE_CREDENTIALS_FILE_PATH)"

# Alias for running the extractor
run: run-extractor 