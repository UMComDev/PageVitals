import requests
import os
import stat
from pathlib import Path
import re
from dotenv import load_dotenv
import secrets

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

# Get list of websites
full_url = f'{base_url}/websites'
print(f"\nMaking API call to: {full_url}")
response = requests.get(full_url, headers=headers)

if response.status_code == 200:
    websites = response.json()['result']['list']
    
    print("\nFound websites:")
    for website in websites:
        print(f"\nWebsite Details:")
        # Loop through all keys in the website dictionary
        for key, value in website.items():
            # Format the key name for display (convert camelCase to Title Case)
            display_key = ' '.join(word.capitalize() for word in re.findall(r'[A-Z]*[a-z0-9]+', key))
            print(f"{display_key}: {value}")
        print("-" * 50)
    
    # Update .env file with individual website IDs
    update_env_file(api_key, websites)
    print("\nWebsite IDs have been saved to .env file")
else:
    print(f"Error: {response.status_code} - {response.text}")
