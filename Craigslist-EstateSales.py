import requests
import csv
from bs4 import BeautifulSoup
from datetime import datetime, date


scraped_data = []

def scrape_listing_details(url):
    details = {}
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        description_section = soup.find('section', {'id': 'postingbody'})
        if description_section:
            description = description_section.text.replace('QR Code Link to This Post', '').strip()
            details['description'] = description.encode('ascii', 'ignore').decode('ascii')  
        
        mapbox = soup.find("div", {"class": "mapbox"})
        if mapbox:
            map_address = mapbox.find("div", {"class": "mapaddress"})
            if map_address:
                details['map_address'] = map_address.text.strip()
            map_element = mapbox.find("div", {"id": "map"})
            if map_element:
                details['latitude'] = map_element['data-latitude']
                details['longitude'] = map_element['data-longitude']
        
        dates = []
        for date_span in soup.find_all("span", {"class": "otherpostings"}):
            date_link = date_span.find("a")
            if date_link:
                try:
                    date_text = date_link.text.split()[-1]
                    date_obj = datetime.strptime(date_text, '%Y-%m-%d').date()
                    if date_obj >= date.today():  
                        if date_obj.weekday() in [5, 6] and date_obj.weekday() not in [0, 1, 2, 3, 4]:
                            # Only find sales on Saturday or Sunday
                            # 0 = Monday
                            # 1 = Tuesday
                            # 2 = Wednesday
                            # 3 = Thursday
                            # 4 = Friday
                            # 5 = Saturday
                            # 6 = Sunday
                            dates.append(date_obj.strftime('%A, %m/%d/%Y'))
                except ValueError:
                    print(f"Skipping invalid date: {date_link.text}")
        details['dates'] = dates

        return details
    except requests.exceptions.RequestException as e:
        print(f"Error making the request for {url}: {e}")
        return None

url = "https://pittsburgh.craigslist.org/search/sss?query=estate%20sale"

try:
    print("Sending request...")
    response = requests.get(url)
    response.raise_for_status()
    print("Request successful.")
except requests.exceptions.RequestException as e:
    print("Error making the request:", e)
    exit(1)

soup = BeautifulSoup(response.content, "html.parser")

listings = soup.find_all("li", {"class": "cl-static-search-result"})

print(f"Found {len(listings)} listings.")

for listing in listings:
    title_element = listing.find("div", {"class": "title"})
    if title_element:
        title = title_element.text.strip()
        if "estate sale" in title.lower():
            listing_url = listing.find("a")["href"]
            
            details = scrape_listing_details(listing_url)
            
            if details and 'dates' in details and details['dates']:
                print("Title:", title)
                print("URL:", listing_url)
                
                if 'map_address' in details:
                    print("Address:", details['map_address'])
                if 'latitude' in details:
                    print("Lat:", details['latitude'])
                if 'longitude' in details:
                    print("Long:", details['longitude'])
                if 'dates' in details:
                    print("Dates:", ', '.join(details['dates']))
                if 'description' in details:
                    print("Description:", details['description'])
                
                print("-" * 40)
                
                scraped_data.append({
                    'Title': title,
                    'Address': details.get('map_address', ''),
                    'URL': listing_url,
                    'Lat': details.get('latitude', ''),
                    'Long': details.get('longitude', ''),
                    'Dates': ', '.join(details.get('dates', [])),
                    'Description': details.get('description', '')
                })

with open('Estate_Sales.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Title', 'Address', 'Dates', 'Description', 'URL', 'Lat', 'Long']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in scraped_data:
        writer.writerow(row)