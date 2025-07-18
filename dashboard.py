import dash
from dash import dcc, html, Input, Output, callback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date

# Initialize the Dash app
app = dash.Dash(__name__)

# Professional color palette - bright, vibrant
COLORS = {
    'dark_green': '#1B5E20',      # Recovery
    'light_green': '#4CAF50',     # General Aerobic
    'yellow': '#FFC107',          # Endurance
    'orange': '#FF9800',          # Lactate Threshold
    'red': '#F44336',             # VO2 Max
    'race_blue': '#2196F3',       # Primary blue (lighter)
    'dark_blue': '#0D47A1',       # 10K PB line
    'grey': '#757575'             # Other
}

def load_running_data():
    """Load and prepare running data with classifications"""
    try:
        df = pd.read_csv('classified_running_data.csv')
    except FileNotFoundError:
        # Fallback to regular data if classified version doesn't exist
        df = pd.read_csv('running_data.csv')
        df['run_type'] = 'General Aerobic'  # Default classification
    
    df['date'] = pd.to_datetime(df['date'])
    return df  # Return all data, filtering will happen in callbacks

def create_weekly_volume_chart(df):
    """05.01: Weekly KMs bar chart"""
    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly_data = df.groupby('week').agg({
        'distance_km': 'sum',
        'date': 'count'
    }).rename(columns={'date': 'runs_count'}).reset_index()
    
    fig = px.bar(weekly_data, x='week', y='distance_km',
                 title='Weekly Volume',
                 labels={'distance_km': 'Distance (km)', 'week': 'Week'},
                 hover_data=['runs_count'])
    
    # Apply race blue color to bars
    fig.update_traces(marker_color=COLORS['race_blue'])
    
    # Professional styling with light background
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20, b=20)
        ),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    
    return fig

def create_pace_trend_chart(df):
    """05.02: Pace trend scatter chart with run_type color coding"""
    # Define colors for each run type using our palette - IN TRAINING INTENSITY ORDER
    run_type_colors = {
        'Recovery': COLORS['dark_green'],
        'General Aerobic': COLORS['light_green'],
        'Endurance': COLORS['yellow'],
        'Lactate Threshold': COLORS['orange'],
        'VO₂ Max Intervals': COLORS['red'],
        'Race': COLORS['race_blue'],  # Changed to blue
        'Other': COLORS['grey']
    }
    
    # Ensure run_type is categorical with correct order for legend
    intensity_order = ['Recovery', 'General Aerobic', 'Endurance', 'Lactate Threshold', 'VO₂ Max Intervals', 'Race', 'Other']
    df['run_type'] = pd.Categorical(df['run_type'], categories=intensity_order, ordered=True)
    
    fig = px.scatter(df, x='date', y='pace_min_per_km',
                     color='run_type',
                     color_discrete_map=run_type_colors,
                     category_orders={'run_type': intensity_order},
                     hover_data=['distance_km', 'average_heartrate'],
                     title='Pace Trends by Run Type',
                     labels={'pace_min_per_km': 'Pace (min/km)', 'date': 'Date'})
    
    # Set y-axis to start at 3:30
    fig.update_yaxes(range=[3.5, None])
    
    # Custom hover template
    fig.update_traces(
        hovertemplate='<b>Date:</b> %{x}<br>' +
                      '<b>Pace:</b> %{y} min/km<br>' +
                      '<b>Distance:</b> %{customdata[0]} km<br>' +
                      '<b>Average Heart Rate:</b> %{customdata[1]} bpm<br>' +
                      '<extra></extra>',
        marker=dict(size=12)  # Increase dot size for better visibility
    )
    
    # Professional styling with light background
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20, b=20)
        ),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        legend=dict(font=dict(size=12)),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    
    return fig

