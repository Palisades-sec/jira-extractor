# Jira Ticket Extractor

A Python script to extract Jira tickets and their attachments/links based on JQL queries.

## Prerequisites

- Python 3.x
- Virtual environment (recommended)
- Jira API token (can be generated from your Atlassian account)

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd jira_script
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:
   Create a `.env` file in the root directory with the following content:

```env
JIRA_URL=https://your-domain.atlassian.net/
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT
JIRA_JQL=project = "YOUR_PROJECT" AND created >= -30d
```

## Usage

The script can be run using the following command:

```bash
python -m main --jql "your-jql-query"
```

### Command Line Arguments

| Argument        | Required | Description                                  | Example                               |
| --------------- | -------- | -------------------------------------------- | ------------------------------------- |
| `--jql`         | Yes      | JQL query to select tickets                  | `"project = KAN AND created >= -30d"` |
| `--url`         | No       | Jira URL (defaults to .env value)            | `https://your-domain.atlassian.net`   |
| `--username`    | No       | Jira username/email (defaults to .env value) | `your-email@domain.com`               |
| `--api-token`   | No       | Jira API token (defaults to .env value)      | `your-api-token`                      |
| `--max-results` | No       | Maximum number of tickets to process         | `100`                                 |

### Examples

1. Basic usage with JQL query:

```bash
python -m main --jql "project = KAN AND created >= -30d"
```

2. Specify maximum results:

```bash
python -m main --jql "project = KAN AND created >= -30d" --max-results 50
```

3. Override environment variables:

```bash
python -m main --jql "project = KAN AND created >= -30d" --url "https://custom-domain.atlassian.net" --username "different@email.com" --api-token "your-token"
```

### Common JQL Query Examples

1. Tickets created in the last 30 days:

## Features

- Extract Jira tickets based on JQL queries
- Download ticket attachments
- Process linked content (Confluence, Google Docs, etc.)
- Generate PDF versions of tickets
- Parallel processing for better performance
- Comprehensive error handling and logging

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
