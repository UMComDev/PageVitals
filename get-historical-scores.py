import requests
import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

# Constants
API_BASE_URL = 'https://api.pagevitals.com'
ENV_FILE_PATH = '.env'
RETRY_AFTER_DEFAULT = 10
MAX_API_CALLS = 50
TIME_WINDOW_SECONDS = 10
CSV_DIR = 'csv'
HISTORY_DAYS = 90  # Number of days to fetch historical Lighthouse scores

# Load environment variables
load_dotenv()

# Check if API key exists
api_key = os.getenv('PAGEVITALS_API_KEY')
if not api_key:
    print("PAGEVITALS_API_KEY not found in .env file")
    exit(1)

# API configuration
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'User-Agent': 'PageVitals-API-Client/1.0'
}

def log_api_response(response_data, website_name):
    """
    Logs the API response to a JSON file.
    """
    log_dir = 'logs'
    Path(log_dir).mkdir(exist_ok=True)  # Create the logs directory if it doesn't exist
    log_file = f'{log_dir}/pages_response_{website_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(log_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    print(f"\nAPI response logged to: {log_file}")

def get_historical_scores(website_id, page_id, start_date, end_date, device):
    """
    Fetches the historical scores for a given page, date range, and device.
    """
    scores = []
    full_url = f"{API_BASE_URL}/{website_id}/pages/{page_id}/timeline?startDate={start_date}&endDate={end_date}&device={device}"
    print(f"\nMaking API call to: {full_url}")

    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', RETRY_AFTER_DEFAULT))
            print(f"\nRate limit exceeded. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            response = requests.get(full_url, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            scores = response_data['result']
            print(f"API response received.")
        else:
            print(f"Error fetching scores for page {page_id}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    return scores

def write_pages_to_csv(pages, website_name, website_id):
    """
    Writes the page data, including historical scores, to a CSV file.
    """
    csv_path = Path(CSV_DIR) / f'{website_name}_pages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    csv_path.parent.mkdir(exist_ok=True)  # Create the csv directory if it doesn't exist

    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Page ID', 'Alias', 'URL', 'Device', 'Date', 'LCP', 'FCP', 'Speed Index', 'TBT', 'CLS', 'TTFB', 'TTI', 'DOM Elements', 'DOM Max Depth', 'DOM Ready', 'On Load', 'DNS Time', 'Connect Time', 'Server Time', 'Transfer Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for page in pages:
            page_id = page['id']
            start_date = (datetime.now() - timedelta(days=HISTORY_DAYS)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            historical_scores = get_historical_scores(website_id, page_id, start_date, end_date, page['device'])

            for score in historical_scores:
                row = {
                    'Page ID': page['id'],
                    'Alias': page['alias'],
                    'URL': page['url'],
                    'Device': page['device'],
                    'Date': score['date'],
                    'LCP': score.get('lcp', 'N/A'),
                    'FCP': score.get('fcp', 'N/A'),
                    'Speed Index': score.get('speed_index', 'N/A'),
                    'TBT': score.get('tbt', 'N/A'),
                    'CLS': score.get('cls', 'N/A'),
                    'TTFB': score.get('ttfb', 'N/A'),
                    'TTI': score.get('tti', 'N/A'),
                    'DOM Elements': score.get('dom_elements', 'N/A'),
                    'DOM Max Depth': score.get('dom_max_depth', 'N/A'),
                    'DOM Ready': score.get('dom_ready', 'N/A'),
                    'On Load': score.get('on_load', 'N/A'),
                    'DNS Time': score.get('dns_time', 'N/A'),
                    'Connect Time': score.get('connect_time', 'N/A'),
                    'Server Time': score.get('server_time', 'N/A'),
                    'Transfer Time': score.get('transfer_time', 'N/A')
                }
                writer.writerow(row)

    print(f"Page data written to CSV: {csv_path}")

if __name__ == "__main__":
    """
    Main execution of the script.
    """
    # Loop through all environment variables that start with PAGEVITALS_WEBSITE_
    for key, value in os.environ.items():
        if key.startswith('PAGEVITALS_WEBSITE_'):
            website_name = key.split('PAGEVITALS_WEBSITE_')[1]
            website_id = value
            print(f"Fetching pages for website: {website_name} (ID: {website_id})")
            pages_url = f"{API_BASE_URL}/{website_id}/pages"
            pages_response = requests.get(pages_url, headers=headers)
            
            if pages_response.status_code == 200:
                pages_data = pages_response.json()
                pages = pages_data['result']['list']
                log_api_response(pages_data, website_name)
                write_pages_to_csv(pages, website_name, website_id)
            else:
                print(f"Error fetching pages for website {website_name}: {pages_response.status_code} - {pages_response.text}")