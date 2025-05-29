import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get and print the Google API key
google_api_key = os.getenv("GOOGLE_API_KEY")

if google_api_key:
    print("✅ GOOGLE_API_KEY loaded successfully:")
    print(google_api_key)
else:
    print("❌ GOOGLE_API_KEY not found. Check your .env file.")