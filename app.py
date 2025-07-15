import dash
from dash import dcc, html, Input, Output
import dash_auth
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# CRITICAL: Expose server for deployment
server = app.server

# Password protection for portfolio/employer access
VALID_USERNAME_PASSWORD_PAIRS = {
    'runna': 'portfolio2025',
    'demo': 'strava123'
}
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

# Professional color palette - consistent with your dashboard
COLORS = {
    'dark_green': '#1B5E20',      # Recovery
    'light_green': '#4CAF50',     # General Aerobic
    'yellow': '#FFC107',          # Endurance
    'orange': '#FF9800',          # Lactate Threshold
    'red': '#F44336',             # VO2 Max
    'race_blue': '#2196F3',       # Primary blue
    'dark_blue': '#0D47A1',       # 10K PB line
    'grey': '#757575'             # Other
}

def load_running_data():
    """Load and prepare running data with absolute paths for deployment"""
    import os
    
    # Debug: Print current directory and files
    print("Current directory:", os.getcwd())
    print("Files in directory:", os.listdir('.'))
    
    try:
        # Try direct file names first (Railway should find them in root)
        df = pd.read_csv('classified_running_data.csv')
        print(f"Successfully loaded classified_running_data.csv with {len(df)} rows")
    except FileNotFoundError:
        print("classified_running_data.csv not found, trying running_data.csv")
        try:
            df = pd.read_csv('running_data.csv')
            df['run_type'] = 'General Aerobic'  # Default classification
            print(f"Successfully loaded running_data.csv with {len(df)} rows")
        except FileNotFoundError:
            print("No CSV files found, creating empty dataframe")
            return pd.DataFrame({
                'date': [], 'distance_km': [], 'pace_min_per_km': [], 'run_type': []
            })
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return pd.DataFrame({
            'date': [], 'distance_km': [], 'pace_min_per_km': [], 'run_type': []
        })
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        print(f"Data processed successfully, date range: {df['date'].min()} to {df['date'].max()}")
    
    return df

def create_weekly_volume_chart(df):
    """Weekly volume bar chart with race blue color"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="Weekly Volume")
        return fig
        
    df['week'] = df['date'].dt.to_period('W').dt.start_time
    weekly_data = df.groupby('week').agg({
        'distance_km': 'sum',
        'date': 'count'
    }).rename(columns={'date': 'runs_count'}).reset_index()
    
    fig = px.bar(weekly_data, x='week', y='distance_km',
                 title='Weekly Volume',
                 labels={'distance_km': 'Distance (km)', 'week': 'Week'},
                 hover_data=['runs_count'])
    
    fig.update_traces(marker_color=COLORS['race_blue'])
    
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center', pad=dict(t=20, b=20)),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    return fig

def create_pace_trend_chart(df):
    """Pace trends by run type with training intensity order"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="Pace Trends by Run Type")
        return fig
        
    run_type_colors = {
        'Recovery': COLORS['dark_green'],
        'General Aerobic': COLORS['light_green'],
        'Endurance': COLORS['yellow'],
        'Lactate Threshold': COLORS['orange'],
        'VO₂ Max Intervals': COLORS['red'],
        'Race': COLORS['race_blue'],
        'Other': COLORS['grey']
    }
    
    intensity_order = ['Recovery', 'General Aerobic', 'Endurance', 'Lactate Threshold', 'VO₂ Max Intervals', 'Race', 'Other']
    df['run_type'] = pd.Categorical(df['run_type'], categories=intensity_order, ordered=True)
    
    fig = px.scatter(df, x='date', y='pace_min_per_km',
                     color='run_type',
                     color_discrete_map=run_type_colors,
                     category_orders={'run_type': intensity_order},
                     hover_data=['distance_km', 'average_heartrate'],
                     title='Pace Trends by Run Type',
                     labels={'pace_min_per_km': 'Pace (min/km)', 'date': 'Date'})
    
    fig.update_yaxes(range=[3.5, None])
    fig.update_traces(
        hovertemplate='<b>Date:</b> %{x}<br><b>Pace:</b> %{y} min/km<br><b>Distance:</b> %{customdata[0]} km<br><b>Average Heart Rate:</b> %{customdata[1]} bpm<br><extra></extra>',
        marker=dict(size=12)
    )
    
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center', pad=dict(t=20, b=20)),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        legend=dict(font=dict(size=12)),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    return fig

