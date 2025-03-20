#!/usr/bin/env python3
import os
import json
import requests
import html2text
import mimetypes
from urllib.parse import urlparse
import logging
from jira import JIRA
import base64
from datetime import datetime
import re
import argparse
from PyPDF2 import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("jira_extractor.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class JiraTicketExtractor:
    def __init__(self, jira_url, username=None, api_token=None):
        """
        Initialize Jira client with authentication

        Args:
            jira_url (str): URL of the Jira instance
            username (str): Jira username
            api_token (str): Jira API token or password
        """
        self.jira_url = jira_url
        self.output_dir = "jira_tickets"

        # Setup Jira client
        if username and api_token:
            self.jira = JIRA(server=jira_url, basic_auth=(username, api_token))
            logger.info(f"Connected to Jira at {jira_url}")
        else:
            # Try using environment variables
            username = os.environ.get("JIRA_USERNAME")
            api_token = os.environ.get("JIRA_API_TOKEN")

            if username and api_token:
                self.jira = JIRA(server=jira_url, basic_auth=(username, api_token))
                logger.info(f"Connected to Jira using environment credentials")
            else:
                raise ValueError(
                    "No credentials provided. Use parameters or set JIRA_USERNAME and JIRA_API_TOKEN environment variables"
                )

        # Initialize session for requests
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False

    def extract_tickets(self, jql_query, max_results=50):
        """
        Extract tickets based on JQL query

        Args:
            jql_query (str): JQL query to find tickets
            max_results (int): Maximum number of tickets to retrieve
        """
        logger.info(f"Extracting tickets using query: {jql_query}")

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Fetch issues based on JQL query
        issues = self.jira.search_issues(jql_query, maxResults=max_results)
        logger.info(f"Found {len(issues)} tickets")

        # Process each issue
        for issue in issues:
            self.process_ticket(issue)

    def process_ticket(self, issue):
        """
        Process a single Jira ticket

        Args:
            issue: Jira issue object
        """
        ticket_key = issue.key
        logger.info(f"Processing ticket: {ticket_key}")

        # Create ticket directory
        ticket_dir = os.path.join(self.output_dir, ticket_key)
        if not os.path.exists(ticket_dir):
            os.makedirs(ticket_dir)

        # Extract basic ticket information
        ticket_info = {
            "key": ticket_key,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "status": issue.fields.status.name,
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "issueType": issue.fields.issuetype.name,
            "assignee": (
                getattr(issue.fields.assignee, "displayName", "Unassigned")
                if issue.fields.assignee
                else "Unassigned"
            ),
            "reporter": (
                getattr(issue.fields.reporter, "displayName", "Unknown")
                if issue.fields.reporter
                else "Unknown"
            ),
        }

        # Save ticket information as JSON
        with open(os.path.join(ticket_dir, f"{ticket_key}_info.json"), "w") as f:
            json.dump(ticket_info, f, indent=4)

        # Convert ticket to PDF
        self.convert_ticket_to_pdf(issue, ticket_dir)

        # Extract attachments
        self.extract_attachments(issue, ticket_dir)

        # Extract links from description and comments
        self.extract_links_from_description(issue, ticket_dir)
        self.extract_links_from_comments(issue, ticket_dir)

    def convert_ticket_to_pdf(self, issue, ticket_dir):
        """
        Convert ticket information to PDF

        Args:
            issue: Jira issue object
            ticket_dir (str): Directory to save PDF
        """
        pdf_path = os.path.join(ticket_dir, f"{issue.key}.pdf")

        # Create a PDF with ticket information
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 16)
        can.drawString(72, 750, f"Jira Ticket: {issue.key}")

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 720, "Summary:")
        can.setFont("Helvetica", 12)
        text = issue.fields.summary
        can.drawString(72, 700, text[:80])
        if len(text) > 80:
            can.drawString(72, 685, text[80:160])

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 660, "Status:")
        can.setFont("Helvetica", 12)
        can.drawString(200, 660, issue.fields.status.name)

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 640, "Issue Type:")
        can.setFont("Helvetica", 12)
        can.drawString(200, 640, issue.fields.issuetype.name)

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 620, "Created:")
        can.setFont("Helvetica", 12)
        can.drawString(200, 620, issue.fields.created)

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 600, "Updated:")
        can.setFont("Helvetica", 12)
        can.drawString(200, 600, issue.fields.updated)

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 580, "Assignee:")
        can.setFont("Helvetica", 12)
        assignee = (
            getattr(issue.fields.assignee, "displayName", "Unassigned")
            if issue.fields.assignee
            else "Unassigned"
        )
        can.drawString(200, 580, assignee)

        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 560, "Reporter:")
        can.setFont("Helvetica", 12)
        reporter = (
            getattr(issue.fields.reporter, "displayName", "Unknown")
            if issue.fields.reporter
            else "Unknown"
        )
        can.drawString(200, 560, reporter)

        # Add description
        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, 520, "Description:")
        can.setFont("Helvetica", 10)

        # Handle description text
        description = (
            issue.fields.description
            if issue.fields.description
            else "No description provided."
        )
        # Convert from Jira markup to plain text
        if description:
            plain_desc = self.h2t.handle(description)
            y_position = 500
            for line in plain_desc.split("\n")[
                :20
            ]:  # Limit to first 20 lines for simplicity
                if line.strip():
                    can.drawString(72, y_position, line[:100])
                    y_position -= 15
                    if y_position < 72:
                        break

        can.save()

        # Move to the beginning of the StringIO buffer
        packet.seek(0)

        # Create a new PDF with Reportlab's content
        new_pdf = PdfWriter()
        new_pdf.add_page()

        # Write the content to the PDF
        with open(pdf_path, "wb") as f:
            new_pdf.write(f)

        logger.info(f"Saved ticket PDF to {pdf_path}")

    def extract_attachments(self, issue, ticket_dir):
        """
        Extract attachments from a Jira ticket

        Args:
            issue: Jira issue object
            ticket_dir (str): Directory to save attachments
        """
        attachments_dir = os.path.join(ticket_dir, "attachments")
        if not os.path.exists(attachments_dir):
            os.makedirs(attachments_dir)

        for attachment in issue.fields.attachment:
            logger.info(f"Downloading attachment: {attachment.filename}")

            # Get attachment content
            attachment_data = self.jira.attachment(attachment.id)

            # Save attachment
            attachment_path = os.path.join(attachments_dir, attachment.filename)
            with open(attachment_path, "wb") as f:
                f.write(attachment_data)

            logger.info(f"Saved attachment to {attachment_path}")

    def extract_links_from_description(self, issue, ticket_dir):
        """
        Extract and process links from ticket description

        Args:
            issue: Jira issue object
            ticket_dir (str): Directory to save extracted content
        """
        if not issue.fields.description:
            return

        links_dir = os.path.join(ticket_dir, "links")
        if not os.path.exists(links_dir):
            os.makedirs(links_dir)

        # Extract URLs using regex
        description = issue.fields.description
        urls = re.findall(
            r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?", description
        )

        for url in urls:
            self.process_link(url, links_dir, f"description_link_{urls.index(url)}")

    def extract_links_from_comments(self, issue, ticket_dir):
        """
        Extract and process links from ticket comments

        Args:
            issue: Jira issue object
            ticket_dir (str): Directory to save extracted content
        """
        comments = self.jira.comments(issue)

        if not comments:
            return

        links_dir = os.path.join(ticket_dir, "links")
        if not os.path.exists(links_dir):
            os.makedirs(links_dir)

        for comment in comments:
            if comment.body:
                # Extract URLs using regex
                urls = re.findall(
                    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?",
                    comment.body,
                )

                for url in urls:
                    self.process_link(
                        url, links_dir, f"comment_{comment.id}_link_{urls.index(url)}"
                    )

    def process_link(self, url, links_dir, prefix):
        """
        Process a link based on its type (Google Docs, Confluence, etc.)

        Args:
            url (str): URL to process
            links_dir (str): Directory to save extracted content
            prefix (str): Prefix for saved files
        """
        logger.info(f"Processing link: {url}")

        domain = urlparse(url).netloc

        # Handle different types of links
        if "docs.google.com" in domain or "drive.google.com" in domain:
            self.process_google_link(url, links_dir, prefix)
        elif "confluence" in domain:
            self.process_confluence_link(url, links_dir, prefix)
        else:
            self.process_generic_link(url, links_dir, prefix)

    def process_google_link(self, url, links_dir, prefix):
        """
        Process Google Docs/Drive links

        Args:
            url (str): URL to process
            links_dir (str): Directory to save extracted content
            prefix (str): Prefix for saved files
        """
        logger.info("Processing Google link (API integration would be required)")

        # Save link for reference
        link_info = {
            "url": url,
            "type": "google_doc",
            "note": "Google API integration required to extract content",
        }

        with open(os.path.join(links_dir, f"{prefix}_google_link.json"), "w") as f:
            json.dump(link_info, f, indent=4)

        # Note: To fully implement Google Docs extraction, you would need to:
        # 1. Set up Google API credentials
        # 2. Use the Google Drive API to access the document
        # 3. Export it as PDF or extract the content
        # This is beyond the scope of this example script

    def process_confluence_link(self, url, links_dir, prefix):
        """
        Process Confluence links

        Args:
            url (str): URL to process
            links_dir (str): Directory to save extracted content
            prefix (str): Prefix for saved files
        """
        logger.info(f"Processing Confluence link: {url}")

        try:
            # Extract page ID from URL
            page_id = None
            if "pageId=" in url:
                page_id = re.search(r"pageId=(\d+)", url).group(1)
            else:
                # Try to get the page content directly
                response = self.session.get(url)
                response.raise_for_status()

                # Save the HTML content
                html_path = os.path.join(links_dir, f"{prefix}_confluence.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(response.text)

                # Convert HTML to text
                text_content = self.h2t.handle(response.text)

                # Save as text
                text_path = os.path.join(links_dir, f"{prefix}_confluence.txt")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(text_content)

                # Convert to PDF
                self.html_to_pdf(
                    response.text, os.path.join(links_dir, f"{prefix}_confluence.pdf")
                )

                logger.info(f"Saved Confluence content to {links_dir}")

        except Exception as e:
            logger.error(f"Failed to process Confluence link: {e}")

            # Save link for reference
            link_info = {"url": url, "type": "confluence", "error": str(e)}

            with open(
                os.path.join(links_dir, f"{prefix}_confluence_link.json"), "w"
            ) as f:
                json.dump(link_info, f, indent=4)

    def process_generic_link(self, url, links_dir, prefix):
        """
        Process generic web links

        Args:
            url (str): URL to process
            links_dir (str): Directory to save extracted content
            prefix (str): Prefix for saved files
        """
        logger.info(f"Processing generic link: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Determine content type
            content_type = response.headers.get("Content-Type", "").lower()

            if "text/html" in content_type:
                # Save the HTML content
                html_path = os.path.join(links_dir, f"{prefix}_webpage.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(response.text)

                # Convert HTML to text
                text_content = self.h2t.handle(response.text)

                # Save as text
                text_path = os.path.join(links_dir, f"{prefix}_webpage.txt")
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(text_content)

                # Convert to PDF
                self.html_to_pdf(
                    response.text, os.path.join(links_dir, f"{prefix}_webpage.pdf")
                )

            elif "application/pdf" in content_type:
                # Save the PDF directly
                pdf_path = os.path.join(links_dir, f"{prefix}_document.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(response.content)

            else:
                # For other content types, just save the raw content
                ext = mimetypes.guess_extension(content_type.split(";")[0]) or ".bin"
                file_path = os.path.join(links_dir, f"{prefix}_content{ext}")
                with open(file_path, "wb") as f:
                    f.write(response.content)

            logger.info(f"Saved link content to {links_dir}")

        except Exception as e:
            logger.error(f"Failed to process link: {e}")

            # Save link for reference
            link_info = {"url": url, "type": "generic", "error": str(e)}

            with open(os.path.join(links_dir, f"{prefix}_link.json"), "w") as f:
                json.dump(link_info, f, indent=4)

    def html_to_pdf(self, html_content, output_path):
        """
        Convert HTML content to PDF

        Args:
            html_content (str): HTML content to convert
            output_path (str): Path to save the PDF
        """
        try:
            # Extract text from HTML
            text_content = self.h2t.handle(html_content)

            # Create a PDF with text content
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 10)

            # Add text to PDF
            y_position = 750
            for line in text_content.split("\n")[
                :100
            ]:  # Limit to first 100 lines for simplicity
                if line.strip():
                    can.drawString(72, y_position, line[:100])
                    y_position -= 15
                    if y_position < 72:
                        break

            can.save()
            packet.seek(0)

            # Create a new PDF
            new_pdf = PdfWriter()
            new_pdf.add_page()

            # Write the content to the PDF
            with open(output_path, "wb") as f:
                new_pdf.write(f)

            logger.info(f"Converted HTML to PDF at {output_path}")

        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Jira tickets and their attachments/links"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Jira URL (e.g., https://your-domain.atlassian.net)",
    )
    parser.add_argument("--username", help="Jira username (email)")
    parser.add_argument("--api-token", help="Jira API token")
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

    args = parser.parse_args()

    try:
        # Create extractor
        extractor = JiraTicketExtractor(args.url, args.username, args.api_token)

        # Extract tickets
        extractor.extract_tickets(args.jql, args.max_results)

        logger.info("Ticket extraction completed successfully")

    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
