import os
import json
import requests
import time
from google.cloud import bigquery
from datetime import datetime, timedelta

# GCP Configuration
PROJECT_ID = "lifbq-407915"
DATASET_ID = "shipbob"
# Maps Brand Name to the Environment Variable/Secret Name in GCP
BRAND_TOKEN_MAP = {
    "4gvn": "SHIPBOB_PAT_4GVN",
    "lif": "SHIPBOB_PAT_LIF",
    "glo": "SHIPBOB_PAT_GLO"
}

def shipbob_daily_sync(request):
    """
    Cloud Function entry point. 
    Triggered by Cloud Scheduler via HTTP POST every 24 hours.
    """
    client = bigquery.Client(project=PROJECT_ID)

    
    # 14-Day Lookback logic to catch late invoicing/status updates
    # This ensures we catch status updates and billing for orders created in the last 2 weeks
    lookback_date = (datetime.utcnow() - timedelta(days=14)).strftime('%Y-%m-%dT00:00:00')
    
    try:
        for brand, secret_env_var in BRAND_TOKEN_MAP.items():
            print(f"--- Starting Sync for Brand: {brand.upper()} ---", flush=True)
            
            # 1. Retrieve Token from Environment (Mapped from Secret Manager)
            token = os.getenv(secret_env_var)
            if not token:
                print(f"[ERROR] Environment variable {secret_env_var} not found. Skipping {brand}.")
                continue

            # 2. API Setup
            url = "https://api.shipbob.com/2026-01/order"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "StartDate": lookback_date,
                "Limit": 250,
                "Page": 1
            }
            
            all_fresh_rows = []
            page = 1
            
            # 3. Fetch from ShipBob with Pagination support
            while True:
                try:
                    print(f"  Fetching {brand} page {page}...", flush=True)
                    resp = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if resp.status_code != 200:
                        print(f"  [ERROR] API {resp.status_code}: {resp.text}")
                        break
                        
                    orders = resp.json()
                    if not orders:
                        break
                    
                    for order in orders:
                        shipments = order.get('shipments', [])
                        if not shipments:
                            all_fresh_rows.append({
                                "order_id": str(order['id']),
                                "order_number": str(order.get('order_number') or ''),
                                "status": order.get('status'),
                                "purchase_date": order.get('purchase_date'),
                                "created_date": order.get('created_date'),
                                "shipment_id": None,
                                "shipment_status": None,
                                "invoice_amount": 0.0,
                                "ingested_at": datetime.utcnow().isoformat()
                            })
                        else:
                            for s in shipments:
                                all_fresh_rows.append({
                                    "order_id": str(order['id']),
                                    "order_number": str(order.get('order_number') or ''),
                                    "status": order.get('status'),
                                    "purchase_date": order.get('purchase_date'),
                                    "created_date": order.get('created_date'),
                                    "shipment_id": str(s.get('id')),
                                    "shipment_status": s.get('status'),
                                    "invoice_amount": float(s.get('invoice_amount') or 0.0),
                                    "ingested_at": datetime.utcnow().isoformat()
                                })
                    
                    # Pagination using page increments
                    if len(orders) < 250:
                        break
                    
                    page += 1
                    params["Page"] = page
                    
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  [EXCEPTION] API Pull: {e}")
                    break

            # 4. Upsert into BigQuery (Delete then Insert)
            if all_fresh_rows:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.{brand}_fulfillment_cost"
                
                # Extract IDs to delete as strings to match BigQuery schema
                order_ids = list(set([str(row['order_id']) for row in all_fresh_rows]))
                
                # Run deletion query natively with safe array formatting
                ids_tuple = str(order_ids).replace('[', '(').replace(']', ')')
                if len(order_ids) == 1:
                    ids_tuple = f"('{order_ids[0]}')" # Fix for single item tuple formatting
                
                delete_query = f"DELETE FROM `{table_id}` WHERE order_id IN {ids_tuple}"
                client.query(delete_query).result()
                print(f"  Cleared {len(order_ids)} existing records for deduplication.")
                
                # Load new data
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                    autodetect=False # Use fixed schema to prevent autodetection errors
                )
                client.load_table_from_json(all_fresh_rows, table_id, job_config=job_config).result()
                print(f"  SUCCESS: Ingested {len(all_fresh_rows)} shipment records for {brand}.", flush=True)
            else:
                print(f"  INFO: No shipments found for {brand} in the lookback window.")

        return "Sync Complete"
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return f"Error: {str(e)}"
