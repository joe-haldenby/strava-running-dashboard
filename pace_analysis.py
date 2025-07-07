import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Force browser display
pio.renderers.default = "browser"

def create_pace_analysis():
    # Load the data
    df = pd.read_csv('running_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter to recent training (June onwards)
    df = df[df['date'] >= '2025-06-08']
    
    # Chart 1: Pace over time with distance as bubble size
    fig1 = px.scatter(df, x='date', y='pace_min_per_km', 
                     size='distance_km',
                     hover_data=['name', 'distance_km'],
                     title='Running Pace Trends (Recent Training)',
                     labels={'pace_min_per_km': 'Pace (min/km)', 'date': 'Date'})
    
    fig1.write_html("pace_chart.html")
    print("Pace chart saved as pace_chart.html - open this file in your browser!")
    fig1.show(renderer="browser")
    
    # Chart 2: Weekly volume vs target
    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly_data = df.groupby('week')['distance_km'].sum().reset_index()
    
    fig2 = px.bar(weekly_data, x='week', y='distance_km',
                  title='Weekly Volume vs Pfitz Base Target (48km)',
                  labels={'distance_km': 'Distance (km)', 'week': 'Week'})
    
    # Add 48km target line
    fig2.add_hline(y=48, line_dash="solid", line_color="green",
                   annotation_text="Pfitz Base Target: 48km")
    
    fig2.write_html("volume_chart.html")
    print("Volume chart saved as volume_chart.html - open this file in your browser!")
    fig2.show(renderer="browser")
    
    # Training analysis
    recent_weeks = weekly_data['distance_km'].tail(4)
    print(f"Base Training Progress:")
    print(f"- Current average (last 4 weeks): {recent_weeks.mean():.1f} km/week")
    print(f"- Target: 48 km/week")
    print(f"- Gap to target: {48 - recent_weeks.mean():.1f} km/week")
    print(f"- Average easy pace: {df['pace_min_per_km'].median():.2f} min/km")
    print(f"- Pace range: {df['pace_min_per_km'].min():.2f} - {df['pace_min_per_km'].max():.2f} min/km")

if __name__ == "__main__":
    create_pace_analysis()