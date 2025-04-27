import traceback
import requests
from urllib.parse import urlparse
import json
from ..config.logger import logger
from .file_utils import FileUtils
from .confluence_helper import ConfluencePagehelper, ConfluenceConfig
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import re
from jira_extractor.core.converter import PDFConverter

def save_text_as_pdf(text_content, pdf_path, title=None):
    # Setup PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    # Add title if provided
    if title:
        title_style = styles["Heading1"]
        Story.append(Paragraph(title, title_style))
        Story.append(Spacer(1, 20))  # Add space after title

    # Split text into paragraphs (if needed)
    paragraphs = text_content.split('\n')

    for para in paragraphs:
        if para.strip():  # Avoid empty lines
            Story.append(Paragraph(para.strip(), styles["Normal"]))
            Story.append(Spacer(1, 12))  # 12 points space after each paragraph

    # Build PDF
    doc.build(Story)


class LinkHandler:
    def __init__(self, session, jira_client, project_key = None, jira_config = None):
        """
        Initialize link handler
        
        Args:
            session (requests.Session): Authenticated session for requests
            jira_client: Authenticated Jira client
            project_key (str, optional): Project key for filtering
            jira_config: Jira configuration object
        """
        self.session = session
        self.jira = jira_client
        self.project_key = project_key
        
        # Initialize Confluence helper with Jira credentials
        confluence_config = ConfluenceConfig(
            url=jira_config.jira_url,
            username=jira_config.username,
            api_token=jira_config.api_token,
            cloud=True
        )
        self.confluence_helper = ConfluencePagehelper(
            atlassian_url=jira_config.jira_url,
            atlassian_api_user=jira_config.username,
            atlassian_api_token=jira_config.api_token
        )

    def process_link(self, url, links_dir, prefix):
        """
        Process a link based on its type
        
        Args:
            url (str): URL to process
            links_dir (str): Directory to save extracted content
            prefix (str): Prefix for saved files
        """
        try:
            domain = urlparse(url).netloc
            logger.info(f"Processing link {url} with domain {domain}")
            # Handle different types of links
            if "docs.google.com" in domain or "drive.google.com" in domain:
                return self.process_google_link(url, links_dir, prefix)
            elif ("wiki" and "spaces" and "pages" ) in url:
                logger.info(f"Processing Confluence link {url}")
                return self.process_confluence_link(url, links_dir, prefix)
            # # if project key is not none and in project key in  domain
            elif self.project_key and ("browse" in url):
                logger.info(f"Processing Jira link {url}")
                return self.process_jira_link(url, links_dir, prefix)
        except Exception as e:
            logger.error(f"Failed to process link {url}: {str(e)}")
            return False

    def process_google_link(self, url, links_dir, prefix):
        """
        Process Google Docs/Drive links
        """
        try:
            link_info = {
                "url": url,
                "type": "google_doc",
                "note": "Google API integration required to extract content"
            }
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_google_link.json",
                json.dumps(link_info, indent=4)
            )
        except Exception as e:
            logger.error(f"Failed to process Google link {url}: {str(e)}")
            return False

    def process_confluence_link(self, url, links_dir, prefix):
        """
        Process Confluence links using ConfluencePagehelper and save content as PDF
        """
        try:
            logger.info(f"Processing Confluence link {url}")
            # Get content, attachments and links from Confluence page
            content, attachments, links = self.confluence_helper.get_content_by_page_url(url)
            
            # Get text content
            text_content = self.confluence_helper.text_from_html(content.content)

            logger.info(f"Text content: {text_content}")
            
            # Save text content as PDF with title
            pdf_path = f"{links_dir}/{content.title}_confluence.pdf"
            save_text_as_pdf(text_content, pdf_path, title=content.title)
            
            # Save attachments if any
            if attachments:
                for i, attachment in enumerate(attachments):
                    try:
                        response = self.session.get(str(attachment))
                        response.raise_for_status()
                        attachment_name = f"{prefix}_attachment_{i+1}.pdf"
                        FileUtils.save_file(
                            f"{links_dir}/{attachment_name}",
                            response.content,
                            mode='wb'
                        )
                    except Exception as e:
                        logger.error(f"Failed to save attachment {attachment}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Confluence link {url}: {str(e)}")
            logger.error(traceback.format_exc())
            link_info = {"url": url, "type": "confluence", "error": str(e)}
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_confluence_link.json",
                json.dumps(link_info, indent=4)
            )

    def process_jira_link(self, url, links_dir, prefix):
        """
        Process Jira ticket links by extracting ticket data as JSON and PDF
        """
        try:
            # Extract ticket key from URL
            ticket_key = url.split('/')[-1]
            
            # Get ticket data from Jira
            issue = self.jira.issue(ticket_key)
            
            # Create ticket directory structure
            ticket_dir = os.path.join(links_dir, ticket_key)
            if not FileUtils.ensure_directory(ticket_dir):
                return False
            
            # Create links directory for nested links
            nested_links_dir = os.path.join(ticket_dir, "links")
            if not FileUtils.ensure_directory(nested_links_dir):
                return False
            
            # Save ticket data as JSON
            ticket_data = {
                "key": issue.key,
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
            
            # Save JSON
            json_saved = FileUtils.save_file(
                os.path.join(ticket_dir, f"{ticket_key}.json"),
                json.dumps(ticket_data, indent=4)
            )
            
            # Create PDF
            pdf_converter = PDFConverter()
            pdf_saved = pdf_converter.create_ticket_pdf(
                ticket_data,
                os.path.join(ticket_dir, f"{ticket_key}.pdf")
            )
            
            # Process any links in the description
            if issue.fields.description:
                urls = re.findall(
                    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?",
                    issue.fields.description
                )
                for url in urls:
                    self.process_link(url, nested_links_dir, f"description_link_{urls.index(url)}")
            
            # Process any links in comments
            comments = self.jira.comments(issue)
            for comment in comments:
                if comment.body:
                    urls = re.findall(
                        r"https?://[^\s\]\|>]+",
                        comment.body
                    )
                    urls_set = set(urls)
                    for idx, url in enumerate(urls_set):
                        self.process_link(url, nested_links_dir, f"comment_{comment.id}_link_{idx}")
            
            return json_saved and pdf_saved
            
        except Exception as e:
            logger.error(f"Failed to process Jira link {url}: {str(e)}")
            link_info = {"url": url, "type": "jira", "error": str(e)}
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_jira_link.json",
                json.dumps(link_info, indent=4)
            )

    def process_generic_link(self, url, links_dir, prefix):
        """
        Process generic web links
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "").lower()
            
            if "text/html" in content_type:
                return FileUtils.save_file(
                    f"{links_dir}/{prefix}_webpage.html",
                    response.text,
                    encoding='utf-8'
                )
            elif "application/pdf" in content_type:
                return FileUtils.save_file(
                    f"{links_dir}/{prefix}_document.pdf",
                    response.content,
                    mode='wb'
                )
            else:
                return FileUtils.save_file(
                    f"{links_dir}/{prefix}_content.bin",
                    response.content,
                    mode='wb'
                )
        except Exception as e:
            logger.error(f"Failed to process generic link {url}: {str(e)}")
            link_info = {"url": url, "type": "generic", "error": str(e)}
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_link.json",
                json.dumps(link_info, indent=4)
            ) 