from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db, engine, Base
from models.database import SaunaDB  # 明示的にインポート
import logging
from routers import sauna_ranking
from force_create_tables import force_create_tables
from sqlalchemy import inspect
from sqlalchemy.sql import text

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

# 新しいエンドポイント
@app.get("/force-create-tables")
async def manual_force_create_tables():
    """強制的にテーブルを作成するエンドポイント"""
    try:
        force_create_tables()
        return {"message": "テーブルを強制的に作成しました"}
    except Exception as e:
        logger.error(f"強制テーブル作成エラー: {e}")
        return {"error": str(e)}

@app.get("/debug-db")
async def debug_database():
    """データベース接続のデバッグ情報を返す"""
    try:
        # 接続テスト
        result = {}
        
        # エンジン情報
        result["engine_url"] = str(engine.url).replace(":********@", ":****@")
        
        # テーブル一覧
        inspector = inspect(engine)
        result["tables"] = inspector.get_table_names()
        
        # テーブル作成テスト
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            result["connection_test"] = "成功"
            
            # スキーマ確認
            schema_query = "SELECT schema_name FROM information_schema.schemata"
            schemas = [row[0] for row in conn.execute(text(schema_query))]
            result["schemas"] = schemas
            
            # 現在のユーザーと権限
            user_query = "SELECT current_user, current_database()"
            user_info = conn.execute(text(user_query)).fetchone()
            result["current_user"] = user_info[0]
            result["current_database"] = user_info[1]
            
        return result
    except Exception as e:
        logger.error(f"データベースデバッグエラー: {e}")
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        } 