from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class SaunaBase(BaseModel):
    """サウナの基本情報を格納するベースモデル"""
    name: str = Field(..., description="サウナの名称")
    url: str = Field(..., description="サウナイキタイの詳細ページURL")
    review_count: int = Field(default=0, description="「穴場」キーワードを含むレビュー数")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="データの最終更新日時"
    )

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
    """ランキング表示用のモデル"""
    rank: int = Field(..., description="ランキング順位")
    sauna: SaunaBase

    class Config:
        from_attributes = True 