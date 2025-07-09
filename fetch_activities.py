import requests
import json
import pandas as pd
from datetime import datetime
import time

def load_tokens():
    """Load saved Strava tokens"""
    with open('strava_tokens.json', 'r') as f:
        return json.load(f)

def fetch_activities_summary(limit=50):
    """Fetch basic activities list"""
    tokens = load_tokens()
    headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    
    url = f"https://www.strava.com/api/v3/athlete/activities?per_page={limit}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activities = response.json()
        print(f"Fetched {len(activities)} activities")
        return activities
    else:
        print(f"Error fetching activities: {response.status_code}")
        return []

def fetch_detailed_activity(activity_id):
    """Fetch detailed data for a specific activity"""
    tokens = load_tokens()
    headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching detailed activity {activity_id}: {response.status_code}")
        return None

def extract_best_efforts(detailed_activity):
    """Extract best efforts data from detailed activity"""
    best_efforts = detailed_activity.get('best_efforts', [])
    
    # Standard distances we care about (in meters)
    target_distances = {
        400: '400m',
        804.67: '0.5_mile',  # 0.5 mile in meters
        1000: '1k',
        1609.34: '1_mile',   # 1 mile in meters
        3218.69: '2_mile',   # 2 miles in meters
        5000: '5k',
        10000: '10k'
    }
    
    efforts_data = {}
    
    for effort in best_efforts:
        distance = effort.get('distance', 0)
        
        # Find matching target distance (with some tolerance)
        for target_dist, name in target_distances.items():
            if abs(distance - target_dist) < 50:  # 50m tolerance
                efforts_data[f'{name}_time_sec'] = effort.get('elapsed_time', None)
                efforts_data[f'{name}_pace_min_per_km'] = calculate_pace_from_effort(
                    effort.get('elapsed_time', 0), distance
                )
                break
    
    return efforts_data

def calculate_pace_from_effort(time_seconds, distance_meters):
    """Calculate pace in min/km from time and distance"""
    if time_seconds == 0 or distance_meters == 0:
        return None
    
    distance_km = distance_meters / 1000
    pace_min_per_km = (time_seconds / 60) / distance_km
    return round(pace_min_per_km, 2)

def filter_running_activities(activities):
    """Filter for running activities only"""
    running_types = ['Run', 'TrailRun', 'Treadmill']
    runs = [a for a in activities if a['type'] in running_types]
    print(f"Found {len(runs)} running activities")
    return runs

def create_running_dataframe(runs):
    """Convert running data to enhanced pandas DataFrame"""
    if not runs:
        print("No running activities found")
        return pd.DataFrame()
    
    enhanced_data = []
    
    for i, run in enumerate(runs):
        print(f"Processing run {i+1}/{len(runs)}: {run['name']}")
        
        # Get detailed data for this run
        detailed = fetch_detailed_activity(run['id'])
        
        if detailed:
            # Extract basic data
            run_data = {
                'date': run['start_date'][:10],
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
            }
            
            # Calculate pace
            run_data['pace_min_per_km'] = round(run_data['duration_min'] / run_data['distance_km'], 2)
            
            # Extract GPS coordinates
            start_latlng = detailed.get('start_latlng', [None, None])
            run_data['start_lat'] = start_latlng[0] if start_latlng else None
            run_data['start_lon'] = start_latlng[1] if start_latlng else None
            
            # Extract best efforts
            best_efforts = extract_best_efforts(detailed)
            run_data.update(best_efforts)
            
            # Extract additional useful fields
            run_data['workout_type'] = detailed.get('workout_type')
            run_data['average_temp'] = detailed.get('average_temp')
            
            enhanced_data.append(run_data)
            
            # Rate limiting - be nice to Strava API
            time.sleep(0.5)  # 500ms between requests
        
        else:
            print(f"Failed to get detailed data for {run['name']}")
    
    # Create DataFrame
    df = pd.DataFrame(enhanced_data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def main():
    """Main function to fetch enhanced running data"""
    print("Fetching enhanced running data from Strava...")
    
    try:
        # Fetch activities
        activities = fetch_activities_summary(100)
        
        # Filter for runs
        runs = filter_running_activities(activities)
        
        # Create enhanced DataFrame
        df = create_running_dataframe(runs)
        
        if not df.empty:
            # Save as standard filename for backwards compatibility
            df.to_csv('running_data.csv', index=False)
            print(f"\n✅ Enhanced data saved to running_data.csv")
            
            # Print summary
            print(f"\nEnhanced Running Data Summary:")
            print(f"- Total runs: {len(df)}")
            print(f"- Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"- Runs with GPS: {df['start_lat'].notna().sum()}")
            
            # Show best efforts summary
            best_effort_columns = [col for col in df.columns if '_time_sec' in col]
            if best_effort_columns:
                efforts_count = df[best_effort_columns].notna().any(axis=1).sum()
                print(f"- Runs with best efforts: {efforts_count}")
                
                print(f"\nBest Efforts Data Available:")
                for col in best_effort_columns:
                    count = df[col].notna().sum()
                    if count > 0:
                        distance = col.replace('_time_sec', '')
                        print(f"  • {distance}: {count} runs")
            
            print(f"\n🎯 Ready for enhanced run classification and weather integration!")
            return df
        else:
            print("No running data found")
            return None
            
    except Exception as e:
        print(f"❌ Error processing activities: {e}")
        return None

if __name__ == "__main__":
    main()