def create_weather_impact_chart(df):
    """Weather impact bar chart by temperature bins"""
    if df.empty or 'feels_like_c' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No weather data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="Pace by Weather Conditions")
        return fig
        
    all_runs = df.dropna(subset=['feels_like_c'])
    
    if len(all_runs) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No weather data available for runs", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="Pace by Weather Conditions", 
                         plot_bgcolor='#f8f9fa', paper_bgcolor='#f8f9fa')
        return fig
    
    def get_temp_bin(temp):
        if temp < 5: return 'Cold'
        elif temp < 15: return 'Cool'
        elif temp < 25: return 'Warm'
        else: return 'Hot'
    
    all_runs['temp_bin'] = all_runs['feels_like_c'].apply(get_temp_bin)
    all_runs['week'] = all_runs['date'].dt.to_period('W').dt.start_time
    
    weekly_temp_data = all_runs.groupby(['week', 'temp_bin']).agg({
        'pace_min_per_km': 'mean',
        'date': 'count'
    }).rename(columns={'date': 'run_count'}).reset_index()
    
    temp_colors = {'Cold': '#1976D2', 'Cool': '#64B5F6', 'Warm': '#FF9800', 'Hot': '#F44336'}
    
    fig = px.bar(weekly_temp_data, x='week', y='pace_min_per_km', 
                 color='temp_bin', color_discrete_map=temp_colors,
                 title='Pace by Weather Conditions',
                 labels={'pace_min_per_km': 'Average Pace (min/km)', 'week': 'Week', 'temp_bin': 'Temperature'},
                 hover_data=['run_count'], barmode='group')
    
    fig.update_layout(
        height=450,
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center', pad=dict(t=20, b=20)),
        xaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        yaxis=dict(title=dict(font=dict(size=14, color='#34495e'))),
        legend=dict(font=dict(size=12), title=dict(text='Temperature')),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    return fig

def create_pb_tracking_chart(df):
    """PB tracking with 10K and 5K lines"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="PB Tracking")
        return fig
        
    if '5k_pace_min_per_km' not in df.columns and '10k_pace_min_per_km' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No best efforts data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=450, title="PB Tracking", 
                         plot_bgcolor='#f8f9fa', paper_bgcolor='#f8f9fa')
        return fig
    
    fig = go.Figure()
    
    # 10K PBs first in legend
    if '10k_pace_min_per_km' in df.columns:
        tenK_data = df[df['10k_pace_min_per_km'].notna()].copy()
        if len(tenK_data) > 0:
            tenK_data = tenK_data.sort_values('date')
            tenK_data['pb_pace'] = tenK_data['10k_pace_min_per_km'].cummin()
            tenK_data['race_time_min'] = tenK_data['pb_pace'] * 10
            
            fig.add_trace(go.Scatter(
                x=tenK_data['date'], y=tenK_data['pb_pace'],
                mode='lines+markers', name='10K PB',
                line=dict(color=COLORS['dark_blue'], width=3), marker=dict(size=8),
                hovertemplate='<b>10K PB</b><br>Date: %{x}<br>Pace: %{y:.2f} min/km<br>Time: %{customdata:.1f} minutes<br><extra></extra>',
                customdata=tenK_data['race_time_min']
            ))
    
    # 5K PBs second in legend
    if '5k_pace_min_per_km' in df.columns:
        fiveK_data = df[df['5k_pace_min_per_km'].notna()].copy()
        if len(fiveK_data) > 0:
            fiveK_data = fiveK_data.sort_values('date')
            fiveK_data['pb_pace'] = fiveK_data['5k_pace_min_per_km'].cummin()
            fiveK_data['race_time_min'] = fiveK_data['pb_pace'] * 5
            
            fig.add_trace(go.Scatter(
                x=fiveK_data['date'], y=fiveK_data['pb_pace'],
                mode='lines+markers', name='5K PB',
                line=dict(color=COLORS['race_blue'], width=3), marker=dict(size=8),
                hovertemplate='<b>5K PB</b><br>Date: %{x}<br>Pace: %{y:.2f} min/km<br>Time: %{customdata:.1f} minutes<br><extra></extra>',
                customdata=fiveK_data['race_time_min']
            ))
    
    fig.update_layout(
        xaxis_title='Date', yaxis_title='Pace (min/km)', height=450, hovermode='x unified',
        font=dict(size=13, family='"Open Sans", verdana, arial, sans-serif'),
        title=dict(text='PB Tracking', font=dict(size=18, color='#2c3e50'), x=0.5, xanchor='center', pad=dict(t=20, b=20)),
        xaxis=dict(title_font=dict(size=14, color='#34495e')),
        yaxis=dict(title_font=dict(size=14, color='#34495e')),
        legend=dict(font=dict(size=12)),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa'
    )
    return fig

# App layout - identical to your dashboard design
app.layout = html.Div([
    html.Div([
        html.H1("Strava Running Dashboard", 
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
                    start_date=date(2025, 6, 8),
                    end_date=date.today(),
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
        
        # Charts
        html.Div([dcc.Graph(id='weekly-volume-chart')], style={'margin-bottom': '40px'}),
        html.Div([dcc.Graph(id='pace-trend-chart')], style={'margin-bottom': '40px'}),
        html.Div([dcc.Graph(id='weather-impact-chart')], style={'margin-bottom': '40px'}),
        html.Div([dcc.Graph(id='pb-tracking-chart')]),
        
    ], style={'max-width': '1400px', 'margin': '0 auto', 'padding': '30px'})
])

@app.callback(
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
    df = load_running_data()
    
    if not df.empty and start_date and end_date:
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    return (
        create_weekly_volume_chart(df),
        create_pace_trend_chart(df),
        create_weather_impact_chart(df),
        create_pb_tracking_chart(df)
    )

# For deployment
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=False, host='0.0.0.0', port=port)