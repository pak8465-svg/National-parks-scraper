"""
National Parks Data Collector for Google Colab
Collects park data from NPS API and writes to Google Sheets
"""

# ============================================================================
# IMPORTS
# ============================================================================
import requests
import pandas as pd
import gspread
from google.colab import auth
from google.auth import default

# ============================================================================
# CONFIGURATION - PASTE YOUR VALUES HERE
# ============================================================================

# PASTE YOUR NPS API KEY HERE (get one from https://www.nps.gov/subjects/developer/get-started.htm)
API_KEY = "RnEZn4MzPJHMqocffj42YHtgzVm6uuGOyp49hLAZ"

# PASTE YOUR GOOGLE SHEET URL HERE (the full URL from your browser)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1QfsxIUok_5owSTJvI1_V5GNuzTsAOShHxktxh9w_jHA/edit?usp=sharing"

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def authenticate_google_sheets():
    """Authenticate with Google Sheets using Colab auth"""
    print("Authenticating with Google...")
    auth.authenticate_user()
    creds, _ = default()
    gc = gspread.authorize(creds)
    print("✓ Authentication successful")
    return gc

def fetch_parks_data(api_key, limit=50):
    """Fetch parks data from NPS API"""
    print(f"\nFetching parks data from NPS API (limit: {limit})...")

    url = "https://developer.nps.gov/api/v1/parks"
    params = {
        "api_key": api_key,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        print(f"✓ Successfully fetched data from NPS API")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching data: {e}")
        return None

def parse_parks_data(api_response):
    """Extract relevant fields from API response"""
    print("\nParsing park data...")

    if not api_response or 'data' not in api_response:
        print("✗ No data found in API response")
        return []

    parks_list = []

    for park in api_response['data']:
        park_data = {
            'Full Name': park.get('fullName', 'N/A'),
            'States': park.get('states', 'N/A'),
            'Description': park.get('description', 'N/A'),
            'Acres': park.get('acres', 'N/A'),
            'Designation': park.get('designation', 'N/A')
        }
        parks_list.append(park_data)

    print(f"✓ Parsed {len(parks_list)} parks")
    return parks_list

def write_to_google_sheet(gc, sheet_url, data):
    """Write data to Google Sheet"""
    print("\nWriting data to Google Sheet...")

    try:
        # Open the sheet
        sheet = gc.open_by_url(sheet_url)
        worksheet = sheet.sheet1  # Use the first worksheet

        # Clear existing data
        worksheet.clear()

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Write headers and data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

        print(f"✓ Successfully wrote {len(data)} parks to Google Sheet")
        print(f"✓ Sheet URL: {sheet_url}")

    except Exception as e:
        print(f"✗ Error writing to Google Sheet: {e}")
        print("Make sure you have shared the sheet with your Google account")

def main():
    """Main execution function"""
    print("=" * 60)
    print("National Parks Data Collector")
    print("=" * 60)

    # Validate configuration
    if API_KEY == "YOUR_API_KEY_HERE":
        print("✗ ERROR: Please paste your NPS API key in the API_KEY variable")
        return

    if SHEET_URL == "YOUR_GOOGLE_SHEET_URL_HERE":
        print("✗ ERROR: Please paste your Google Sheet URL in the SHEET_URL variable")
        return

    # Step 1: Authenticate with Google
    gc = authenticate_google_sheets()

    # Step 2: Fetch parks data from NPS API
    api_response = fetch_parks_data(API_KEY, limit=50)
    if not api_response:
        return

    # Step 3: Parse the data
    parks_data = parse_parks_data(api_response)
    if not parks_data:
        return

    # Step 4: Write to Google Sheet
    write_to_google_sheet(gc, SHEET_URL, parks_data)

    print("\n" + "=" * 60)
    print("✓ Process completed successfully!")
    print("=" * 60)

# ============================================================================
# RUN THE SCRIPT
# ============================================================================

if __name__ == "__main__":
    main()
