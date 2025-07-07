import dash
from dash import dcc, html, Input, Output, callback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Initialize the Dash app
app = dash.Dash(__name__)

def load_running_data():
    """Load and prepare running data"""
    df = pd.read_csv('running_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    # Filter to June 8th onwards
    df = df[df['date'] >= '2025-06-08']
    return df

def create_weekly_volume_chart(df):
    """Create weekly volume chart with 48km target"""
    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly_data = df.groupby('week').agg({
        'distance_km': 'sum',
        'date': 'count'
    }).rename(columns={'date': 'runs_count'}).reset_index()
    
    fig = px.bar(weekly_data, x='week', y='distance_km',
                 title='Weekly Running Distance (from June 8th)',
                 labels={'distance_km': 'Distance (km)', 'week': 'Week'},
                 hover_data=['runs_count'])
    
    # Add 48km target line
    fig.add_hline(y=48, line_dash="solid", line_color="green", line_width=2,
                  annotation_text="Pfitz Base Target: 48km")
    
    fig.update_layout(height=400)
    return fig

def create_pace_trend_chart(df):
    """Create pace trend chart"""
    fig = px.scatter(df, x='date', y='pace_min_per_km',
                     size='distance_km',
                     hover_data=['distance_km', 'average_heartrate'],
                     title='Pace Trends (from June 8th)',
                     labels={'pace_min_per_km': 'Pace (min/km)', 'date': 'Date'})
    
    # Set y-axis to start at 3:30
    fig.update_yaxes(range=[3.5, None])
    
    # Custom hover template
    fig.update_traces(
        hovertemplate='<b>Date:</b> %{x}<br>' +
                      '<b>Pace:</b> %{y} min/km<br>' +
                      '<b>Distance:</b> %{customdata[0]} km<br>' +
                      '<b>Average Heart Rate:</b> %{customdata[1]} bpm<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(height=400)
    return fig

def create_summary_stats(df):
    """Create summary statistics"""
    recent_weeks = df.groupby(df['date'].dt.to_period('W'))['distance_km'].sum()
    
    stats = {
        'total_runs': len(df),
        'total_distance': df['distance_km'].sum(),
        'avg_weekly': recent_weeks.mean(),
        'current_pace': df['pace_min_per_km'].tail(5).mean(),
        'target_gap': 48 - recent_weeks.mean()
    }
    return stats

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Strava Running Dashboard", 
                style={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '30px',
                       'font-family': '"Open Sans", verdana, arial, sans-serif'}),
        
        html.Div([
            html.Button('Refresh Data', id='refresh-btn', n_clicks=0,
                       style={'background-color': '#3498db', 'color': 'white', 
                              'border': 'none', 'padding': '10px 20px', 
                              'border-radius': '5px', 'cursor': 'pointer'})
        ], style={'text-align': 'center', 'margin-bottom': '30px'}),
        
        # Charts
        html.Div([
            dcc.Graph(id='weekly-volume-chart'),
        ], style={'margin-bottom': '30px'}),
        
        html.Div([
            dcc.Graph(id='pace-trend-chart'),
        ]),
        
    ], style={'max-width': '1200px', 'margin': '0 auto', 'padding': '20px'})
])

@callback(
    [Output('weekly-volume-chart', 'figure'),
     Output('pace-trend-chart', 'figure')],
    [Input('refresh-btn', 'n_clicks')]
)
def update_dashboard(n_clicks):
    """Update all dashboard components"""
    # Load fresh data
    df = load_running_data()
    
    # Create charts
    weekly_fig = create_weekly_volume_chart(df)
    pace_fig = create_pace_trend_chart(df)
    
    return weekly_fig, pace_fig

if __name__ == '__main__':
    app.run(debug=True, port=8050)