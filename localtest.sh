#!/bin/bash

# 當任何指令失敗時停止執行
set -e

echo "🚀 啟動本機測試環境..."

# 1. 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "⚠️ 找不到 .env 檔案！請確保根目錄下有 .env 並填入 GEMINI_API_KEY。"
    exit 1
fi

# 2. 啟動後端 (FastAPI)
echo "📡 正在啟動後端 (FastAPI) 於 http://127.0.0.1:8765 ..."
export PYTHONPATH=$PYTHONPATH:.
python3 -m backend.main > backend.log 2>&1 &
BACKEND_PID=$!

# 3. 啟動前端 (Vite)
echo "💻 正在啟動前端 (Vite) 於 http://localhost:5173 ..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 所有服務已啟動！"
echo "🔗 前端網址: http://localhost:5173"
echo "🔗 後端 API: http://127.0.0.1:8765"
echo ""
echo "📝 運行日誌已記錄在 backend.log 與 frontend.log"
echo "🛑 按下 [Ctrl+C] 可同時關閉前後端伺服器。"

# 定義清理函式，確保退出時殺掉進程
cleanup() {
    echo ""
    echo "🧹 正在關閉伺服器 (PIDs: $BACKEND_PID, $FRONTEND_PID)..."
    kill $BACKEND_PID || true
    kill $FRONTEND_PID || true
    echo "✨ 已成功關閉。"
    exit
}

# 捕捉 Ctrl+C (SIGINT)
trap cleanup SIGINT

# 持續等待背景進程
wait
