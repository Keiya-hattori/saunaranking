from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from services.scraper import SaunaScraper
from database.db import get_db
from crud import bulk_upsert_saunas
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
            "count": int
        }
    
    Raises:
        HTTPException: スクレイピングまたはDB保存処理で失敗した場合
    """
    try:
        # スクレイピングを実行（デフォルトで3ページ分）
        scraped_saunas = sauna_scraper.run_scheduled_scraping(num_pages=1)
        
        # スクレイピングしたデータをDBに保存
        try:
            saved_saunas = bulk_upsert_saunas(db, scraped_saunas)
            
            # 成功レスポンスを返す
            return {
                "message": "Scraping and DB update completed successfully",
                "count": len(saved_saunas)
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