# 📦 Shipbob Fulfillment Sync

## Overview
This Google Cloud Function is responsible for the daily synchronization of fulfillment data from ShipBob into our data warehouse. It processes order shipments across multiple brands and ensures that BigQuery remains accurate for financial reconciliation and inventory reporting.

## 🔗 Cloud Function Details
* **Entry Point Function:** `shipbob_daily_sync(request)`
* **Trigger URL:** `https://us-central1-lifbq-407915.cloudfunctions.net/shipbob-fulfillment-daily-sync`
* **GCP Region:** `us-central1`
* **GCP Project:** `lifbq-407915`

## 🚀 How it Works
1. **Trigger:** The function is invoked via an HTTP trigger (usually fired by Google Cloud Scheduler on a daily cadence).
2. **Extraction:** It authenticates and fetches raw shipment/fulfillment statuses from ShipBob APIs.
3. **Ingestion:** The processed data is loaded directly into Google BigQuery for downstream use in Retool and Tableau.

## 📁 Repository Structure
* `main.py` - Contains the primary Cloud Function logic.
* `SHIPBOB_PIPELINE_DOCUMENTATION.txt` - Historical pipeline configurations and notes.

## 🛠️ Deployment

This project uses a PowerShell script to automate the deployment to Google Cloud Functions (Gen 2).

**To deploy updates:**
1. Open your terminal or PowerShell.
2. Ensure you are authenticated with Google Cloud (`gcloud auth login`).
3. Run the deployment script:
   ```powershell
   ./deploy.ps1

