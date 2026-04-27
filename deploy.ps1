$PROJECT_ID = "lifbq-407915"
$REGION = "us-central1"
$FUNCTION_NAME = "shipbob-fulfillment-daily-sync"

Write-Host "Deploying Shipbob Fulfillment Sync Cloud Function..."
gcloud functions deploy $FUNCTION_NAME `
    --gen2 `
    --runtime=python311 `
    --region=$REGION `
    --source=. `
    --entry-point=shipbob_daily_sync `
    --trigger-http `
    --memory=512MB `
    --timeout=3600s `
    --set-secrets="SHIPBOB_PAT_4GVN=SHIPBOB_PAT_4GVN:latest,SHIPBOB_PAT_LIF=SHIPBOB_PAT_LIF:latest,SHIPBOB_PAT_GLO=SHIPBOB_PAT_GLO:latest" `
    --project=$PROJECT_ID

Write-Host "Deployment Complete! The function is now live."
