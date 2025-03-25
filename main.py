#!/usr/bin/env python3
import os
import sys
import argparse
from dotenv import load_dotenv
from jira_extractor.config.logger import logger
from jira_extractor.core.extractor import JiraTicketExtractor

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract Jira tickets and their attachments/links"
    )
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
        required=True,
        help='JQL query to select tickets (e.g., "project = PROJ AND created >= -30d")',
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of tickets to process",
    )
    
    return parser.parse_args()

def main():
    """Main entry point of the script"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Parse arguments
        args = parse_arguments()
        
        # Validate required arguments
        if not all([args.url, args.jql]):
            logger.error("Missing required arguments: url and jql must be provided")
            return 1
        
        # Create and run extractor
        extractor = JiraTicketExtractor(args.url, args.username, args.api_token)
        success = extractor.extract_tickets(args.jql, args.max_results)
        
        if success:
            logger.info("Ticket extraction completed successfully")
            return 0
        else:
            logger.error("Ticket extraction completed with errors")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 