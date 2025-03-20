# Jira Ticket Extractor

A Python-based tool for extracting Jira tickets and their attachments, with support for parallel processing and multiple output formats (JSON, PDF).

## Features

- Extract Jira tickets using JQL queries
- Parallel processing of tickets in batches
- Export ticket information to JSON and PDF formats
- Download ticket attachments
- Extract and process links from ticket descriptions and comments
- Support for different link types (Confluence, Google Docs, generic web links)
- Intelligent link content extraction with proper naming

## Prerequisites

- Python 3.12 or higher
- Jira account with API access
- Required Python packages (installed via pyproject.toml):
  - jira==3.8.0
  - requests==2.28.1
  - html2text
  - PyPDF2
  - reportlab
  - python-dotenv==1.0.1
  - pydantic==2.4.2
  - pydantic-settings==2.0.2

## Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd jira-script
   ```

2. Create a `.env` file in the project root with your Jira credentials:
   ```env
   JIRA_URL=https://your-domain.atlassian.net/
   JIRA_USERNAME=your.email@domain.com
   JIRA_API_TOKEN=your-jira-api-token
   JIRA_PROJECT_KEY=YOUR-PROJECT
   JIRA_JQL=project = "YOUR-PROJECT" AND created >= -30d
   ```

## Usage

The script can be run directly using Python:

```bash
python jira_extractor_script.py
```

The script will automatically read configuration from your .env file. You can also override settings using command line arguments:

```bash
python jira_extractor_script.py --url "YOUR_JIRA_URL" --username "YOUR_USERNAME" --api-token "YOUR_API_TOKEN" --jql "YOUR_JQL_QUERY"
```

## Command Line Arguments

- `--url`: Jira instance URL
- `--username`: Jira username (email)
- `--api-token`: Jira API token
- `--jql`: JQL query to select tickets
- `--max-results`: Maximum number of tickets to process per batch (default: 50)

## Output Structure

```
jira_tickets/
├── TICKET-123/
│   ├── TICKET-123_info.json    # Ticket metadata
│   ├── TICKET-123.pdf         # PDF version of ticket
│   ├── attachments/           # Ticket attachments
│   │   └── attachment_files
│   └── links/                 # Extracted links
│       ├── Project_Requirements.html      # Confluence page with actual title
│       ├── Project_Requirements.txt
│       ├── Project_Requirements.pdf
│       ├── google_doc_Specification.json  # Google doc link info
│       └── generic_webpage.html          # Generic web links
```

## Link Processing

The script processes different types of links found in tickets:

### Confluence Pages

- Files are named using the actual page title from Confluence
- Example: A page titled "Project Requirements" creates:
  - `Project_Requirements.html`
  - `Project_Requirements.txt`
  - `Project_Requirements.pdf`

### Google Docs

- Stored as JSON files with link information
- Files named with document title when available
- Example: `google_doc_DocumentName.json`

### Generic Web Links

- Named based on content type and URL components
- HTML pages saved with appropriate extensions
- PDFs and other files maintain their format
- Example: `webpage_title.html`, `document.pdf`

## Performance Features

- Parallel processing using ThreadPoolExecutor
- Configurable batch size (default: min(max_results, 100))
- Maximum 5 concurrent batch processes
- Progress tracking and logging
- Efficient handling of large ticket volumes

## Error Handling

- Comprehensive error logging
- Graceful handling of failed tickets/batches
- Continues processing despite individual ticket failures
- Detailed error information in logs

## Development

### Project Structure

```
.
├── jira_extractor_script.py  # Main script
├── .env                      # Configuration file
├── pyproject.toml           # Python dependencies
└── README.md                # Documentation
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

## Limitations

- Google Docs integration requires additional setup (not implemented)
- PDF conversion limited to text content
- Maximum 5 concurrent batch processes to avoid API rate limits
- Certain file types may not be properly processed in attachments

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, please:

1. Check existing documentation
2. Review closed issues
3. Open a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
