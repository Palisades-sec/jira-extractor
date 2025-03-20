#!/usr/bin/env python3
import os
import argparse
import logging
from dotenv import load_dotenv
from jira_extractor.jira_extractor_script import JiraTicketExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def extract_jira(args):
    """Handle Jira extraction"""
    try:
        # Validate required Jira parameters
        if not all([args.url, args.username, args.api_token, args.jql]):
            raise ValueError(
                "For Jira extraction, --url, --username, --api-token, and --jql are required "
                "or must be set in environment variables"
            )
            
        # Create extractor
        extractor = JiraTicketExtractor(args.url, args.username, args.api_token)

        # Extract tickets
        extractor.extract_tickets(args.jql, args.max_results)
        
        logger.info("Jira ticket extraction completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Jira extraction failed: {str(e)}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Extract data from various sources"
    )
    parser.add_argument(
        "--extract",
        choices=["jira"],
        required=True,
        help="Specify what to extract (currently supports: jira)",
    )
    
    # Get the initial args to check the extract type
    args, remaining_args = parser.parse_known_args()
    
    if args.extract == "jira":
        # Jira-specific arguments
        parser.add_argument(
            "--url",
            default=os.getenv("JIRA_URL"),
            help="Jira URL (e.g., https://your-domain.atlassian.net)",
        )
        parser.add_argument(
            "--username",
            default=os.getenv("JIRA_USERNAME"),
            help="Jira username (email)",
        )
        parser.add_argument(
            "--api-token",
            default=os.getenv("JIRA_API_TOKEN"),
            help="Jira API token",
        )
        parser.add_argument(
            "--jql",
            default=os.getenv("JIRA_JQL"),
            help='JQL query to select tickets (e.g., "project = PROJ AND created >= -30d")',
        )
        parser.add_argument(
            "--max-results",
            type=int,
            default=50,
            help="Maximum number of tickets to process",
        )

    # Parse all arguments after adding the appropriate ones
    args = parser.parse_args()

    # Handle different extraction types
    if args.extract == "jira":
        return extract_jira(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())
