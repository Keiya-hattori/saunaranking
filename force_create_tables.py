# テーブル強制作成用のスクリプト
from sqlalchemy import inspect, MetaData, Table, Column, Integer, String, DateTime
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import text
from database.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_create_tables():
    """強制的にテーブルを作成"""
    try:
        # 接続テスト
        with engine.connect() as conn:
            logger.info("データベースに接続しました")
            
            # 既存のテーブルを確認
            inspector = inspect(engine)
            if 'saunas' in inspector.get_table_names():
                logger.info("saunasテーブルは既に存在します")
                return
            
            # SQLを直接実行してテーブルを作成
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS saunas (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                url VARCHAR UNIQUE NOT NULL,
                review_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("saunasテーブルを強制的に作成しました")
            
    except Exception as e:
        logger.error(f"テーブル作成中にエラーが発生: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    force_create_tables() 