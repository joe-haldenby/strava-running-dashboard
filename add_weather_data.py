import pandas as pd
import requests
import json
import time
from datetime import datetime
from config import WEATHER_API_KEY

def get_historical_weather(lat, lon, datetime_str):
    """
    Get historical weather data for a specific location and datetime
    Using OpenWeatherMap One Call API 3.0
    """
    # Convert datetime string to unix timestamp
    # Handle both ISO format (2025-07-06T14:30:00Z) and date only
    if 'T' in datetime_str:
        # ISO format from Strava - remove Z and T
        datetime_str = datetime_str.replace('Z', '').replace('T', ' ')

    try:
        date_obj = datetime.strptime(datetime_str[:19], '%Y-%m-%d %H:%M:%S')
    except:
        # Fallback to date only if parsing fails
        date_obj = datetime.strptime(datetime_str[:10], '%Y-%m-%d')

    timestamp = int(date_obj.timestamp())
    
    # OpenWeatherMap One Call API 3.0 - Historical data
    url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
    
    params = {
        'lat': lat,
        'lon': lon,
        'dt': timestamp,
        'appid': WEATHER_API_KEY,
        'units': 'metric'  # Celsius, km/h, etc.
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant weather info
            current_weather = data.get('data', [{}])[0] if data.get('data') else {}
            
            weather_info = {
                'temperature_c': current_weather.get('temp'),
                'feels_like_c': current_weather.get('feels_like'),
                'humidity_pct': current_weather.get('humidity')
            }
            
            return weather_info
            
        else:
            print(f"Weather API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def add_weather_to_running_data():
    """
    Add weather data to existing running data using GPS coordinates
    """
    print("Adding weather data to running activities...")
    
    # Load enhanced running data
    try:
        df = pd.read_csv('running_data.csv')
        df['date'] = pd.to_datetime(df['date'])
    except FileNotFoundError:
        print("❌ running_data.csv not found. Run fetch_activities.py first.")
        return None
    
    # Check if we have GPS coordinates
    runs_with_gps = df[df['start_lat'].notna() & df['start_lon'].notna()]
    
    if len(runs_with_gps) == 0:
        print("❌ No GPS coordinates found in data. Make sure enhanced fetch_activities.py was used.")
        return None
    
    print(f"Found {len(runs_with_gps)} runs with GPS coordinates")
    
    # Add weather data for each run
    for idx, row in runs_with_gps.iterrows():
        run_datetime = row.get('start_datetime', row['date'])
        print(f"Getting weather for {run_datetime}: {row['name']}")
        
        weather = get_historical_weather(
            lat=row['start_lat'],
            lon=row['start_lon'], 
            datetime_str=run_datetime
        )
        
        if weather:
            # Add weather data to the row
            for key, value in weather.items():
                df.at[idx, key] = value
        
        # Rate limiting - OpenWeatherMap allows 60 calls/minute
        time.sleep(1.1)  # Just over 1 second between calls
    
    # Save enhanced data with weather
    df.to_csv('running_data.csv', index=False)
    print(f"\n✅ Weather data added and saved to running_data.csv")
    
    # Print summary
    weather_runs = df[df['temperature_c'].notna()]
    if len(weather_runs) > 0:
        print(f"\nWeather Data Summary:")
        print(f"- Runs with weather data: {len(weather_runs)}")
        print(f"- Temperature range: {weather_runs['temperature_c'].min():.1f}°C to {weather_runs['temperature_c'].max():.1f}°C")
        print(f"- Average temperature: {weather_runs['temperature_c'].mean():.1f}°C")
        print(f"- Average humidity: {weather_runs['humidity_pct'].mean():.1f}%")
    
    return df

def main():
    """Main function to add weather data"""
    
    # Check if weather API key is configured
    if not WEATHER_API_KEY or WEATHER_API_KEY == "your_openweather_api_key_here":
        print("❌ Please add your OpenWeatherMap API key to config.py")
        print("Set WEATHER_API_KEY = 'your_actual_api_key'")
        return
    
    # Add weather data
    df = add_weather_to_running_data()
    
    if df is not None:
        print(f"\n🎯 Next steps:")
        print(f"- Update dashboard to show weather data")
        print(f"- Add temperature analysis charts")
        print(f"- Enhance run classifier with weather context")

if __name__ == "__main__":
    main()