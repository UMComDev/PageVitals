import requests
import os
from dotenv import load_dotenv
import csv
from datetime import datetime

# Load environment variables
load_dotenv()

# API configuration
api_key = os.getenv('PAGEVITALS_API_KEY')
base_url = 'https://api.pagevitals.com'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Website IDs
websites = {}
for env_var in os.environ:
    if env_var.startswith('PAGEVITALS_WEBSITE_'):
        site_name = env_var.replace('PAGEVITALS_WEBSITE_', '')
        websites[site_name] = os.getenv(env_var)

if not websites:
    raise ValueError("No website IDs found in environment variables. "
                    "Please ensure variables are set with prefix 'PAGEVITALS_WEBSITE_'")

# Collect page data
all_pages = []
for site_name, site_id in websites.items():
    response = requests.get(
        f'{base_url}/v1/websites/{site_id}/pages',
        headers=headers
    )
    
    if response.status_code == 200:
        pages = response.json()['result']['list']
        for page in pages:
            all_pages.append({
                'website': site_name,
                'url': page['url']
            })
        print(f"Successfully retrieved {len(pages)} pages for {site_name}")
    else:
        print(f"Error fetching {site_name}: {response.status_code} - {response.text}")

# Only create CSV if we have data
if all_pages:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'pages_list_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['website', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for page in all_pages:
            writer.writerow(page)
    print(f"\nPage list has been saved to {csv_filename}")
else:
    print("\nNo data was successfully retrieved. CSV file was not created.")