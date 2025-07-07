# Strava Running Dashboard

A simple running analytics dashboard that connects to Strava's API to track training progress. 

Built while learning data analysis as part of my transition from Product Manager to Product Analyst.

![Dashboard](assets/dashboard_preview.png)

## Why I created this

I'm recently aimed to pick up running with some consistancy. I want to use this dashboard to:
- Track improvements
- Assist with goal setting

## What it does

Currently, this dashboard:
- Displays weekly running distance with training targets
- Displays pace trends by date with interactive HR data

## Tech stack

- **Python** for data processing
- **Plotly Dash** for the interactive dashboard
- **Pandas** for data manipulation
- **Strava API** for getting running data

## Getting started

You'll need a Strava account and Python installed.

1. Clone this repo
2. Install dependencies: `pip install dash plotly pandas requests`
3. Set up Strava API access at https://developers.strava.com
4. Copy `config_template.py` to `config.py` and add your credentials
5. Run `python strava_auth.py` to connect to Strava
6. Run `python fetch_activities.py` to get your data
7. Run `python dashboard.py` and open http://localhost:8050

## Project structure

- `strava_auth.py` - handles Strava OAuth
- `fetch_activities.py` - pulls and processes running data
- `dashboard.py` - main dashboard application
- `pace_analysis.py` - standalone analysis charts




