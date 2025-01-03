import requests
from typing import Optional, Dict, List, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import pytz
from markdown2 import Markdown
from weasyprint import HTML
from jinja2 import Template
import urllib.request
from pathlib import Path

@dataclass
class Offer:
    currency: str
    discount: float
    ean: str
    end_time: str
    last_update: str
    new_price: float
    original_price: float
    percent_discount: float
    start_time: str
    stock: int
    stock_unit: str

@dataclass
class Product:
    description: str
    ean: str
    image: Optional[str]

@dataclass
class Clearance:
    offer: Offer
    product: Product

class FoodWasteAPI:
    BASE_URL = "https://api.sallinggroup.com/v1/food-waste"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}"
        }
    
    def search_by_zip(self, zip_code: str) -> List[Dict]:
        """Search for food waste products by zip code."""
        params = {"zip": zip_code}
        return self._make_request(params)
    
    def search_by_coordinates(self, latitude: float, longitude: float, radius: int = 5) -> List[Dict]:
        """Search for food waste products by coordinates within a radius (km)."""
        params = {
            "geo": f"{latitude},{longitude}",
            "radius": radius
        }
        return self._make_request(params)
    
    def get_store_clearances(self, store_id: str) -> Dict:
        """Get food waste products for a specific store."""
        url = f"{self.BASE_URL}/{store_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _make_request(self, params: Dict) -> List[Dict]:
        """Make a request to the API with the given parameters."""
        response = requests.get(self.BASE_URL, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

def format_datetime(timestamp_str: str) -> str:
    """Convert UTC timestamp to Danish local time and format it."""
    # Parse the UTC timestamp
    dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    # Set UTC timezone
    utc = pytz.UTC
    dt = utc.localize(dt)
    # Convert to Danish time
    danish_tz = pytz.timezone('Europe/Copenhagen')
    danish_time = dt.astimezone(danish_tz)
    # Format in Danish style
    return danish_time.strftime("%d/%m/%Y kl. %H:%M")

def format_stock(stock: Union[int, float], unit: str) -> str:
    """Format stock amount with appropriate unit."""
    # Translate unit to Danish
    unit_translations = {
        'each': 'stk.',
        'kg': 'kg',
        'g': 'g'
    }
    
    danish_unit = unit_translations.get(unit.lower(), unit)
    
    if isinstance(stock, (int, float)):
        if danish_unit.lower() == 'kg':
            return f"{stock:.2f} {danish_unit}"
        return f"{int(stock)} {danish_unit}"
    return f"{stock} {danish_unit}"

def get_sort_key(clearance: Dict) -> float:
    """Get a sorting key for clearances based on stock quantity."""
    offer = clearance['offer']
    stock = offer['stock']
    unit = offer['stockUnit'].lower()
    
    # Convert kg to a comparable number (1 kg = 1000 units)
    if unit == 'kg':
        return float(stock) * 1000
    # For pieces (stk), just use the number
    return float(stock)

def get_optimized_image_url(original_url: str) -> str:
    """Convert image URL to optimized format."""
    if not original_url:
        return ""
    
    if "digitalassets.sallinggroup.com" in original_url:
        # URL is already in the correct format
        return original_url
    
    # Extract the asset ID from various URL formats
    asset_id = None
    if "dam.dsg.dk" in original_url:
        # Extract ID from URLs like: https://dam.dsg.dk/services/assets.img/id/f8f240ff-5e83-435a-a55a-477a6540b89b/...
        try:
            asset_id = original_url.split('/id/')[1].split('/')[0]
        except IndexError:
            return original_url
    
    if asset_id:
        # Construct the optimized URL
        return f"https://digitalassets.sallinggroup.com/image/upload/e_trim/c_limit,e_sharpen:80,f_auto,q_auto,w_400,h_400/{asset_id}"
    
    return original_url

def generate_outputs(data: Union[List[Dict], Dict]) -> Tuple[str, str]:
    """Generate HTML and PDF outputs for the clearances data."""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create images directory if it doesn't exist
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    base_filename = f"tilbud_{current_time}"
    
    # Generate HTML content
    html_content = f"""
    <h1>Tilbud med kort holdbarhed</h1>
    <p class="updated">Opdateret: {datetime.now().strftime('%d/%m/%Y kl. %H:%M')}</p>
    """
    
    if isinstance(data, dict):
        stores = [data]
    else:
        stores = data
    
    for store in stores:
        html_content += f'<div class="store">\n'
        html_content += f'<h2>{store["store"]["name"]}</h2>\n'
        html_content += f'<p><strong>Adresse:</strong> {store["store"]["address"]["street"]}, {store["store"]["address"]["zip"]} {store["store"]["address"]["city"]}</p>\n'
        
        # Sort clearances by stock quantity
        clearances = sorted(store['clearances'], 
                          key=get_sort_key,
                          reverse=True)
        
        for clearance in clearances:
            product = clearance['product']
            offer = clearance['offer']
            
            # Get optimized image URL
            image_url = ""
            if product.get('image'):
                image_url = get_optimized_image_url(product['image'])
            
            html_content += '<div class="item">\n'
            if image_url:
                html_content += f'<img src="{image_url}" alt="{product["description"]}" loading="lazy">\n'
            else:
                html_content += '<div style="width:100px;height:100px;background:#eee;"></div>\n'
            
            html_content += '<div class="item-details">\n'
            html_content += f'<h3>{product["description"]}</h3>\n'
            html_content += f'<p class="price"><span class="original-price">{offer["originalPrice"]} {offer["currency"]}</span> → <strong>{offer["newPrice"]} {offer["currency"]}</strong></p>\n'
            html_content += f'<p><span class="discount">-{offer["percentDiscount"]:.1f}%</span></p>\n'
            html_content += f'<p class="stock">📦 Beholdning: {format_stock(offer["stock"], offer["stockUnit"])}</p>\n'
            html_content += f'<p class="valid-until">⏰ Gyldig indtil: {format_datetime(offer["endTime"])}</p>\n'
            html_content += '</div>\n'
            html_content += '</div>\n'
        
        html_content += '</div>\n'
    
    # Read HTML template
    with open('template.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # Generate final HTML with template
    final_html = template.render(content=html_content)
    
    # Save HTML file
    html_file = output_dir / f"{base_filename}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    # Generate PDF
    pdf_file = output_dir / f"{base_filename}.pdf"
    HTML(string=final_html).write_pdf(pdf_file)
    
    return str(html_file), str(pdf_file)

def export_to_markdown(data: Union[List[Dict], Dict], filename: str = None):
    """Export clearances data to a markdown file."""
    if filename is None:
        # Create filename with current timestamp
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"tilbud_{current_time}.md"
    
    markdown_content = "# Tilbud med kort holdbarhed\n\n"
    markdown_content += f"*Opdateret: {datetime.now().strftime('%d/%m/%Y kl. %H:%M')}*\n\n"
    
    if isinstance(data, dict):
        stores = [data]
    else:
        stores = data
    
    for store in stores:
        markdown_content += f"## {store['store']['name']}\n"
        markdown_content += f"**Adresse:** {store['store']['address']['street']}, {store['store']['address']['zip']} {store['store']['address']['city']}\n\n"
        
        # Sort clearances by stock quantity
        clearances = sorted(store['clearances'], 
                          key=get_sort_key,
                          reverse=True)
        
        for clearance in clearances:
            product = clearance['product']
            offer = clearance['offer']
            
            markdown_content += f"### {product['description']}\n"
            markdown_content += f"- 💰 ~~{offer['originalPrice']} {offer['currency']}~~ → **{offer['newPrice']} {offer['currency']}**\n"
            markdown_content += f"- 🏷️ Rabat: **{offer['percentDiscount']:.1f}%**\n"
            markdown_content += f"- 📦 Beholdning: {format_stock(offer['stock'], offer['stockUnit'])}\n"
            markdown_content += f"- ⏰ Gyldig indtil: {format_datetime(offer['endTime'])}\n"
            if product.get('image'):
                markdown_content += f"- 🖼️ [Se billede]({product['image']})\n"
            markdown_content += "\n---\n\n"
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename

def print_clearances(data: Union[List[Dict], Dict]):
    """Pretty print the clearances data and generate output files."""
    # Generate HTML and PDF outputs
    html_file, pdf_file = generate_outputs(data)
    print(f"\nOutput filer genereret:")
    print(f"- HTML: {html_file}")
    print(f"- PDF: {pdf_file}")
    
    if isinstance(data, dict):
        stores = [data]
    else:
        stores = data
    
    for store in stores:
        print(f"\nButik: {store['store']['name']}")
        print(f"Adresse: {store['store']['address']['street']}, {store['store']['address']['zip']} {store['store']['address']['city']}")
        print("\nTilbud (sorteret efter størst beholdning):")
        
        clearances = sorted(store['clearances'], 
                          key=get_sort_key,
                          reverse=True)
        
        for clearance in clearances:
            product = clearance['product']
            offer = clearance['offer']
            print(f"\n- {product['description']}")
            print(f"  Oprindelig pris: {offer['originalPrice']} {offer['currency']}")
            print(f"  Ny pris: {offer['newPrice']} {offer['currency']}")
            print(f"  Rabat: {offer['percentDiscount']:.1f}%")
            print(f"  Beholdning: {format_stock(offer['stock'], offer['stockUnit'])}")
            print(f"  Gyldig indtil: {format_datetime(offer['endTime'])}")

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API token from environment variable
    api_token = os.getenv('SALLING_API_TOKEN')
    if not api_token:
        print("Error: Please set your API token in the .env file")
        print("Create a .env file and add: SALLING_API_TOKEN=your_token_here")
        return
    
    api = FoodWasteAPI(api_token)
    
    while True:
        print("\nFood Waste Search Options:")
        print("1. Search by ZIP code")
        print("2. Search by coordinates")
        print("3. Search by store ID")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            zip_code = input("Enter ZIP code: ")
            try:
                results = api.search_by_zip(zip_code)
                print_clearances(results)
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
        
        elif choice == "2":
            try:
                lat = float(input("Enter latitude (e.g., 56.154459): "))
                lon = float(input("Enter longitude (e.g., 10.206777): "))
                radius = int(input("Enter radius in km (default 5): ") or "5")
                results = api.search_by_coordinates(lat, lon, radius)
                print_clearances(results)
            except (ValueError, requests.exceptions.RequestException) as e:
                print(f"Error: {e}")
        
        elif choice == "3":
            store_id = input("Enter store ID: ")
            try:
                results = api.get_store_clearances(store_id)
                print_clearances(results)
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
        
        elif choice == "4":
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
