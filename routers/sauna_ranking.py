from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from services.scraper import SaunaScraper
from database.db import get_db
from crud import bulk_upsert_saunas
from models.database import ScrapingState, SaunaDB
from typing import Dict
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()

# スクレイパーのインスタンスをグローバルに作成
# （リクエストごとに作成する必要はない）
sauna_scraper = SaunaScraper()

@router.get("/api/github-action-scraping")
async def run_github_action_scraping(
    db: Session = Depends(get_db)
) -> Dict:
    """
    GitHub Actionsから呼び出されるスクレイピング実行とDB保存を行うエンドポイント
    
    Args:
        db: データベースセッション（FastAPIのDependsで自動注入）
    
    Returns:
        Dict: 実行結果を含むJSON
        {
            "message": str,
            "count": int,
            "current_page": int
        }
    
    Raises:
        HTTPException: スクレイピングまたはDB保存処理で失敗した場合
    """
    try:
        # スクレイピングを実行（DBセッションを渡す）
        scraped_saunas = sauna_scraper.run_scheduled_scraping(db, num_pages=3)
        
        # スクレイピングしたデータをDBに保存
        try:
            saved_saunas = bulk_upsert_saunas(db, scraped_saunas)
            
            # 現在のスクレイピング状態を取得
            stmt = select(ScrapingState).where(ScrapingState.key == "last_page")
            state = db.execute(stmt).scalar_one_or_none()
            
            # 成功レスポンスを返す
            return {
                "message": "Scraping and DB update completed successfully",
                "count": len(saved_saunas),
                "current_page": state.value if state else 1
            }
            
        except Exception as db_error:
            # DB保存時のエラーをログに記録
            logger.error(f"Database operation failed: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database operation failed: {str(db_error)}"
            )
            
    except Exception as scraping_error:
        # スクレイピング時のエラーをログに記録
        logger.error(f"Scraping failed: {str(scraping_error)}")
        
        # クライアントにエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(scraping_error)}"
        )

@router.get("/api/scraping-state")
async def get_scraping_state(db: Session = Depends(get_db)):
    """現在のスクレイピング状態を確認するエンドポイント"""
    try:
        stmt = select(ScrapingState).where(ScrapingState.key == "last_page")
        state = db.execute(stmt).scalar_one_or_none()
        
        # 現在のスクレイピング状態の詳細情報を返す
        return {
            "last_page": state.value if state else None,
            "updated_at": state.updated_at.isoformat() if state else None,
            "next_page": state.value + 1 if state else 1,  # 1ページずつスクレイピング
            "total_saunas": db.query(SaunaDB).count(),
            "last_scraping": state.updated_at.isoformat() if state else None
        }
    except Exception as e:
        logger.error(f"Failed to get scraping state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scraping state: {str(e)}"
        ) 
    
@router.post("/api/reset-scraping-state")
async def reset_scraping_state(db: Session = Depends(get_db)):
    """スクレイピング状態（last_page）を初期化するエンドポイント"""
    try:
        stmt = select(ScrapingState).where(ScrapingState.key == "last_page")
        state = db.execute(stmt).scalar_one_or_none()

        if state:
            state.value = 1
        else:
            state = ScrapingState(key="last_page", value=1)
            db.add(state)

        db.commit()
        return {"message": "Scraping state reset to page 1."}

    except Exception as e:
        logger.error(f"Failed to reset scraping state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset scraping state: {str(e)}"
        )