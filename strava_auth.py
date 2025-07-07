import requests
import json
import webbrowser
from config import CLIENT_ID, CLIENT_SECRET

def get_strava_tokens():
    # Open browser for authorization
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8050/auth&scope=read,activity:read_all"
    
    print("Opening browser for Strava authorization...")
    webbrowser.open(auth_url)
    
    print("\nAfter authorizing, copy the full redirect URL and paste it here:")
    redirect_url = input("Redirect URL: ").strip()
    
    # Extract authorization code
    code = redirect_url.split('code=')[1].split('&')[0]
    print(f"Got authorization code: {code[:10]}...")
    
    # Exchange code for tokens
    response = requests.post('https://www.strava.com/oauth/token', data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    })
    
    if response.status_code == 200:
        tokens = response.json()
        
        # Save tokens for later use
        with open('strava_tokens.json', 'w') as f:
            json.dump(tokens, f)
        
        print("Authentication successful!")
        print(f"Access token saved: {tokens['access_token'][:20]}...")
        
        # Test the connection
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        athlete = requests.get('https://www.strava.com/api/v3/athlete', headers=headers).json()
        print(f"Connected as: {athlete['firstname']} {athlete['lastname']}")
        
        return tokens
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_strava_tokens()