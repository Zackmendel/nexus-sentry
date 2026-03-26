import requests
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURATION ---
API_KEY = "2ce8fb9fe87878fea88aedf3e56584a0876f129c6bda4fcc979eb64048e33386"
FILENAME = "btc_hourly_history.csv"
INSTRUMENT = "BTC-USD"

def get_last_timestamp_from_csv(filename):
    """
    Reads the existing CSV and finds the most recent timestamp.
    """
    if not os.path.exists(filename):
        return None
    
    try:
        # 16MB is small enough to read the whole file to ensure we have the true max
        df = pd.read_csv(filename)
        if df.empty:
            return None
        
        df['Date'] = pd.to_datetime(df['Date'])
        return int(df['Date'].max().timestamp())
    except Exception as e:
        print(f"Error reading existing file: {e}")
        return None

def fetch_and_sync_hourly(api_key, filename, instrument="BTC-USD"):
    # 1. Determine where to start
    last_known_ts = get_last_timestamp_from_csv(filename)
    now_ts = int(time.time())
    
    if last_known_ts:
        print(f"Found existing data. Resuming from: {datetime.fromtimestamp(last_known_ts)}")
        start_ts = last_known_ts
    else:
        print("No existing data found. Starting from full history (2010)...")
        start_ts = int(datetime(2010, 1, 1).timestamp())

    if start_ts >= now_ts - 3600:
        print("Data is already up to date.")
        return

    # 2. Fetch forward in batches
    base_url = "https://data-api.coindesk.com/index/cc/v1/historical/hours"
    limit = 2000
    current_max_ts = start_ts
    
    params = {
        "market": "cadli",
        "instrument": instrument,
        "limit": limit,
        "fill": "true",
        "apply_mapping": "true",
        "response_format": "JSON",
        "api_key": api_key
    }

    print(f"Starting update: {datetime.fromtimestamp(current_max_ts)} -> {datetime.fromtimestamp(now_ts)}")

    while current_max_ts < now_ts - 3600:
        # Calculate the next 'to_ts' (up to 2000 hours ahead)
        target_to_ts = min(current_max_ts + (limit * 3600), now_ts)
        params['to_ts'] = target_to_ts
        
        print(f"Fetching batch up to {datetime.fromtimestamp(target_to_ts)}...")
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code == 429:
                print("Rate limit hit. Pausing for 30 seconds...")
                time.sleep(30)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if 'Data' in data and len(data['Data']) > 0:
                batch = data['Data']
                
                # Filter for only NEW records to avoid overlap with existing file or previous batch
                fresh_batch = [x for x in batch if x['TIMESTAMP'] > current_max_ts]
                
                if not fresh_batch:
                    # Potential gap in API data? Jump forward to avoid infinite loop
                    print(f"No new data in this range. Skipping to {datetime.fromtimestamp(target_to_ts)}")
                    current_max_ts = target_to_ts
                    continue
                
                # Convert to DataFrame
                df_batch = pd.DataFrame(fresh_batch)
                df_batch['Date'] = pd.to_datetime(df_batch['TIMESTAMP'], unit='s')
                
                # Standardize columns
                cols = ['Date', 'INSTRUMENT', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'TIMESTAMP']
                df_batch = df_batch[[c for c in cols if c in df_batch.columns]]
                
                # --- PERIODIC SAVE: Append immediately ---
                file_exists = os.path.exists(filename)
                df_batch.to_csv(filename, mode='a', index=False, header=not file_exists)
                
                # Update tracker
                current_max_ts = max(x['TIMESTAMP'] for x in fresh_batch)
                print(f"Saved {len(fresh_batch)} new hours. Progress: {datetime.fromtimestamp(current_max_ts)}")
                
                # Rate limit politeness
                time.sleep(1)
            else:
                print("No data returned by API for this range.")
                # Increment current_max_ts slightly to try next window
                current_max_ts = target_to_ts
                
        except Exception as e:
            print(f"Error during fetch: {e}")
            break

    print("Update Complete.")

if __name__ == "__main__":
    fetch_and_sync_hourly(API_KEY, FILENAME, INSTRUMENT)
