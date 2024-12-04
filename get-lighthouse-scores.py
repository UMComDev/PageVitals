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
# Look for environment variables starting with PAGEVITALS_WEBSITE_
for env_var in os.environ:
    if env_var.startswith('PAGEVITALS_WEBSITE_'):
        # Extract site name from environment variable (everything after PAGEVITALS_WEBSITE_)
        site_name = env_var.replace('PAGEVITALS_WEBSITE_', '')
        websites[site_name] = os.getenv(env_var)

if not websites:
    raise ValueError("No website IDs found in environment variables. "
                    "Please ensure variables are set with prefix 'PAGEVITALS_WEBSITE_'")

# Collect data first
website_scores = []
for site_name, site_id in websites.items():
    response = requests.get(
        f'{base_url}/v1/websites/{site_id}/lighthouse/average',
        headers=headers
    )
    
    if response.status_code == 200:
        scores = response.json()['result']
        website_scores.append({
            'website': site_name,
            'performance': scores.get('performance', 'N/A'),
            'accessibility': scores.get('accessibility', 'N/A'),
            'best_practices': scores.get('bestPractices', 'N/A'),
            'seo': scores.get('seo', 'N/A')
        })
        print(f"Successfully retrieved scores for {site_name}")
    else:
        print(f"Error fetching {site_name}: {response.status_code} - {response.text}")

# Only create CSV if we have data
if website_scores:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'lighthouse_scores_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['website', 'performance', 'accessibility', 'best_practices', 'seo']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for score in website_scores:
            writer.writerow(score)
    print(f"\nScores have been saved to {csv_filename}")
else:
    print("\nNo data was successfully retrieved. CSV file was not created.") 