import os
import json
import re
from ..config.logger import logger
from ..utils.file_utils import FileUtils
from ..utils.link_handlers import LinkHandler
from .converter import PDFConverter

class TicketProcessor:
    def __init__(self, jira_client, session):
        """
        Initialize ticket processor
        
        Args:
            jira_client: Authenticated Jira client
            session: Authenticated requests session
        """
        self.jira = jira_client
        self.link_handler = LinkHandler(session)
        self.pdf_converter = PDFConverter()
        self.output_dir = "jira_tickets"

    def process_ticket(self, issue):
        """
        Process a single Jira ticket
        
        Args:
            issue: Jira issue object
            
        Returns:
            bool: True if processing was successful
        """
        try:
            ticket_key = issue.key
            logger.info(f"Processing ticket: {ticket_key}")
            
            # Create ticket directory
            ticket_dir = os.path.join(self.output_dir, ticket_key)
            if not FileUtils.ensure_directory(ticket_dir):
                return False
            
            # Extract and save basic ticket information
            if not self._save_ticket_info(issue, ticket_dir):
                return False
            
            # Create ticket PDF
            if not self._create_ticket_pdf(issue, ticket_dir):
                return False
            
            # Extract attachments
            if not self._extract_attachments(issue, ticket_dir):
                return False
            
            # Extract comments
            if not self._extract_comments(issue, ticket_dir):
                return False
            
            # Extract links
            if not self._extract_links(issue, ticket_dir):
                return False
            
            logger.info(f"Successfully processed ticket: {ticket_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process ticket {issue.key}: {str(e)}")
            return False

    def _save_ticket_info(self, issue, ticket_dir):
        """Save basic ticket information as JSON"""
        try:
            ticket_info = {
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
            
            return FileUtils.save_file(
                os.path.join(ticket_dir, f"{issue.key}_info.json"),
                json.dumps(ticket_info, indent=4)
            )
        except Exception as e:
            logger.error(f"Failed to save ticket info for {issue.key}: {str(e)}")
            return False

    def _create_ticket_pdf(self, issue, ticket_dir):
        """Create PDF version of the ticket"""
        try:
            ticket_info = {
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
            
            return self.pdf_converter.create_ticket_pdf(
                ticket_info,
                os.path.join(ticket_dir, f"{issue.key}.pdf")
            )
        except Exception as e:
            logger.error(f"Failed to create PDF for {issue.key}: {str(e)}")
            return False

    def _extract_attachments(self, issue, ticket_dir):
        """Extract attachments from the ticket"""
        try:
            attachments_dir = os.path.join(ticket_dir, "attachments")
            if not FileUtils.ensure_directory(attachments_dir):
                return False
            
            for attachment in issue.fields.attachment:
                try:
                    logger.info(f"Downloading attachment: {attachment.filename}")
                    attachment_data = attachment.get()
                    
                    if not FileUtils.save_file(
                        os.path.join(attachments_dir, attachment.filename),
                        attachment_data,
                        mode='wb'
                    ):
                        logger.warning(f"Failed to save attachment: {attachment.filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to download attachment {attachment.filename}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process attachments for {issue.key}: {str(e)}")
            return False

    def _extract_comments(self, issue, ticket_dir):
        """Extract comments from the ticket"""
        try:
            comments_dir = os.path.join(ticket_dir, "comments")
            if not FileUtils.ensure_directory(comments_dir):
                return False
            
            # Get all comments
            comments = self.jira.comments(issue)
            
            # Save comments as JSON
            comments_data = []
            for comment in comments:
                comment_info = {
                    "id": comment.id,
                    "author": getattr(comment.author, "displayName", "Unknown"),
                    "created": comment.created,
                    "updated": comment.updated,
                    "body": comment.body,
                    "visibility": getattr(comment.visibility, "value", "None") if hasattr(comment, "visibility") else "None"
                }
                comments_data.append(comment_info)
            
            # Save all comments in a single JSON file
            if not FileUtils.save_file(
                os.path.join(comments_dir, "comments.json"),
                json.dumps(comments_data, indent=4)
            ):
                logger.warning(f"Failed to save comments JSON for {issue.key}")
            
            # Save each comment as a separate text file
            for comment in comments_data:
                comment_text = f"""Comment ID: {comment['id']}
Author: {comment['author']}
Created: {comment['created']}
Updated: {comment['updated']}
Visibility: {comment['visibility']}

{comment['body']}
"""
                if not FileUtils.save_file(
                    os.path.join(comments_dir, f"comment_{comment['id']}.txt"),
                    comment_text
                ):
                    logger.warning(f"Failed to save comment {comment['id']} as text file")
            
            logger.info(f"Extracted {len(comments_data)} comments for ticket {issue.key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract comments for {issue.key}: {str(e)}")
            return False

    def _extract_links(self, issue, ticket_dir):
        """Extract links from description and comments"""
        try:
            links_dir = os.path.join(ticket_dir, "links")
            if not FileUtils.ensure_directory(links_dir):
                return False
            
            # Extract from description
            if issue.fields.description:
                urls = re.findall(
                    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?",
                    issue.fields.description
                )
                for url in urls:
                    self.link_handler.process_link(url, links_dir, f"description_link_{urls.index(url)}")
            
            # Extract from comments
            comments = self.jira.comments(issue)
            for comment in comments:
                if comment.body:
                    urls = re.findall(
                        r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?\S+)?",
                        comment.body
                    )
                    for url in urls:
                        self.link_handler.process_link(url, links_dir, f"comment_{comment.id}_link_{urls.index(url)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract links for {issue.key}: {str(e)}")
            return False 