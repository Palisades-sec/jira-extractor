import requests
from urllib.parse import urlparse
import json
from ..config.logger import logger
from .file_utils import FileUtils

class LinkHandler:
    def __init__(self, session):
        """
        Initialize link handler
        
        Args:
            session (requests.Session): Authenticated session for requests
        """
        self.session = session

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
            
            # Handle different types of links
            if "docs.google.com" in domain or "drive.google.com" in domain:
                return self.process_google_link(url, links_dir, prefix)
            elif "wiki" in domain:
                return self.process_confluence_link(url, links_dir, prefix)
            else:
                return self.process_generic_link(url, links_dir, prefix)
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
        Process Confluence links
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Save the HTML content
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_confluence.html",
                response.text,
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Failed to process Confluence link {url}: {str(e)}")
            link_info = {"url": url, "type": "confluence", "error": str(e)}
            return FileUtils.save_file(
                f"{links_dir}/{prefix}_confluence_link.json",
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