def create_weather_impact_chart(df):
    """05.03: Weather impact - weekly grouped bar chart by temperature bins for all runs"""
    # Use all runs, not just General Aerobic
    all_runs = df.copy()
    
    if len(all_runs) == 0 or 'feels_like_c' not in all_runs.columns:
        # Create empty chart if no data
        fig = go.Figure()
        fig.add_annotation(text="No runs with weather data", 
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#7f8c8d'))
        fig.update_layout(
            height=450,
            title=dict(
                text="Pace by Weather Conditions",
                font=dict(size=18, color='#2c3e50'),
                x=0.5,
                xanchor='center',
                pad=dict(t=20, b=20)
            ),
            font=dict(family='"Open Sans", verdana, arial, sans-serif'),
            margin=dict(t=60, b=40, l=40, r=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )
        return fig
    
    # Remove runs without weather data
    all_runs = all_runs.dropna(subset=['feels_like_c'])
    
    if len(all_runs) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No weather data available for runs", 
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#7f8c8d'))
        fig.update_layout(
            height=450,
            title=dict(
                text="Pace by Weather Conditions",
                font=dict(size=18, color='#2c3e50'),
                x=0.5,
                xanchor='center',
                pad=dict(t=20, b=20)
            ),
            font=dict(family='"Open Sans", verdana, arial, sans-serif'),
            margin=dict(t=60, b=40, l=40, r=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )
        return fig
    
    # Create temperature bins
    def get_temp_bin(temp):
        if temp < 5:
            return 'Cold'
        elif temp < 15:
            return 'Cool'
        elif temp < 25:
            return 'Warm'
        else:
            return 'Hot'
    
    all_runs['temp_bin'] = all_runs['feels_like_c'].apply(get_temp_bin)
    all_runs['week'] = all_runs['date'].dt.to_period('W').dt.start_time
    
    # Group by week and temperature bin, calculate average pace
    weekly_temp_data = all_runs.groupby(['week', 'temp_bin']).agg({
        'pace_min_per_km': 'mean',
        'date': 'count'
    }).rename(columns={'date': 'run_count'}).reset_index()
    
    # Temperature bin colors
    temp_colors = {
        'Cold': '#1976D2',      # Blue
        'Cool': '#64B5F6',      # Light blue
        'Warm': '#FF9800',      # Orange
        'Hot': '#F44336'        # Red
    }
    
    # Create grouped bar chart
    fig = px.bar(weekly_temp_data, x='week', y='pace_min_per_km', 
                 color='temp_bin',
                 color_discrete_map=temp_colors,
                 title='Pace by Weather Conditions',
                 labels={'pace_min_per_km': 'Average Pace (min/km)', 'week': 'Week', 'temp_bin': 'Temperature'},
                 hover_data=['run_count'],
                 barmode='group')
    
    # Professional styling with light background
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20, b=20)
        ),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        legend=dict(font=dict(size=12), title=dict(text='Temperature')),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    
    return fig

def create_pb_tracking_chart(df):
    """05.04: PB Tracking line chart for 5k and 10k best efforts"""
    # Check if we have best efforts data
    if '5k_pace_min_per_km' not in df.columns and '10k_pace_min_per_km' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No best efforts data available", 
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color='#7f8c8d'))
        fig.update_layout(
            height=450,
            title=dict(
                text="PB Tracking",
                font=dict(size=18, color='#2c3e50'),
                x=0.5,
                xanchor='center',
                pad=dict(t=20, b=20)
            ),
            font=dict(family='"Open Sans", verdana, arial, sans-serif'),
            margin=dict(t=60, b=40, l=40, r=40),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa'
        )
        return fig
    
    fig = go.Figure()
    
    # Process 10K PBs FIRST (so it appears first in legend)
    if '10k_pace_min_per_km' in df.columns:
        tenK_data = df[df['10k_pace_min_per_km'].notna()].copy()
        if len(tenK_data) > 0:
            # Calculate cumulative PB (best pace so far)
            tenK_data = tenK_data.sort_values('date')
            tenK_data['pb_pace'] = tenK_data['10k_pace_min_per_km'].cummin()
            
            # Convert pace to time for hover
            tenK_data['race_time_min'] = tenK_data['pb_pace'] * 10
            
            fig.add_trace(go.Scatter(
                x=tenK_data['date'],
                y=tenK_data['pb_pace'],
                mode='lines+markers',
                name='10K PB',
                line=dict(color=COLORS['dark_blue'], width=3),
                marker=dict(size=8),
                hovertemplate='<b>10K PB</b><br>' +
                             'Date: %{x}<br>' +
                             'Pace: %{y:.2f} min/km<br>' +
                             'Time: %{customdata:.1f} minutes<br>' +
                             '<extra></extra>',
                customdata=tenK_data['race_time_min']
            ))
    
    # Process 5K PBs SECOND (so it appears second in legend)
    if '5k_pace_min_per_km' in df.columns:
        fiveK_data = df[df['5k_pace_min_per_km'].notna()].copy()
        if len(fiveK_data) > 0:
            # Calculate cumulative PB (best pace so far)
            fiveK_data = fiveK_data.sort_values('date')
            fiveK_data['pb_pace'] = fiveK_data['5k_pace_min_per_km'].cummin()
            
            # Convert pace to time for hover
            fiveK_data['race_time_min'] = fiveK_data['pb_pace'] * 5
            
            fig.add_trace(go.Scatter(
                x=fiveK_data['date'],
                y=fiveK_data['pb_pace'],
                mode='lines+markers',
                name='5K PB',
                line=dict(color=COLORS['race_blue'], width=3),
                marker=dict(size=8),
                hovertemplate='<b>5K PB</b><br>' +
                             'Date: %{x}<br>' +
                             'Pace: %{y:.2f} min/km<br>' +
                             'Time: %{customdata:.1f} minutes<br>' +
                             '<extra></extra>',
                customdata=fiveK_data['race_time_min']
            ))
    
    # Professional styling with light background
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Pace (min/km)',
        height=450,
        hovermode='x unified',
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(
            text='PB Tracking',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center',
            pad=dict(t=20, b=20)
        ),
        xaxis=dict(title_font=dict(size=14, color='#34495e')),
        yaxis=dict(title_font=dict(size=14, color='#34495e')),
        legend=dict(font=dict(size=12)),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    
    return fig

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Running Analytics Dashboard", 
                style={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '40px',
                       'font-family': '"Open Sans", verdana, arial, sans-serif'}),
        
        # Control Panel
        html.Div([
            html.Div([
                html.Button('Refresh Data', id='refresh-btn', n_clicks=0,
                           style={'background-color': '#2196F3', 'color': 'white', 
                                  'border': 'none', 'padding': '12px 24px', 
                                  'border-radius': '6px', 'cursor': 'pointer',
                                  'font-family': '"Open Sans", verdana, arial, sans-serif',
                                  'font-size': '14px', 'font-weight': '500',
                                  'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
                                  'transition': 'all 0.2s ease'})
            ], style={'margin-bottom': '20px'}),
            
            html.Div([
                html.Label("Select Date Range:", 
                          style={'font-weight': 'bold', 'margin-right': '15px', 'color': '#2c3e50',
                                 'font-family': '"Open Sans", verdana, arial, sans-serif',
                                 'font-size': '14px'}),
                dcc.DatePickerRange(
                    id='date-range-picker',
                    start_date=date(2025, 6, 8),  # Default to June 8th
                    end_date=date.today(),        # Default to today
                    display_format='YYYY-MM-DD',
                    style={'font-family': '"Open Sans", verdana, arial, sans-serif',
                           'background-color': '#2196F3', 'color': 'white',
                           'border': 'none', 'border-radius': '6px',
                           'font-size': '14px', 'font-weight': '500'}
                )
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})
            
        ], style={'text-align': 'center', 'margin-bottom': '40px', 
                  'padding': '20px', 'background-color': '#f8f9fa', 
                  'border-radius': '8px', 'margin': '0 20px 40px 20px'}),
        
        # Charts - One per row for better visibility
        html.Div([
            dcc.Graph(id='weekly-volume-chart'),
        ], style={'margin-bottom': '40px'}),
        
        html.Div([
            dcc.Graph(id='pace-trend-chart'),
        ], style={'margin-bottom': '40px'}),
        
        html.Div([
            dcc.Graph(id='weather-impact-chart'),
        ], style={'margin-bottom': '40px'}),
        
        html.Div([
            dcc.Graph(id='pb-tracking-chart'),
        ]),
        
    ], style={'max-width': '1400px', 'margin': '0 auto', 'padding': '30px'})
])

@callback(
    [Output('weekly-volume-chart', 'figure'),
     Output('pace-trend-chart', 'figure'),
     Output('weather-impact-chart', 'figure'),
     Output('pb-tracking-chart', 'figure')],
    [Input('refresh-btn', 'n_clicks'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_dashboard(n_clicks, start_date, end_date):
    """Update all dashboard components based on date range"""
    # Load fresh data (from CSV only - no API calls)
    df = load_running_data()
    
    # Filter data based on selected date range
    if start_date and end_date:
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Create all charts with filtered data
    weekly_fig = create_weekly_volume_chart(df)
    pace_fig = create_pace_trend_chart(df)
    weather_fig = create_weather_impact_chart(df)
    pb_fig = create_pb_tracking_chart(df)
    
    return weekly_fig, pace_fig, weather_fig, pb_fig

# For deployment
server = app.server

if __name__ == '__main__':
    app.run(debug=True, port=8050)