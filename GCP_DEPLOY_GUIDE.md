# Google Cloud 部署指南 (Cloud Run + Cloud SQL)

此指南將引導您完成「個人 AI 工作助理」的雲端部署流程。

## 1. 準備工作
請確保您已安裝 [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) 並完成初始化：
```bash
gcloud auth login
gcloud config set project [ainotebook-493613]
```

## 2. 建立 Cloud SQL (PostgreSQL)
1.  建立執行個體：
    ```bash
    gcloud sql instances create ai-assistant-db \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=asia-east1
    ```
2.  設定資料庫與密碼：
    ```bash
    gcloud sql databases create assistant_db --instance=ai-assistant-db
    gcloud sql users set-password postgres --instance=ai-assistant-db --password=[YOUR_DB_PASSWORD]
    ```

## 3. 建立 Cloud Storage (持久化儲存)
建立一個 Bucket 用於存放 ChromaDB 與上傳檔案：
```bash
gsutil mb -l asia-east1 gs://[YOUR_PROJECT_ID]-ai-data
```

## 4. 部署後端 (Backend)
1.  建立並推送 Docker 映像檔：
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/ai-backend . -f backend/Dockerfile
    ```
2.  部署至 Cloud Run：
    ```bash
    gcloud run deploy ai-backend \
        --image gcr.io/[YOUR_PROJECT_ID]/ai-backend \
        --platform managed \
        --region asia-east1 \
        --allow-unauthenticated \
        --add-cloudsql-instances [YOUR_PROJECT_ID]:asia-east1:ai-assistant-db \
        --update-env-vars DATABASE_URL="postgresql://postgres:[YOUR_DB_PASSWORD]@/assistant_db?host=/cloudsql/[YOUR_PROJECT_ID]:asia-east1:ai-assistant-db" \
        --update-env-vars GEMINI_API_KEY=[YOUR_GEMINI_KEY] \
        --update-env-vars DATA_DIR="/mnt/data" \
        --execution-environment gen2 \
        --add-volume name=ai-data,type=cloud-storage,bucket=[YOUR_PROJECT_ID]-ai-data \
        --add-volume-mount volume=ai-data,mount-path=/mnt/data
    ```
    *記下部署後的後端 URL (例如 `https://ai-backend-xxxxx.a.run.app`)。*

## 5. 部署前端 (Frontend)
1.  建立並推送前端 Docker 映像檔 (需傳入後端 URL)：
    ```bash
    gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/ai-frontend \
        --build-arg VITE_API_BASE_URL="https://[YOUR_BACKEND_URL]/api" . -f frontend/Dockerfile
    ```
2.  部署至 Cloud Run：
    ```bash
    gcloud run deploy ai-frontend \
        --image gcr.io/[YOUR_PROJECT_ID]/ai-frontend \
        --platform managed \
        --region asia-east1 \
        --allow-unauthenticated
    ```

## 6. 後續調整
-   **CORS**: 若遇到跨來源錯誤，請更新後端的 `allow_origins` 為前端的 Cloud Run URL。
-   **域名**: 您可以在 Google Cloud Console 為服務對應自訂網域。
