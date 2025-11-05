"""
National Parks Brochure Scraper
================================
Scrapes park brochures from the US National Parks Service website,
extracts text and metadata, and writes results to Google Sheets.

Usage: Designed to run in Google Colab with necessary dependencies installed.
"""

import requests
import time
import re
import io
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

# For PDF processing
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")

# For Google Sheets
try:
    import gspread
    from google.auth import default
    from google.colab import auth
except ImportError:
    print("Google Colab libraries not available. Install gspread for standalone usage.")


class NationalParksScraper:
    """Scraper for National Parks brochures"""

    # Major National Parks with their 4-letter codes
    PARK_CODES = [
        ('yell', 'Yellowstone'),
        ('yose', 'Yosemite'),
        ('grca', 'Grand Canyon'),
        ('zion', 'Zion'),
        ('acad', 'Acadia'),
        ('glac', 'Glacier'),
        ('romo', 'Rocky Mountain'),
        ('olym', 'Olympic'),
        ('grsm', 'Great Smoky Mountains'),
        ('shen', 'Shenandoah'),
        ('arch', 'Arches'),
        ('cany', 'Canyonlands'),
        ('brca', 'Bryce Canyon'),
        ('jotr', 'Joshua Tree'),
        ('deva', 'Death Valley'),
        ('seki', 'Sequoia'),
        ('redw', 'Redwood'),
        ('noca', 'North Cascades'),
        ('mora', 'Mount Rainier'),
        ('grte', 'Grand Teton'),
        ('badl', 'Badlands'),
        ('cave', 'Carlsbad Caverns'),
        ('pefo', 'Petrified Forest'),
        ('thro', 'Theodore Roosevelt'),
        ('meve', 'Mesa Verde'),
        ('crla', 'Crater Lake'),
        ('lavo', 'Lassen Volcanic'),
        ('chis', 'Channel Islands'),
        ('pinn', 'Pinnacles'),
        ('kova', 'Kobuk Valley'),
    ]

    def __init__(self, delay_seconds: int = 10):
        """
        Initialize the scraper

        Args:
            delay_seconds: Delay between requests (default: 10)
        """
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.results = []

    def find_brochure_url(self, park_code: str, park_name: str) -> Optional[str]:
        """
        Find the brochure URL for a given park

        Args:
            park_code: 4-letter park code
            park_name: Full park name

        Returns:
            URL to brochure PDF or None if not found
        """
        # Common URL patterns for NPS brochures
        patterns = [
            f"https://www.nps.gov/{park_code}/planyourvisit/upload/{park_name.replace(' ', '-')}-Brochure.pdf",
            f"https://www.nps.gov/{park_code}/planyourvisit/upload/{park_name.replace(' ', '-')}-brochure.pdf",
            f"https://www.nps.gov/{park_code}/learn/upload/{park_name.replace(' ', '-')}-Brochure.pdf",
            f"https://home.nps.gov/{park_code}/planyourvisit/upload/{park_name.replace(' ', '-')}-Brochure.pdf",
        ]

        # Try to find the brochure page first
        try:
            brochure_page = f"https://www.nps.gov/{park_code}/planyourvisit/brochures.htm"
            response = self.session.get(brochure_page, timeout=30)

            if response.status_code == 200:
                # Look for PDF links in the page
                pdf_links = re.findall(r'href="([^"]*\.pdf)"', response.text)
                if pdf_links:
                    # Get the first PDF link
                    pdf_url = pdf_links[0]
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://www.nps.gov{pdf_url}" if pdf_url.startswith('/') else f"https://www.nps.gov/{park_code}/planyourvisit/{pdf_url}"
                    return pdf_url
        except Exception as e:
            print(f"Error checking brochure page for {park_name}: {e}")

        # Try common patterns
        for pattern in patterns:
            try:
                response = self.session.head(pattern, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    return pattern
            except:
                continue

        return None

    def download_pdf(self, url: str) -> Optional[bytes]:
        """
        Download PDF from URL

        Args:
            url: URL to PDF file

        Returns:
            PDF content as bytes or None if failed
        """
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            # Verify it's a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.endswith('.pdf'):
                print(f"Warning: URL may not be a PDF: {url}")
                return None

            return response.content
        except Exception as e:
            print(f"Error downloading PDF from {url}: {e}")
            return None

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF content

        Args:
            pdf_content: PDF file as bytes

        Returns:
            Extracted text
        """
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)

            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def parse_park_info(self, text: str, park_name: str) -> Dict[str, str]:
        """
        Parse park information from extracted text

        Args:
            text: Extracted text from PDF
            park_name: Name of the park

        Returns:
            Dictionary with parsed information
        """
        info = {
            'park_name': park_name,
            'state': '',
            'established_year': '',
            'size': ''
        }

        # Extract state (look for state names or abbreviations)
        state_pattern = r'\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b'
        state_match = re.search(state_pattern, text, re.IGNORECASE)
        if state_match:
            info['state'] = state_match.group(1)

        # Extract established year (look for patterns like "Established 1872" or "established in 1872")
        year_patterns = [
            r'[Ee]stablished[:\s]+(?:in\s+)?(\d{4})',
            r'[Dd]esignated[:\s]+(?:in\s+)?(\d{4})',
            r'[Cc]reated[:\s]+(?:in\s+)?(\d{4})',
        ]
        for pattern in year_patterns:
            year_match = re.search(pattern, text)
            if year_match:
                year = year_match.group(1)
                if 1850 <= int(year) <= datetime.now().year:
                    info['established_year'] = year
                    break

        # Extract size (look for acres, square miles, etc.)
        size_patterns = [
            r'(\d+[\d,]*)\s+acres',
            r'(\d+[\d,]*)\s+square\s+miles',
            r'(\d+[\d,]*)\s+hectares',
        ]
        for pattern in size_patterns:
            size_match = re.search(pattern, text, re.IGNORECASE)
            if size_match:
                info['size'] = size_match.group(0)
                break

        return info

    def scrape_parks(self, limit: int = 20) -> List[Dict[str, str]]:
        """
        Scrape park brochures

        Args:
            limit: Maximum number of parks to scrape

        Returns:
            List of dictionaries with park information
        """
        print(f"Starting to scrape up to {limit} National Park brochures...")
        print(f"Using {self.delay_seconds} second delay between requests")
        print("-" * 60)

        count = 0
        for park_code, park_name in self.PARK_CODES:
            if count >= limit:
                break

            print(f"\n[{count + 1}/{limit}] Processing {park_name}...")

            try:
                # Find brochure URL
                brochure_url = self.find_brochure_url(park_code, park_name)

                if not brochure_url:
                    print(f"  ❌ Could not find brochure URL for {park_name}")
                    continue

                print(f"  📄 Found brochure: {brochure_url}")

                # Download PDF
                pdf_content = self.download_pdf(brochure_url)

                if not pdf_content:
                    print(f"  ❌ Failed to download PDF for {park_name}")
                    continue

                print(f"  ✓ Downloaded PDF ({len(pdf_content)} bytes)")

                # Extract text
                text = self.extract_text_from_pdf(pdf_content)

                if not text:
                    print(f"  ❌ Failed to extract text from PDF")
                    continue

                print(f"  ✓ Extracted {len(text)} characters of text")

                # Parse information
                info = self.parse_park_info(text, park_name)
                info['brochure_url'] = brochure_url
                info['text_preview'] = text[:500]  # First 500 chars

                self.results.append(info)
                count += 1

                print(f"  ✓ Successfully processed {park_name}")
                print(f"     State: {info['state']}")
                print(f"     Established: {info['established_year']}")
                print(f"     Size: {info['size']}")

                # Delay before next request
                if count < limit:
                    print(f"\n  ⏳ Waiting {self.delay_seconds} seconds before next request...")
                    time.sleep(self.delay_seconds)

            except Exception as e:
                print(f"  ❌ Error processing {park_name}: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"✓ Scraping complete! Successfully processed {len(self.results)} parks")
        return self.results

    def write_to_google_sheets(self, spreadsheet_url: str):
        """
        Write results to Google Sheets

        Args:
            spreadsheet_url: URL to the Google Spreadsheet
        """
        try:
            # Authenticate with Google
            auth.authenticate_user()
            creds, _ = default()

            # Open the spreadsheet
            gc = gspread.authorize(creds)

            # Extract spreadsheet ID from URL
            spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
            spreadsheet = gc.open_by_key(spreadsheet_id)

            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet('Park Data')
            except:
                worksheet = spreadsheet.add_worksheet(title='Park Data', rows=100, cols=10)

            # Prepare data
            headers = ['Park Name', 'State', 'Established Year', 'Size', 'Brochure URL', 'Scraped Date']
            data = [headers]

            for result in self.results:
                row = [
                    result['park_name'],
                    result['state'],
                    result['established_year'],
                    result['size'],
                    result['brochure_url'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                data.append(row)

            # Clear existing data and write new data
            worksheet.clear()
            worksheet.update('A1', data)

            print(f"\n✓ Successfully wrote {len(self.results)} rows to Google Sheets")
            print(f"  Sheet: {spreadsheet.title} / {worksheet.title}")

        except Exception as e:
            print(f"\n❌ Error writing to Google Sheets: {e}")
            print("Make sure you've authenticated with Google Colab and have access to the spreadsheet")

    def save_results_json(self, filename: str = 'parks_data.json'):
        """
        Save results to JSON file as backup

        Args:
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Results saved to {filename}")
        except Exception as e:
            print(f"\n❌ Error saving JSON: {e}")


def main():
    """Main execution function"""

    # Configuration
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1QfsxIUok_5owSTJvI1_V5GNuzTsAOShHxktxh9w_jHA/edit?usp=sharing"
    LIMIT = 20
    DELAY_SECONDS = 10

    # Create scraper
    scraper = NationalParksScraper(delay_seconds=DELAY_SECONDS)

    # Scrape parks
    results = scraper.scrape_parks(limit=LIMIT)

    # Save to JSON as backup
    scraper.save_results_json('parks_data.json')

    # Write to Google Sheets
    if results:
        scraper.write_to_google_sheets(SPREADSHEET_URL)
    else:
        print("\n⚠ No results to write to Google Sheets")

    print("\n" + "=" * 60)
    print("✓ Script execution complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
