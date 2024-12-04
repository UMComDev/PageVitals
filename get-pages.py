import requests
import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

# Constants
API_BASE_URL = 'https://api.pagevitals.com'
ENV_FILE_PATH = '.env'
RETRY_AFTER_DEFAULT = 10
MAX_API_CALLS = 50
TIME_WINDOW_SECONDS = 10
CSV_DIR = 'csv'

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

# Function to log API response
def log_api_response(response_data, website_name):
    log_file = f'logs/pages_response_{website_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(log_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    print(f"\nAPI response logged to: {log_file}")

# Function to write pages to CSV
def write_pages_to_csv(pages, website_name):
    csv_path = Path(CSV_DIR) / f'{website_name}_pages.csv'
    csv_path.parent.mkdir(exist_ok=True)  # Create the csv directory if it doesn't exist

    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Page ID', 'Alias', 'URL', 'Device']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for page in pages:
            writer.writerow({
                'Page ID': page['id'],
                'Alias': page['alias'],
                'URL': page['url'],
                'Device': page['device']
            })
    
    print(f"Page data written to CSV: {csv_path}")

# Get list of pages for a specific website
def get_pages(website_id, website_name):
    full_url = f'{API_BASE_URL}/{website_id}/pages'
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
            log_api_response(response_data, website_name)
            write_pages_to_csv(response_data['result']['list'], website_name)

            print(f"\nFound pages for {website_name}:")
            for page in response_data['result']['list']:
                print(f"Page ID: {page['id']}, Alias: {page['alias']}, URL: {page['url']}, Device: {page['device']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        exit(1)

# Main execution
if __name__ == "__main__":
    # Loop through all environment variables that start with PAGEVITALS_WEBSITE_
    for key, value in os.environ.items():
        if key.startswith('PAGEVITALS_WEBSITE_'):
            website_name = key.split('PAGEVITALS_WEBSITE_')[1]
            website_id = value
            print(f"Fetching pages for website: {website_name} (ID: {website_id})")
            get_pages(website_id, website_name)