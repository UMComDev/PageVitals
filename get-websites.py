import requests
import os
import stat
from pathlib import Path
import re
from dotenv import load_dotenv
import secrets
import json
from datetime import datetime, timedelta
import time

# Constants
API_BASE_URL = 'https://api.pagevitals.com'
ENV_FILE_PATH = '.env'
LOG_DIR_PATH = 'logs'
LOG_FILE_PREFIX = 'websites_response_'
RETRY_AFTER_DEFAULT = 10
MAX_API_CALLS = 50
TIME_WINDOW_SECONDS = 10

def secure_file_permissions(filepath):
    """Set secure file permissions for the .env file"""
    os.chmod(filepath, stat.S_IRUSR)
    if os.name == 'posix' and os.stat(filepath).st_uid != os.getuid():
        raise PermissionError("File ownership mismatch")

def update_env_file(websites=None):
    """Safely update .env file with individual website IDs"""
    env_path = Path(ENV_FILE_PATH)
    temp_path = Path(f'{ENV_FILE_PATH}.{secrets.token_hex(16)}.tmp')
    
    with open(temp_path, 'w') as f:
        if websites:
            for website in websites:
                site_name = re.sub(r'[^a-zA-Z0-9]', '', website['displayName'].upper())
                f.write(f'PAGEVITALS_WEBSITE_{site_name}={website["id"]}\n')
    
    secure_file_permissions(temp_path)
    temp_path.replace(env_path)
    temp_path.unlink(missing_ok=True)  # Safely unlink the temp file

def log_api_response(response_data):
    """Log API response to a timestamped file in a logs directory"""
    log_dir = Path(LOG_DIR_PATH)
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f'{LOG_FILE_PREFIX}{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(log_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    
    print(f"\nAPI response logged to: {log_file}")

class RateLimiter:
    """Simple rate limiter to respect API limits of 50 calls per 10 seconds"""
    def __init__(self, max_calls=50, time_window=10):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def wait_if_needed(self):
        """Check if we need to wait before making another API call"""
        now = datetime.now()
        self.calls = [call_time for call_time in self.calls if now - call_time < timedelta(seconds=self.time_window)]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = (min(self.calls) + timedelta(seconds=self.time_window) - now).total_seconds()
            if sleep_time > 0:
                print(f"\nRate limit approached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        
        self.calls.append(now)

# Check if .env exists and create it if it doesn't
if not Path(ENV_FILE_PATH).exists():
    print(f"No {ENV_FILE_PATH} file found. Creating one...")
    exit(1)

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

# Create rate limiter instance
rate_limiter = RateLimiter(max_calls=MAX_API_CALLS, time_window=TIME_WINDOW_SECONDS)

# Get list of websites
full_url = f'{API_BASE_URL}/websites'
print(f"\nMaking API call to: {full_url}")

# Check rate limit before making the call
rate_limiter.wait_if_needed()

try:
    response = requests.get(full_url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', RETRY_AFTER_DEFAULT))
        print(f"\nRate limit exceeded. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        rate_limiter.wait_if_needed()
        response = requests.get(full_url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        websites = response_data['result']['list']
        log_api_response(response_data)
        
        print("\nFound websites:")
        for website in websites:
            print("\nWebsite Details:")
            for key, value in website.items():
                display_key = ' '.join(word.capitalize() for word in re.findall(r'[A-Z]*[a-z0-9]+', key))
                print(f"{display_key}: {value}")
            print("-" * 50)
        
        update_env_file(websites)
        print("\nWebsite IDs have been saved to .env file")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    exit(1)