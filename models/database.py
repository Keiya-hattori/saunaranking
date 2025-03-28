from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SaunaDB(Base):
    """穴場キーワードを含むサウナモデル"""
    __tablename__ = "saunas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SaunaKashikiriDB(Base):
    """貸切キーワードを含むサウナモデル"""
    __tablename__ = "saunas_kashikiri"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ScrapingState(Base):
    """スクレイピングの状態を保存するモデル"""
    __tablename__ = "scraping_state"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)  # 例: "last_page"/"last_page_kashikiri"
    value = Column(Integer, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now()) 