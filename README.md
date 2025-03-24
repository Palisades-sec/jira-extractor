# Jira Ticket Extractor

A Python tool to extract Jira tickets, including attachments and linked content, with proper error handling and parallel processing.

## Features

- Extract Jira tickets based on JQL queries
- Download ticket attachments
- Process linked content (Confluence, Google Docs, etc.)
- Generate PDF versions of tickets
- Parallel processing for better performance
- Comprehensive error handling and logging

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd jira-ticket-extractor
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Jira credentials:

```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_JQL="project = PROJ AND created >= -30d"
```

## Usage

Run the script with command line arguments:

```bash
python -m jira_extractor.main --url https://your-domain.atlassian.net --jql "project = PROJ"
```

Or use environment variables from `.env` file:

```bash
python -m jira_extractor.main
```

### Command Line Arguments

- `--url`: Jira URL (e.g., https://your-domain.atlassian.net)
- `--username`: Jira username (email)
- `--api-token`: Jira API token
- `--jql`: JQL query to select tickets
- `--max-results`: Maximum number of tickets to process (default: 50)

## Output

The script creates a `jira_tickets` directory with the following structure for each ticket:

```
jira_tickets/
└── TICKET-123/
    ├── TICKET-123_info.json    # Ticket information
    ├── TICKET-123.pdf          # PDF version of the ticket
    ├── attachments/            # Ticket attachments
    └── links/                  # Processed linked content
```

## Error Handling

- All operations include proper error handling
- Failed operations are logged with detailed error messages
- The script continues processing other tickets if one fails
- A summary of failed operations is provided at the end

## Logging

- Detailed logs are written to console
- Includes information about:
  - Ticket processing status
  - Download progress
  - Error messages
  - Operation completion status

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
