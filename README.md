# National Parks Brochure Scraper

A Python script that scrapes park brochures from the U.S. National Parks Service website, extracts text and metadata from PDF files, and writes the results to Google Sheets.

## Features

- Scrapes up to 20 National Park brochures (configurable limit)
- Downloads PDF files from the NPS website
- Extracts text from PDF files using PyPDF2
- Parses key information:
  - Park name
  - State location
  - Established year
  - Size (acres/square miles)
- Writes results to Google Sheets
- Respects 10-second delay between requests (configurable)
- Comprehensive error handling
- Designed for Google Colab but works standalone

## Installation

### For Google Colab (Recommended)

1. Open the `scrape_park_brochures.ipynb` notebook in Google Colab
2. Run the first cell to install dependencies
3. Follow the authentication prompts
4. Run the main cell to execute the scraper

### For Local/Standalone Use

```bash
# Clone the repository
git clone https://github.com/pak8465-svg/National-parks-scraper.git
cd National-parks-scraper

# Install dependencies
pip install -r requirements.txt

# Run the script
python scrape_park_brochures.py
```

## Dependencies

- `requests` - HTTP library for downloading files
- `PyPDF2` - PDF text extraction
- `gspread` - Google Sheets API client
- `google-auth` - Google authentication

See `requirements.txt` for complete list.

## Usage

### Google Colab

The easiest way to run this script is in Google Colab:

1. Upload `scrape_park_brochures.ipynb` to Google Colab
2. Run the notebook cells in order
3. Authenticate with your Google account when prompted
4. Results will be written to the specified Google Sheet

### Standalone Python

```python
from scrape_park_brochures import NationalParksScraper

# Create scraper with 10-second delay
scraper = NationalParksScraper(delay_seconds=10)

# Scrape up to 20 parks
results = scraper.scrape_parks(limit=20)

# Save to JSON
scraper.save_results_json('parks_data.json')

# Write to Google Sheets (requires authentication)
scraper.write_to_google_sheets('YOUR_SPREADSHEET_URL')
```

## Configuration

You can modify these settings in the `main()` function:

```python
SPREADSHEET_URL = "your_google_sheets_url"  # Your Google Sheets URL
LIMIT = 20                                   # Number of parks to scrape
DELAY_SECONDS = 10                          # Delay between requests
```

## Google Sheets Setup

1. Create a Google Sheet or use an existing one
2. Get the shareable link
3. Update the `SPREADSHEET_URL` in the script
4. Ensure your Google account has edit access to the sheet

The script will create/update a worksheet named "Park Data" with the following columns:
- Park Name
- State
- Established Year
- Size
- Brochure URL
- Scraped Date

## Output

### Google Sheets
Results are written to the specified Google Sheet with headers and data.

### JSON Backup
A `parks_data.json` file is created as a backup with all scraped data.

## Error Handling

The script includes comprehensive error handling:
- Network errors during downloads
- PDF parsing errors
- Missing or invalid brochure URLs
- Google Sheets authentication issues

Errors are logged to console but don't stop the scraping process.

## Rate Limiting

The script respects a configurable delay (default: 10 seconds) between requests to avoid overloading the NPS servers.

## Supported Parks

The script includes 30 major U.S. National Parks:

- Yellowstone
- Yosemite
- Grand Canyon
- Zion
- Acadia
- Glacier
- Rocky Mountain
- Olympic
- Great Smoky Mountains
- And many more...

## Limitations

- Some parks may not have brochures in the expected URL patterns
- Text extraction quality depends on PDF structure
- Parsing accuracy varies based on brochure formatting
- Requires stable internet connection

## Troubleshooting

### "Could not find brochure URL"
Some parks may have different URL structures. The script tries multiple patterns but may not find all brochures.

### "Failed to extract text from PDF"
Some PDFs may be image-based or have complex layouts that prevent text extraction.

### Google Sheets authentication errors
Ensure you've run the authentication cells in Colab and have edit access to the spreadsheet.

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Author

Created for scraping National Parks data for research and educational purposes.

## Disclaimer

This script is for educational purposes. Please respect the NPS website's terms of service and use reasonable rate limiting when scraping.
