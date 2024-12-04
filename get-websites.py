import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
api_key = os.getenv('PAGEVITALS_API_KEY')
base_url = 'https://api.pagevitals.com'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Get list of websites
response = requests.get(f'{base_url}/websites', headers=headers)

if response.status_code == 200:
    websites = response.json()['result']['list']
    print("\nYour websites:")
    print("-" * 50)
    for website in websites:
        print(f"Website ID: {website.get('id', 'N/A')}")
        print(f"Domain: {website.get('domain', 'N/A')}")
        print("-" * 50)
else:
    print(f"Error: {response.status_code} - {response.text}")
