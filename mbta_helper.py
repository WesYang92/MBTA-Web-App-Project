import os
from dotenv import load_dotenv
import urllib.request
import json
from datetime import datetime
import urllib.parse

# Load environment variables
load_dotenv()

# Get API keys from environment variables
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
MBTA_API_KEY = os.getenv("MBTA_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Useful base URLs (you need to add the appropriate parameters for each API request)
MAPBOX_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
MBTA_BASE_URL = "https://api-v3.mbta.com/stops"
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_json(url: str) -> dict:
    """
    Given a properly formatted URL for a JSON web API request, return a Python JSON object containing the response to that request.

    Both get_lat_lng() and get_nearest_station() might need to use this function.
    """
    try:
        # Create a Request object with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request) as f:
            response_text = f.read().decode('utf-8')
            return json.loads(response_text)
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code} - {e.reason}')
        return {}
    except urllib.error.URLError as e:
        print(f'URL Error: {e.reason}')
        return {}
    except Exception as e:
        print(f'Error fetching data: {e}')
        return {}

def get_lat_lng(place_name: str) -> tuple[str, str, str]:
    """
    Get coordinates and city name for a given place with proper URL encoding
    """
    try:
        # Properly encode the place name for URL
        query = urllib.parse.quote(place_name)
        url = f'{MAPBOX_BASE_URL}/{query}.json?access_token={MAPBOX_TOKEN}&types=place,poi'
        
        data = get_json(url)
        
        if not data or 'features' not in data or not data['features']:
            print(f"No location found for: {place_name}")
            return "Error", "Error", "Error"
            
        feature = data['features'][0]
        longitude, latitude = feature['center']
        
        # Extract city name from context
        city_name = "Unknown"
        context = feature.get("context", [])
        
        # First try to get the place name
        for ctx in context:
            if ctx.get("id", "").startswith("place."):
                city_name = ctx.get("text", "Unknown")
                break
        
        # If no city found in context, use the place name itself
        if city_name == "Unknown" and feature.get("text"):
            city_name = feature.get("text")
                
        return str(latitude), str(longitude), city_name
        
    except Exception as e:
        print(f'Error getting coordinates: {e}')
        return "Error", "Error", "Error"

def get_weather(city_name: str) -> dict:
    """
    Get weather information with proper URL encoding
    """
    try:
        # Properly encode the city name for URL
        encoded_city = urllib.parse.quote(f"{city_name},US")
        url = f"{WEATHER_BASE_URL}?q={encoded_city}&appid={WEATHER_API_KEY}&units=imperial"
        
        data = get_json(url)
        
        if not data or "main" not in data:
            print(f"No weather data found for: {city_name}")
            return {
                "temp": "N/A",
                "condition": "N/A",
                "description": "Weather data unavailable",
                "humidity": "N/A",
                "feels_like": "N/A",
                "wind_speed": "N/A"
            }
            
        return {
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data.get("wind", {}).get("speed", 0))
        }
        
    except Exception as e:
        print(f"Error getting weather: {e}")
        return {
            "temp": "Error",
            "condition": "Error",
            "description": "Error",
            "humidity": "Error",
            "feels_like": "Error",
            "wind_speed": "Error"
        }

def get_nearest_station(latitude: str, longitude: str) -> tuple[str, bool]:
    """
    Get nearest MBTA station with proper parameter handling
    """
    try:
        # Ensure parameters are properly formatted
        params = urllib.parse.urlencode({
            'api_key': MBTA_API_KEY,
            'filter[latitude]': latitude,
            'filter[longitude]': longitude,
            'sort': 'distance'
        })
        
        url = f"{MBTA_BASE_URL}?{params}"
        data = get_json(url)
        
        if not data or not data.get('data'):
            print(f"No station found near coordinates: ({latitude}, {longitude})")
            return "No station found", False
        
        station = data['data'][0]
        station_name = station['attributes']['name']
        wheelchair_accessible = bool(station['attributes']['wheelchair_boarding'])
        
        return station_name, wheelchair_accessible
    
    except Exception as e:
        print(f'Error finding nearest station: {e}')
        return 'Error finding station', False

def find_stop_near(place_name: str) -> tuple[str, bool]:
    """
    Given a place name or address, return the nearest MBTA stop and whether it is wheelchair accessible.

    This function might use all the functions above.
    """
    latitude, longitude, city_name = get_lat_lng(place_name)
    if latitude == 'Error' or longitude == 'Error':
        return 'Could not find location', False, {}
    
    station_name, wheelchair_accessible = get_nearest_station(latitude, longitude)
    weather_info =get_weather(city_name)
    return station_name, wheelchair_accessible, weather_info

def display_location_info(place_name: str) -> None:
    """Helper function to display formatted location, transit, and weather information"""
    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"Information for: {place_name}")
    print(f"Time: {current_time}")
    print(f"{'='*60}")
    
    # Get location info
    latitude, longitude, city_name = get_lat_lng(place_name)
    print(f"\n LOCATION")
    print(f"City: {city_name}")
    print(f"Coordinates: ({latitude}, {longitude})")
    
    # Get transit and weather info
    station_name, wheelchair_accessible, weather_info = find_stop_near(place_name)
    
    # Display transit information
    print(f"\n NEAREST MBTA STATION")
    print(f"Station: {station_name}")
    print(f"Wheelchair Accessible: {'✓' if wheelchair_accessible else '✗'}")
    
    # Display weather information
    print(f"\n  WEATHER CONDITIONS")
    if weather_info.get("temp") != "Error":
        print(f"Temperature: {weather_info['temp']}°F")
        print(f"Feels Like: {weather_info['feels_like']}°F")
        print(f"Condition: {weather_info['description']}")
        print(f"Humidity: {weather_info['humidity']}%")
        print(f"Wind Speed: {weather_info['wind_speed']} mph")
    else:
        print("Weather information unavailable")
    
    print(f"\n{'='*60}")


def main():
    """
    You should test all the above functions here
    """
    test_locations = [
            "Boston College",
            "Harvard University",
            "MIT",
            "Fenway Park",
            "Boston Common"
        ]
        
    print("\nFetching information for various Boston locations...")
    print("Note: This may take a few moments.\n")
        
    for location in test_locations:
        display_location_info(location)


if __name__ == "__main__":
    main()
