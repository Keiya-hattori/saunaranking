from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# PostgreSQL接続URLを環境変数から取得
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sauna_db"  # デフォルト値
)

# Renderのデータベース接続文字列対応
# "postgres://" で始まる場合 "postgresql://" に置換
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# エンジンの作成
engine = create_engine(DATABASE_URL)

# セッションローカルの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()

def get_db():
    """
    FastAPIのDependencyとして使用するデータベースセッションを提供する

    Yields:
        Session: データベースセッション

    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = crud.get_items(db)
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    データベースの初期化（テーブルの作成）を行う
    
    注意: この関数はアプリケーション起動時に一度だけ実行する
    """
    from models.database import SaunaDB  # 循環インポートを避けるためここでインポート
    
    # テーブルが存在しない場合のみ作成
    Base.metadata.create_all(bind=engine) 