from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db
import logging
from routers import sauna_ranking

# ロガーの設定
logger = logging.getLogger(__name__)

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# アプリケーション起動時にデータベースを初期化
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("データベースの初期化を開始します")
        init_db()
        logger.info("データベースの初期化が完了しました")
    except Exception as e:
        logger.error(f"データベースの初期化に失敗しました: {e}")
        raise

# サウナランキング関連のルーターを登録
app.include_router(sauna_ranking.router) 