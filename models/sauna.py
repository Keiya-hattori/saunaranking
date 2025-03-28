from datetime import datetime
from pydantic import BaseModel, Field

class SaunaBase(BaseModel):
    """サウナの基本情報を格納するベースモデル"""
    name: str
    url: str  # HttpUrlではなくstrを使用
    review_count: int
    last_updated: datetime

class SaunaCreate(SaunaBase):
    """サウナ情報作成時に使用するモデル"""
    pass

class SaunaInDB(SaunaBase):
    """データベースに保存されるサウナモデル"""
    id: int = Field(..., description="サウナの一意識別子")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="レコード作成日時"
    )

    class Config:
        from_attributes = True

class SaunaRanking(BaseModel):
    """ランキング表示用のモデル（穴場）"""
    name: str
    url: str  # HttpUrlではなくstrを使用
    review_count: int
    last_updated: datetime

    class Config:
        from_attributes = True

class SaunaRankingKashikiri(BaseModel):
    """ランキング表示用のモデル（貸切）"""
    name: str
    url: str  # HttpUrlではなくstrを使用
    review_count: int
    last_updated: datetime

    class Config:
        from_attributes = True 