from flask import Flask, render_template, request
from datetime import datetime
from mbta_helper import get_lat_lng, get_nearest_station, get_weather

app = Flask(__name__)

@app.route('/')
def index():
    """Display search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search request"""
    try:
        place_name = request.form.get('place_name')
        if not place_name:
            return render_template('index.html', error="Please enter a location")

        # Get location data
        latitude, longitude, city = get_lat_lng(place_name ,)
        if latitude == "Error" or longitude == "Error":
            return render_template('index.html', error="Location not found")

        # Get station data
        station_name, wheelchair_accessible = get_nearest_station(latitude, longitude)
        if station_name == "Error finding station":
            return render_template('index.html', error="No nearby stations found")

        # Get weather data
        weather_info = get_weather(city)
        if weather_info.get("temp") == "Error":
            return render_template('index.html', error="Weather data not available")

        # Format data for template
        location_data = {
            'city': city,
            'lat': latitude,
            'lon': longitude
        }

        station_data = {
            'name': station_name,
            'wheelchair_accessible': wheelchair_accessible
        }

        # Get current time
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return render_template('result.html',
                             place_name=place_name,
                             location=location_data,
                             station=station_data,
                             weather=weather_info,
                             timestamp=timestamp)

    except Exception as e:
        print(f"Error in search route: {str(e)}")  # Debug print
        return render_template('index.html', error=f"An error occurred: {str(e)}")

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True)