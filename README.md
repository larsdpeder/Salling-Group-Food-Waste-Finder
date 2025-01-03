
<img width="675" alt="Screenshot 2025-01-03 at 14 22 04" src="https://github.com/user-attachments/assets/7269e62d-3900-46fd-bed3-4d4bb6c3fb18" />


# Salling Group Food Waste Finder 🍽️

This Python script helps you find discounted food products from Salling Group stores (Føtex, Netto, Basalt, and Bilka) that are about to expire. Help reduce food waste and save money!

## About the Service 🌱

Salling Group has more than 10,000 food products on sale every day that are about to expire in local stores. Many customers may not be aware of these discounts. This tool helps reduce food waste in Denmark by making it easy to find heavily discounted food products with short expiry dates.

### Supported Stores 🏪
- Føtex
- Netto
- Basalt
- Bilka

## Features ✨

- Search for discounted products by:
  - ZIP code
  - Coordinates (latitude/longitude)
  - Specific store ID
- Automatic sorting by stock quantity
- Beautiful HTML output with product images
- PDF export for offline viewing
- Danish-friendly formatting and translations
- Real-time data from Salling Group's API

## API Information 🔌

This script uses the Salling Group Anti Food Waste API, which provides real-time information about discounted food products in Danish stores.

### Limitations and Notes 📊
- **Store Limit**: Maximum 20 stores returned per search
- **Search Scope**: 
  - ZIP code search includes all stores in that area
  - Coordinate search with large radius may return incomplete store lists
- **Daily Quota**: 10,000 requests per day
- **Documentation**: [Salling Group API Reference](https://developer.sallinggroup.com/api-reference#apis-food-waste)

### Endpoints Used 🛠
- `/v1/food-waste/?zip={zip}` - Search by ZIP code
- `/v1/food-waste/?geo={lat},{lon}&radius={km}` - Search by coordinates
- `/v1/food-waste/{store-id}` - Search by specific store

### Rate Limiting 🚦
- 10,000 requests per day (resets at midnight UTC)
- Spike protection to prevent abusive/burst requests
- Each search counts as one request
- Failed requests still count towards your daily quota

## Prerequisites 📋

- Python 3.7 or higher
- pip (Python package installer)
- Salling Group API token (authentication required)

## Installation 🚀

1. Clone this repository:
```bash
git clone [your-repo-url]
cd Foodwaste
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Get your API token:
   - Go to [Salling Group Developer Portal](https://developer.sallinggroup.com/)
   - Create an account
   - Create a new application
   - Generate an API token

4. Create a `.env` file in the project directory and add your API token:
```bash
SALLING_API_TOKEN=your_token_here
```

## Usage 💡

Run the script:
```bash
python food_waste_search.py
```

You'll be presented with three search options:
1. Search by ZIP code
2. Search by coordinates
3. Search by store ID

### Example Searches

**ZIP Code Search:**
```
Enter your choice (1-4): 1
Enter ZIP code: 8000
```

**Coordinate Search:**
```
Enter your choice (1-4): 2
Enter latitude (e.g., 56.154459): 56.154459
Enter longitude (e.g., 10.206777): 10.206777
Enter radius in km (default 5): 3
```

### Output Files 📄

The script generates two types of output in the `output` directory:
- HTML file with interactive layout and images
- PDF file for easy sharing and printing
- All files are timestamped for easy tracking

## Output Format 📊

For each store, you'll see:
- Store name and address
- List of discounted products sorted by stock quantity
- For each product:
  - Original and discounted price
  - Discount percentage
  - Current stock
  - Expiry time
  - Product image (when available)

## Notes 📝

- Stock quantities are not real-time and should be used as indicators only
- Products are only shown if they were added or updated in the last two days
- The API has rate limits, so avoid making too many requests in a short time
- Images are loaded directly from Salling Group's CDN for optimal performance

## Error Handling 🔧

If you encounter any errors:
1. Check that your API token is valid and correctly set in the `.env` file
2. Ensure you have all required packages installed
3. Check your internet connection
4. Verify that the coordinates or ZIP code are valid for Denmark

## Contributing 🤝

Feel free to submit issues and enhancement requests!
