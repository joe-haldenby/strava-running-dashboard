import requests
import json
import pandas as pd
from datetime import datetime

def load_tokens():
    """Load saved Strava tokens"""
    with open('strava_tokens.json', 'r') as f:
        return json.load(f)

def fetch_activities(limit=50):
    """Fetch recent activities from Strava"""
    tokens = load_tokens()
    headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    
    # Get activities
    url = f"https://www.strava.com/api/v3/athlete/activities?per_page={limit}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activities = response.json()
        print(f"Fetched {len(activities)} activities")
        return activities
    else:
        print(f"Error fetching activities: {response.status_code}")
        return []

def filter_running_activities(activities):
    """Filter for running activities only"""
    running_types = ['Run', 'TrailRun', 'Treadmill']
    runs = [a for a in activities if a['type'] in running_types]
    print(f"Found {len(runs)} running activities")
    return runs

def create_running_dataframe(runs):
    """Convert running data to pandas DataFrame"""
    if not runs:
        print("No running activities found")
        return pd.DataFrame()
    
    # Extract key metrics
    data = []
    for run in runs:
        data.append({
            'date': run['start_date'][:10],  # Just the date part
            'name': run['name'],
            'distance_km': round(run['distance'] / 1000, 2),
            'duration_min': round(run['moving_time'] / 60, 1),
            'elevation_gain': run['total_elevation_gain'],
            'average_speed_kmh': round(run['average_speed'] * 3.6, 2),
            'max_speed_kmh': round(run['max_speed'] * 3.6, 2) if run['max_speed'] else None,
            'average_heartrate': run.get('average_heartrate'),
            'max_heartrate': run.get('max_heartrate'),
            'kudos_count': run['kudos_count'],
            'activity_id': run['id']
        })
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['pace_min_per_km'] = round(df['duration_min'] / df['distance_km'], 2)
    
    return df

def main():
    print("Fetching your Strava running data...")
    
    # Fetch activities
    activities = fetch_activities(100)  # Get last 100 activities
    
    # Filter for runs
    runs = filter_running_activities(activities)
    
    # Create DataFrame
    df = create_running_dataframe(runs)
    
    if not df.empty:
        print(f"\nRunning Data Summary:")
        print(f"- Total runs: {len(df)}")
        print(f"- Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"- Total distance: {df['distance_km'].sum():.1f} km")
        print(f"- Average distance: {df['distance_km'].mean():.1f} km")
        print(f"- Average pace: {df['pace_min_per_km'].mean():.1f} min/km")
        
        print(f"\nRecent runs:")
        print(df[['date', 'name', 'distance_km', 'pace_min_per_km']].head())
        
        # Save data
        df.to_csv('running_data.csv', index=False)
        print(f"\nData saved to running_data.csv")
        
        return df
    else:
        print("No running data found")
        return None

if __name__ == "__main__":
    df = main()