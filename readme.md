# PageVitals API Client

A Python client for interacting with the PageVitals API to collect website performance metrics.

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API key
4. Run `python get-websites.py` to initialize your website configurations

## Available Scripts

- `get-websites.py`: Fetches all websites and stores their IDs in `.env`
- `get-pages.py`: Retrieves all pages for configured websites and exports to CSV
- `get-lighthouse-scores.py`: Collects Lighthouse performance metrics and exports to CSV

## Environment Variables

The application uses the following environment variables:

- `PAGEVITALS_API_KEY`: Your PageVitals API key (recommended to use a "viewer" API key to prevent destructive changes)
- `PAGEVITALS_WEBSITE_[NAME]`: Website IDs (automatically populated by get-websites.py)

## File Outputs

### Pages List CSV
- Generated by `get-pages.py`
- Format: `pages_list_YYYYMMDD_HHMMSS.csv`
- Contains: website name and URL for each page

### Lighthouse Scores CSV
- Generated by `get-lighthouse-scores.py`
- Format: `lighthouse_scores_YYYYMMDD_HHMMSS.csv`
- Contains: Performance, Accessibility, Best Practices, and SEO scores

## Security Notes

- The `.env` file is automatically configured with secure file permissions (600)
- API keys are never logged or exposed in output files
- All sensitive files are included in `.gitignore`

## Error Handling

- Scripts will validate API key format before making requests
- Clear error messages are provided for common issues
- CSV files are only created when data is successfully retrieved