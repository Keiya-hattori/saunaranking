from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# データベースファイルのパスを設定
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = Path("data")
DB_FILE = DB_DIR / "saunas.db"

# データベース保存用ディレクトリが存在しない場合は作成
DB_DIR.mkdir(parents=True, exist_ok=True)

# SQLiteのデータベースURL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# エンジンの作成
# check_same_thread=False は SQLite を使用する際の制限を解除するために必要
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

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