#Get the Lighthouse scores for all pages monitored across all sites
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

def log_api_response(response_data, website_name):
    """
    Logs the API response to a JSON file.
    """
    log_file = f'logs/pages_response_{website_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(log_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    print(f"\nAPI response logged to: {log_file}")

def write_pages_to_csv(pages, website_name):
    """
    Writes the page data, including the specified Lighthouse scores (if available), to a CSV file.
    """
    csv_path = Path(CSV_DIR) / f'{website_name}_pages.csv'
    csv_path.parent.mkdir(exist_ok=True)  # Create the csv directory if it doesn't exist

    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Page ID', 'Alias', 'URL', 'Device', 'Performance Score', 'Accessibility Score', 'Best Practices Score', 'SEO Score']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for page in pages:
            row = {
                'Page ID': page['id'],
                'Alias': page['alias'],
                'URL': page['url'],
                'Device': page['device']
            }

            if 'latest' in page and 'performance_score' in page['latest']:
                row['Performance Score'] = page['latest']['performance_score']
            else:
                row['Performance Score'] = 'N/A'

            if 'latest' in page and 'accessibility_score' in page['latest']:
                row['Accessibility Score'] = page['latest']['accessibility_score']
            else:
                row['Accessibility Score'] = 'N/A'

            if 'latest' in page and 'best_practices_score' in page['latest']:
                row['Best Practices Score'] = page['latest']['best_practices_score']
            else:
                row['Best Practices Score'] = 'N/A'

            if 'latest' in page and 'seo_score' in page['latest']:
                row['SEO Score'] = page['latest']['seo_score']
            else:
                row['SEO Score'] = 'N/A'

            writer.writerow(row)
    
    print(f"Page data written to CSV: {csv_path}")

def get_pages(website_id, website_name):
    """
    Fetches the list of pages for a specific website, including the specified Lighthouse scores.
    """
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
                print(f"Page ID: {page['id']}, Alias: {page['alias']}, URL: {page['url']}, Device: {page['device']}, Performance Score: {page['latest']['performance_score']}, Accessibility Score: {page['latest']['accessibility_score']}, Best Practices Score: {page['latest']['best_practices_score']}, SEO Score: {page['latest']['seo_score']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        exit(1)

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
            get_pages(website_id, website_name)