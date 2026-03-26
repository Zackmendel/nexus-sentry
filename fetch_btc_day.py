import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("COINDESK_API_KEY")  # <--- PASTE KEY HERE
FILENAME = "btc_all_time_history.csv"
INSTRUMENT = "BTC-USD"

def get_last_timestamp_from_csv(filename):
    """
    Reads the existing CSV and finds the most recent timestamp.
    Returns None if file doesn't exist or is empty.
    """
    if not os.path.exists(filename):
        return None
    
    try:
        df = pd.read_csv(filename)
        if df.empty:
            return None
        
        # Ensure Date is datetime object
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Get the maximum date
        last_date = df['Date'].max()
        
        # Convert to Unix timestamp (integer)
        return int(last_date.timestamp())
    except Exception as e:
        print(f"Error reading existing file: {e}")
        return None

def fetch_and_sync(api_key, filename, instrument="BTC-USD"):
    # 1. Determine where to stop
    last_known_ts = get_last_timestamp_from_csv(filename)
    
    if last_known_ts:
        print(f"Found existing data. Last run was: {datetime.fromtimestamp(last_known_ts).date()}")
        print("Checking for new data...")
    else:
        print("No existing data found. Starting FULL history download...")

    # 2. API Setup
    base_url = "https://data-api.coindesk.com/index/cc/v1/historical/days"
    limit = 2000
    new_records = []
    
    # Start fetching from "Now"
    current_to_ts = int(time.time())
    fetching = True
    
    params = {
        "market": "cadli",
        "instrument": instrument,
        "limit": limit,
        "fill": "true",
        "apply_mapping": "true",
        "response_format": "JSON",
        "api_key": api_key
    }

    while fetching:
        # Update the 'to_ts' parameter
        params['to_ts'] = current_to_ts
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'Data' in data and len(data['Data']) > 0:
                batch = data['Data']
                earliest_batch_ts = min(entry['TIMESTAMP'] for entry in batch)
                
                # --- LOGIC: CHECK FOR OVERLAP ---
                # If we have a last_known_ts, we need to see if this batch overlaps with it
                if last_known_ts:
                    # Filter: Keep only records NEWER than last_known_ts
                    fresh_batch = [x for x in batch if x['TIMESTAMP'] > last_known_ts]
                    
                    if len(fresh_batch) < len(batch):
                        # We found the overlap!
                        # 1. Add the fresh data
                        new_records.extend(fresh_batch)
                        print(f"Synced {len(fresh_batch)} new days. Caught up to existing data.")
                        fetching = False # Stop the loop
                    else:
                        # Whole batch is new, keep going backwards
                        new_records.extend(batch)
                        print(f"Retrieved {len(batch)} days... going back further.")
                        # Prepare next jump back
                        current_to_ts = earliest_batch_ts - 86400
                
                # --- LOGIC: FULL DOWNLOAD ---
                else:
                    new_records.extend(batch)
                    print(f"Retrieved {len(batch)} days (Earliest: {datetime.fromtimestamp(earliest_batch_ts).date()})")
                    current_to_ts = earliest_batch_ts - 86400
                    
                    # Safety break for full history (prevent infinite loops on bad data)
                    if datetime.fromtimestamp(earliest_batch_ts).year < 2010:
                        fetching = False

            else:
                print("No more data available from API.")
                fetching = False
                
        except Exception as e:
            print(f"Error during fetch: {e}")
            fetching = False

    # 3. Save / Merge Data
    if new_records:
        new_df = pd.DataFrame(new_records)
        new_df['Date'] = pd.to_datetime(new_df['TIMESTAMP'], unit='s')
        
        # Standardize columns
        cols = ['Date', 'INSTRUMENT', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'TIMESTAMP']
        new_df = new_df[[c for c in cols if c in new_df.columns]]

        if os.path.exists(filename) and last_known_ts:
            # APPEND MODE
            # We read the old file again to append cleanly
            old_df = pd.read_csv(filename)
            old_df['Date'] = pd.to_datetime(old_df['Date'])
            
            # Combine
            final_df = pd.concat([old_df, new_df])
            print(f"Appending {len(new_df)} new rows to existing file.")
        else:
            # NEW FILE MODE
            final_df = new_df
            print(f"Creating new file with {len(new_df)} rows.")

        # Final Cleanup: Sort and Deduplicate
        final_df = final_df.sort_values(by='Date').drop_duplicates(subset=['Date'], keep='last')
        
        # Save
        final_df.to_csv(filename, index=False)
        print("Update Complete.")
    else:
        print("File is already up to date. No new records found.")

# --- RUN ---
fetch_and_sync(API_KEY, FILENAME, INSTRUMENT)