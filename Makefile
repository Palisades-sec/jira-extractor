# Include .env file
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Jira Configuration
JIRA_URL = https://xyzyxzcom.atlassian.net
JIRA_USERNAME = xyzyxz.com@gmail.com
JIRA_API_TOKEN = ATATT3xFfGF0TfvxDLMOJWfzmsVD0zjeN0omN7eJHJ_Y33Q1NInf1ij2JGVsCWI3qVT-w4TXSoVFn2P3lht3TqfZqMzNltW12es4PV8vKTsIUj0AdcVBDk0gtKJvTA0_LS6g9VpZ3D5ybopuGPFsQZW3GgVHX2F17plRUKaWxedOBU5zQpqvdIE=261324F8
JIRA_JQL = "project = KAN AND created >= -30d"
GOOGLE_CREDENTIALS_FILE_PATH = credentials/gcp.json

# Python command (use python or python3 depending on your system)
PYTHON = python

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

# Check if .env file exists
check-env:
	@test -f .env || (echo ".env file not found"; exit 1)

# Run the Jira ticket extractor
run-extractor: check-python check-env
	@echo "Running Jira Ticket Extractor..."
	@echo "Using configuration from .env file..."
	@$(PYTHON) jira_extractor_script.py \
		--url "$(JIRA_URL)" \
		--username "$(JIRA_USERNAME)" \
		--api-token "$(JIRA_API_TOKEN)" \
		--jql "$(JIRA_JQL)"

# Alias for running the extractor
run: run-extractor 