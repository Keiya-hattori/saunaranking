from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db, engine, get_db, Base
from models.database import SaunaDB  # 明示的にインポート
import logging
from routers import sauna_ranking
from force_create_tables import force_create_tables
from sqlalchemy import inspect
from sqlalchemy.sql import text
import time
from sqlalchemy.orm import Session
from services.scraper import SaunaScraper
import crud

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔇 SQLAlchemyのSQLログを抑制（ここを追加！）
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# スクレイピングのインスタンス作成
sauna_scraper = SaunaScraper()

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
        logger.info("アプリケーション起動 - データベース初期化チェック")
        inspector = inspect(engine)
        if 'saunas' not in inspector.get_table_names():
            logger.info("saunasテーブルが存在しないため作成します")
            force_create_tables()
        else:
            logger.info("saunasテーブルは既に存在します")
    except Exception as e:
        logger.error(f"起動時の初期化でエラー: {e}")

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

@app.get("/health")
async def health_check():
    """
    サービスの健康状態をチェックするエンドポイント
    データベース接続も確認する
    """
    try:
        # データベース接続チェック
        with engine.connect() as conn:
            # 簡単なクエリを実行
            result = conn.execute(text("SELECT 1")).scalar()
            
            # テーブルの存在確認
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            return {
                "status": "healthy",
                "database": "connected",
                "tables": tables,
                "timestamp": time.time()
            }
            
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Service unhealthy: {str(e)}"
        )

# スクレイピングエンドポイントにリトライロジックを追加
@app.get("/api/github-action-scraping")
async def run_github_action_scraping(db: Session = Depends(get_db)):
    """
    GitHub Actionsから呼び出されるスクレイピング実行エンドポイント
    リトライロジックを含む
    """
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            # テーブルの存在確認
            inspector = inspect(engine)
            if 'saunas' not in inspector.get_table_names():
                logger.info("saunasテーブルが存在しないため作成します")
                force_create_tables()
            
            # スクレイピングを実行
            scraped_saunas = sauna_scraper.run_scheduled_scraping()
            
            # DBに保存
            saved_saunas = crud.bulk_upsert_saunas(db, scraped_saunas)
            
            return {
                "message": "Scraping and DB update completed successfully",
                "count": len(saved_saunas)
            }
            
        except Exception as e:
            logger.error(f"試行 {attempt + 1}/{max_retries} 失敗: {e}")
            if attempt < max_retries - 1:
                logger.info(f"{retry_delay}秒後にリトライします...")
                time.sleep(retry_delay)
                continue
            raise HTTPException(
                status_code=500,
                detail=f"All retry attempts failed: {str(e)}"
            ) 