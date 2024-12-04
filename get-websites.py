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

def create_env_example():
    """Create .env.example template file"""
    example_path = '.env.example'
    if not os.path.exists(example_path):
        with open(example_path, 'w') as f:
            f.write('PAGEVITALS_API_KEY=your_api_key_here')

def secure_file_permissions(filepath):
    """Set secure file permissions for the .env file"""
    os.chmod(filepath, stat.S_IRUSR)
    
    if os.name == 'posix':
        current_uid = os.getuid()
        file_stat = os.stat(filepath)
        if file_stat.st_uid != current_uid:
            raise PermissionError("File ownership mismatch")

def validate_api_key(key):
    """Basic validation of API key format"""
    if not key or not re.match(r'^[A-Za-z0-9_-]{32,256}$', key):
        raise ValueError("Invalid API key format")
    return key

def update_env_file(key, websites=None):
    """Safely update .env file with API key and individual website IDs"""
    env_path = Path('.env')
    temp_path = Path(f'.env.{secrets.token_hex(16)}.tmp')
    
    try:
        # Write to temporary file first
        with open(temp_path, 'w') as f:
            f.write(f'PAGEVITALS_API_KEY={key}\n')
            if websites:
                for website in websites:
                    # Convert displayName to uppercase, remove non-alphanumeric chars
                    site_name = re.sub(r'[^a-zA-Z0-9]', '', website['displayName'].upper())
                    f.write(f'PAGEVITALS_WEBSITE_{site_name}={website["id"]}\n')
        
        # Ensure temp file has secure permissions before writing
        secure_file_permissions(temp_path)
        
        # Atomic replacement of .env file
        temp_path.replace(env_path)
        
    finally:
        if temp_path.exists():
            temp_path.unlink()

def log_api_response(response_data):
    """Log API response to a timestamped file in a logs directory"""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'websites_response_{timestamp}.json'
    
    # Write response data to file with pretty printing
    with open(log_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    
    print(f"\nAPI response logged to: {log_file}")

class RateLimiter:
    """Simple rate limiter to respect API limits of 50 calls per 10 seconds"""
    def __init__(self, max_calls=50, time_window=10):
        self.max_calls = max_calls
        self.time_window = time_window  # in seconds
        self.calls = []

    def wait_if_needed(self):
        """Check if we need to wait before making another API call"""
        now = datetime.now()
        
        # Remove calls older than our time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        
        # If we've hit our limit, wait until enough time has passed
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            sleep_time = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
            if sleep_time > 0:
                print(f"\nRate limit approached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        
        # Record this call
        self.calls.append(now)

# Create .env.example template
create_env_example()

# Check if .env exists and create it if it doesn't
env_path = '.env'
if not os.path.exists(env_path):
    print("No .env file found. Creating one...")
    print("Please add your PageVitals API key to the .env file")
    print("See .env.example for the required format")
    exit(1)

# Load environment variables
load_dotenv()

# Check if API key exists
api_key = os.getenv('PAGEVITALS_API_KEY')
if not api_key:
    print("PAGEVITALS_API_KEY not found in .env file")
    print("Please enter your PageVitals API key")
    print("Warning: API keys should be handled securely and never shared")
    new_key = input("API Key: ").strip()
    
    try:
        # Validate key format
        validated_key = validate_api_key(new_key)
        # Update .env file
        update_env_file(validated_key)
        print(".env file updated with new API key")
        api_key = validated_key
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error updating .env file: {e}")
        exit(1)

# API configuration
base_url = 'https://api.pagevitals.com'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'User-Agent': 'PageVitals-API-Client/1.0'
}

# Create rate limiter instance
rate_limiter = RateLimiter()

# Get list of websites
full_url = f'{base_url}/websites'
print(f"\nMaking API call to: {full_url}")

# Check rate limit before making the call
rate_limiter.wait_if_needed()

try:
    response = requests.get(full_url, headers=headers)
    
    # Handle rate limit response
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 10))
        print(f"\nRate limit exceeded. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        # Retry the request
        rate_limiter.wait_if_needed()
        response = requests.get(full_url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        websites = response_data['result']['list']
        
        # Log the full API response
        log_api_response(response_data)
        
        print("\nFound websites:")
        for website in websites:
            print(f"\nWebsite Details:")
            for key, value in website.items():
                display_key = ' '.join(word.capitalize() for word in re.findall(r'[A-Z]*[a-z0-9]+', key))
                print(f"{display_key}: {value}")
            print("-" * 50)
        
        # Update .env file with individual website IDs
        update_env_file(api_key, websites)
        print("\nWebsite IDs have been saved to .env file")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    exit(1)
