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
            existing_tables = inspector.get_table_names()
            
            # saunasテーブルの作成
            if 'saunas' not in existing_tables:
                create_saunas_sql = """
                CREATE TABLE IF NOT EXISTS saunas (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    url VARCHAR UNIQUE NOT NULL,
                    review_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_saunas_sql))
                logger.info("saunasテーブルを作成しました")

            # saunas_kashikiriテーブルの作成
            if 'saunas_kashikiri' not in existing_tables:
                create_kashikiri_sql = """
                CREATE TABLE IF NOT EXISTS saunas_kashikiri (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    url VARCHAR UNIQUE NOT NULL,
                    review_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_kashikiri_sql))
                logger.info("saunas_kashikiriテーブルを作成しました")

            # scraping_stateテーブルの作成
            if 'scraping_state' not in existing_tables:
                create_state_sql = """
                CREATE TABLE IF NOT EXISTS scraping_state (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR UNIQUE NOT NULL,
                    value INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_state_sql))
                
                # 初期データの挿入
                init_state_sql = """
                INSERT INTO scraping_state (key, value)
                VALUES 
                    ('last_page', 1),
                    ('last_page_kashikiri', 1)
                ON CONFLICT (key) DO NOTHING;
                """
                conn.execute(text(init_state_sql))
                logger.info("scraping_stateテーブルを作成し、初期データを挿入しました")
            
            conn.commit()
            logger.info("全てのテーブル作成が完了しました")
            
    except Exception as e:
        logger.error(f"テーブル作成中にエラーが発生: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    force_create_tables() 