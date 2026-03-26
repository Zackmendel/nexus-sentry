import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
API_KEY = os.getenv("COINDESK_API_KEY")
FILENAME = "btc_minutes_history.csv"
INSTRUMENT = "BTC-USD"

def check_and_fix_header(filename):
    """
    Ensures the CSV has the correct header. If missing, prepends it.
    """
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return
    
    header = "Date,INSTRUMENT,OPEN,HIGH,LOW,CLOSE,VOLUME,TIMESTAMP"
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
        
        if not first_line.startswith("Date"):
            print(f"Header missing in {filename}. Adding it...")
            temp_file = filename + ".tmp"
            with open(filename, 'r') as original:
                with open(temp_file, 'w') as target:
                    target.write(header + "\n")
                    for line in original:
                        target.write(line)
            os.replace(temp_file, filename)
            print("Header added successfully.")
    except Exception as e:
        print(f"Warning: Could not check/fix header: {e}")

def get_last_timestamp_from_csv(filename):
    """
    Finds the most recent timestamp by reading the last line of the file.
    This is much faster than loading the whole file into pandas.
    """
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return None
    
    try:
        # Seek to end and find last line
        with open(filename, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            # Start at end and look for newline
            offset = -1
            while abs(offset) < size:
                f.seek(offset, os.SEEK_END)
                if f.read(1) == b'\n':
                    # Found a newline, line starts after it
                    line = f.readline().decode().strip()
                    if line and not line.startswith('Date'):
                        parts = line.split(',')
                        if len(parts) >= 8: # Expecting at least 8 columns
                            return int(parts[-1]) # TIMESTAMP is usually last
                offset -= 1
            # If only one line (no newline at end or just header)
            f.seek(0)
            line = f.readline().decode().strip()
            if line and not line.startswith('Date'):
                parts = line.split(',')
                if len(parts) >= 8:
                    return int(parts[-1])
    except Exception as e:
        print(f"Note: Fast-read failed, falling back to pandas: {e}")
        try:
            df = pd.read_csv(filename, usecols=['TIMESTAMP'])
            if not df.empty:
                return int(df['TIMESTAMP'].max())
        except:
            pass
    return None

def fetch_and_sync_minutes(api_key, filename, instrument="BTC-USD"):
    # 0. Maintenance
    check_and_fix_header(filename)

    # 1. Determine where to start
    last_known_ts = get_last_timestamp_from_csv(filename)
    now_ts = int(time.time())
    
    if last_known_ts:
        print(f"Found existing data. Resuming from: {datetime.fromtimestamp(last_known_ts)}")
        start_ts = last_known_ts
    else:
        # Start from 2020 as requested by user in their manual edit
        print("Starting from 2020-01-01 per configuration...")
        start_ts = int(datetime(2020, 1, 1).timestamp())

    if start_ts >= now_ts - 60:
        print("Data is already up to date.")
        return

    # 2. Fetch forward in batches
    base_url = "https://data-api.coindesk.com/index/cc/v1/historical/minutes"
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

    while current_max_ts < now_ts - 60:
        target_to_ts = min(current_max_ts + (limit * 60), now_ts)
        params['to_ts'] = target_to_ts
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 429:
                print("Rate limit hit. Pausing for 60 seconds...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if 'Data' in data and len(data['Data']) > 0:
                batch = data['Data']
                fresh_batch = [x for x in batch if x['TIMESTAMP'] > current_max_ts]
                
                if not fresh_batch:
                    current_max_ts = target_to_ts
                    continue
                
                df_batch = pd.DataFrame(fresh_batch)
                df_batch['Date'] = pd.to_datetime(df_batch['TIMESTAMP'], unit='s')
                
                # Standardize columns
                cols = ['Date', 'INSTRUMENT', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'TIMESTAMP']
                df_batch = df_batch[[c for c in cols if c in df_batch.columns]]
                
                # Append to file
                file_exists = os.path.exists(filename)
                df_batch.to_csv(filename, mode='a', index=False, header=not file_exists)
                
                current_max_ts = max(x['TIMESTAMP'] for x in fresh_batch)
                print(f"Saved {len(fresh_batch)} new minutes. Last ts: {datetime.fromtimestamp(current_max_ts)}")
                
                time.sleep(0.5)
            else:
                current_max_ts = target_to_ts
                
        except Exception as e:
            print(f"Error during fetch: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    print("Update Complete.")

if __name__ == "__main__":
    fetch_and_sync_minutes(API_KEY, FILENAME, INSTRUMENT)

