from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db, engine, Base
from models.database import SaunaDB  # 明示的にインポート
import logging
from routers import sauna_ranking

# ロガーの設定
logging.basicConfig(level=logging.INFO)
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
        # モデルを明示的にインポートした上でテーブル作成
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブルの作成が完了しました")
    except Exception as e:
        logger.error(f"データベースの初期化に失敗しました: {e}")
        # エラー詳細をログに出力
        import traceback
        logger.error(traceback.format_exc())

# サウナランキング関連のルーターを登録
app.include_router(sauna_ranking.router)

# 確認用のエンドポイント
@app.get("/init-db")
async def manual_init_db():
    """手動でDBを初期化するエンドポイント（開発用）"""
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "データベーステーブルが正常に作成されました"}
    except Exception as e:
        logger.error(f"テーブル作成エラー: {e}")
        return {"error": str(e)} 