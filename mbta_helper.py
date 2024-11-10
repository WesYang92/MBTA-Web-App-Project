import os
from dotenv import load_dotenv
import urllib.request
import json
from pprint import pprint
from datetime import datetime

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
        with urllib.request.urlopen(url) as f:
            response_text = f.read().decode('utf-8')
            response_data = json.loads(response_text)
            return response_data
    except Exception as e:
        print(f'Error fetching date:{e}')
        return {}


def get_lat_lng(place_name: str) -> tuple[str, str, str]:
    """
    Given a place name or address, return a (latitude, longitude) tuple with the coordinates of the given place.

    See https://docs.mapbox.com/api/search/geocoding/ for Mapbox Geocoding API URL formatting requirements.
    """
    try:
        encoded_place = place_name.replace(' ', '%20')
        url = f'{MAPBOX_BASE_URL}/{encoded_place}.json?access_token={MAPBOX_TOKEN}&types=poi'
        data = get_json(url)
        
        if not data.get('features'):
            return "Error", "Error", "Error"
            
        feature = data['features'][0]
        longitude, latitude = feature['center']
        
        city_name = "Unknown"
        for context in feature.get("context", []):
            if context.get("id", "").startswith("place."):
                city_name = context.get("text", "Unknown")
                break
                
        return str(latitude), str(longitude), city_name
        
    except Exception as e:
        print(f'Error getting coordinates: {e}')
        return "Error", "Error", "Error"

def get_weather(city_name: str) -> dict:
    """
    Get weather information for a given city.
    """
    try:
        url = (
            f"{WEATHER_BASE_URL}?"
            f"q={city_name},US"
            f"&appid={WEATHER_API_KEY}"
            f"&units=imperial"  # Use Fahrenheit
        )
        
        data = get_json(url)
        
        if "main" not in data:
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
            "wind_speed": round(data["wind"]["speed"])
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
    Given latitude and longitude strings, return a (station_name, wheelchair_accessible) tuple for the nearest MBTA station to the given coordinates.

    See https://api-v3.mbta.com/docs/swagger/index.html#/Stop/ApiWeb_StopController_index for URL formatting requirements for the 'GET /stops' API.
    """
    try:
        url = (
            f"{MBTA_BASE_URL}?"
            f"api_key={MBTA_API_KEY}"
            f"&filter[latitude]={latitude}"
            f"&filter[longitude]={longitude}"
            "&sort=distance"
        )
        data = get_json(url)
        
        if not data.get('data'):
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
    latitude, longitude = get_lat_lng(place_name)
    if latitude == 'Error' or longitude == 'Error':
        return 'Could not find location', False, {}
    
    station_name, wheelchair_accessible = get_nearest_station(latitude, longitude)
    weather_info =get_weather(city_name)
    return station_name, wheelchair_accessible, weather_info

def display_location_info(place_name: str) -> None:
    """Helper function to display formatted location, transit, and weather information"""
    print(f"\n{'='*60}")
    print(f"Information for: {place_name}")
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
