import os
import requests
from jira import JIRA
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config.logger import logger
from .processor import TicketProcessor
from pydantic import BaseModel

class JiraConfig(BaseModel):
    jira_url: str
    username: str
    api_token: str

class JiraTicketExtractor:
    def __init__(self, jira_url, username=None, api_token=None):
        """
        Initialize Jira client with authentication
        
        Args:
            jira_url (str): URL of the Jira instance
            username (str): Jira username
            api_token (str): Jira API token or password
        """
        try:
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
                    logger.info("Connected to Jira using environment credentials")
                else:
                    raise ValueError(
                        "No credentials provided. Use parameters or set JIRA_USERNAME and JIRA_API_TOKEN environment variables"
                    )
            
            # Initialize session for requests
            self.session = requests.Session()
            self.session.auth = (username, api_token)

            self.jira_config = JiraConfig(
                jira_url=jira_url,
                username=username,
                api_token=api_token
            )
            
            # Initialize ticket processor
            # self.processor = TicketProcessor(self.jira, self.session, project_key = None, jira_config = self.jira_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize Jira extractor: {str(e)}")
            raise

    def extract_tickets(self, jql_query, max_results=50):
        """
        Extract tickets based on JQL query using parallel processing
        
        Args:
            jql_query (str): JQL query to find tickets
            max_results (int): Maximum number of tickets to retrieve per batch
            
        Returns:
            bool: True if extraction was successful
        """
        try:
            logger.info(f"Extracting tickets using query: {jql_query}")
            
            # Create output directory if it doesn't exist
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            # Get total number of issues
            total_issues = self.jira.search_issues(jql_query, maxResults=0).total
            logger.info(f"Found total of {total_issues} tickets")
            
            if total_issues == 0:
                logger.info("No tickets found matching the query")
                return True
            
            # Calculate number of batches needed
            batch_size = min(max_results, 100)  # Limit batch size to 100
            num_batches = math.ceil(total_issues / batch_size)
            
            # Process tickets in parallel
            with ThreadPoolExecutor(max_workers=min(num_batches, 5)) as executor:
                future_to_batch = {}
                
                # Submit batch processing tasks
                for batch_num in range(num_batches):
                    start_at = batch_num * batch_size
                    future = executor.submit(
                        self._process_batch,
                        jql_query,
                        start_at,
                        batch_size
                    )
                    future_to_batch[future] = batch_num
                
                # Process completed batches
                failed_batches = []
                for future in as_completed(future_to_batch):
                    batch_num = future_to_batch[future]
                    try:
                        success, processed = future.result()
                        if success:
                            logger.info(
                                f"Completed batch {batch_num + 1}/{num_batches} "
                                f"(processed {processed} tickets)"
                            )
                        else:
                            failed_batches.append(batch_num + 1)
                    except Exception as e:
                        logger.error(f"Batch {batch_num + 1} failed: {str(e)}")
                        failed_batches.append(batch_num + 1)
            
            if failed_batches:
                logger.warning(f"Failed batches: {failed_batches}")
                return False
            
            logger.info(f"Completed processing all {total_issues} tickets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract tickets: {str(e)}")
            return False

    def _process_batch(self, jql_query, start_at, batch_size):
        """
        Process a batch of tickets
        
        Args:
            jql_query (str): JQL query
            start_at (int): Starting index
            batch_size (int): Number of tickets to process in this batch
            
        Returns:
            tuple: (success: bool, processed: int)
        """
        try:
            issues = self.jira.search_issues(
                jql_query,
                startAt=start_at,
                maxResults=batch_size
            )
            # get the project key from the first issue
            project_key = issues[0].fields.project.key
            logger.info(f"Project key: {project_key}")

            processor_v2 = TicketProcessor(self.jira, self.session, project_key, self.jira_config)
            processed = 0
            for issue in issues:
                try:
                    if processor_v2.process_ticket(issue):
                        processed += 1
                except Exception as e:
                    logger.error(f"Failed to process ticket {issue.key}: {str(e)}")
            
            return True, processed
            
        except Exception as e:
            logger.error(f"Failed to process batch starting at {start_at}: {str(e)}")
            return False, 0 