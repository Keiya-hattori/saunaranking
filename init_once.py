from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func
from pathlib import Path

# DBパス設定
db_dir = Path("data")
db_dir.mkdir(exist_ok=True)
db_path = db_dir / "saunas.db"
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

# Baseクラス
Base = declarative_base()

# SaunaDB テーブル定義（ここで確実に定義）
class SaunaDB(Base):
    __tablename__ = "saunas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

# テーブル作成
Base.metadata.create_all(bind=engine)
print("✅ saunas テーブルが初期化されました！")
