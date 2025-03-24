from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfWriter, PdfReader
import html2text
from ..config.logger import logger

class PDFConverter:
    def __init__(self):
        """Initialize PDF converter with HTML to text converter"""
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False

    def html_to_pdf(self, html_content, output_path):
        """
        Convert HTML content to PDF
        
        Args:
            html_content (str): HTML content to convert
            output_path (str): Path to save the PDF
            
        Returns:
            bool: True if conversion was successful
        """
        try:
            # Extract text from HTML
            text_content = self.h2t.handle(html_content)
            
            # Create PDF
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 10)
            
            # Add text to PDF
            y_position = 750
            for line in text_content.split("\n")[:100]:  # Limit to first 100 lines
                if line.strip():
                    # Truncate line if too long
                    truncated_line = line[:100] if len(line) > 100 else line
                    can.drawString(72, y_position, truncated_line)
                    y_position -= 15
                    if y_position < 72:  # Stop if we reach bottom of page
                        break
            
            can.save()
            packet.seek(0)
            
            # Create final PDF
            new_pdf = PdfWriter()
            pdf_reader = PdfReader(packet)
            new_pdf.add_page(pdf_reader.pages[0])
            
            # Save PDF
            with open(output_path, "wb") as f:
                new_pdf.write(f)
            
            logger.info(f"Successfully converted HTML to PDF at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {str(e)}")
            return False

    def create_ticket_pdf(self, ticket_data, output_path):
        """
        Create a PDF document from ticket data
        
        Args:
            ticket_data (dict): Dictionary containing ticket information
            output_path (str): Path to save the PDF
            
        Returns:
            bool: True if PDF creation was successful
        """
        try:
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Set title
            can.setFont("Helvetica-Bold", 16)
            can.drawString(72, 750, f"Jira Ticket: {ticket_data['key']}")
            
            # Add ticket information
            y_position = 720
            field_font_size = 12
            
            fields = [
                ("Summary", ticket_data.get('summary', 'N/A')),
                ("Status", ticket_data.get('status', 'N/A')),
                ("Issue Type", ticket_data.get('issueType', 'N/A')),
                ("Created", ticket_data.get('created', 'N/A')),
                ("Updated", ticket_data.get('updated', 'N/A')),
                ("Assignee", ticket_data.get('assignee', 'N/A')),
                ("Reporter", ticket_data.get('reporter', 'N/A'))
            ]
            
            for field_name, field_value in fields:
                # Draw field name
                can.setFont("Helvetica-Bold", field_font_size)
                can.drawString(72, y_position, f"{field_name}:")
                
                # Draw field value
                can.setFont("Helvetica", field_font_size)
                value_text = str(field_value)[:80]  # Truncate if too long
                can.drawString(200, y_position, value_text)
                
                y_position -= 20
            
            # Add description if available
            if 'description' in ticket_data and ticket_data['description']:
                can.setFont("Helvetica-Bold", field_font_size)
                can.drawString(72, y_position - 20, "Description:")
                
                can.setFont("Helvetica", 10)
                description = str(ticket_data['description'])
                y_position -= 40
                
                # Add description text with word wrap
                for line in description.split('\n')[:20]:  # Limit to 20 lines
                    if line.strip():
                        truncated_line = line[:100] if len(line) > 100 else line
                        can.drawString(72, y_position, truncated_line)
                        y_position -= 15
                        if y_position < 72:
                            break
            
            can.save()
            packet.seek(0)
            
            # Create final PDF
            new_pdf = PdfWriter()
            pdf_reader = PdfReader(packet)
            new_pdf.add_page(pdf_reader.pages[0])
            
            # Save PDF
            with open(output_path, "wb") as f:
                new_pdf.write(f)
            
            logger.info(f"Successfully created ticket PDF at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ticket PDF: {str(e)}")
            return False 