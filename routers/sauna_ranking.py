from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from services.scraper import SaunaScraper
from database.db import get_db
from crud import bulk_upsert_saunas, get_sauna_ranking
from models.database import ScrapingState, SaunaDB, SaunaKashikiriDB
from models.sauna import SaunaRanking, SaunaRankingKashikiri
from typing import Dict, List
import logging
from datetime import datetime
from pydantic import BaseModel

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()

# スクレイパーのインスタンスをグローバルに作成
# （リクエストごとに作成する必要はない）
sauna_scraper = SaunaScraper()

# ランキング用のレスポンスモデル
class SaunaRanking(BaseModel):
    name: str
    url: str
    review_count: int
    last_updated: datetime

    class Config:
        from_attributes = True

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

@router.get("/api/ranking", response_model=List[SaunaRanking])
async def get_ranking(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    サウナのランキングデータを取得するエンドポイント
    
    Args:
        limit: 取得する上位件数（デフォルト50件）
        db: データベースセッション
    
    Returns:
        List[SaunaRanking]: ランキングデータのリスト
    """
    try:
        # レビュー数の多い順にサウナを取得
        saunas = db.query(SaunaDB)\
            .order_by(SaunaDB.review_count.desc())\
            .limit(limit)\
            .all()
        
        if not saunas:
            return []
            
        return [
            SaunaRanking(
                name=sauna.name,
                url=sauna.url,
                review_count=sauna.review_count,
                last_updated=sauna.last_updated
            ) for sauna in saunas
        ]
        
    except Exception as e:
        logger.error(f"ランキングデータの取得に失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ranking data: {str(e)}"
        )

# デバッグ用のエンドポイント
@router.get("/api/ranking/debug")
async def debug_ranking(db: Session = Depends(get_db)):
    """ランキングデータの状態を確認するエンドポイント"""
    try:
        total_count = db.query(SaunaDB).count()
        latest = db.query(SaunaDB)\
            .order_by(SaunaDB.last_updated.desc())\
            .first()
        
        return {
            "total_saunas": total_count,
            "latest_update": latest.last_updated if latest else None,
            "database_status": "connected"
        }
    except Exception as e:
        return {
            "error": str(e),
            "database_status": "error"
        }

@router.post("/api/reset-database")
async def reset_database(db: Session = Depends(get_db)):
    """データベースをリセットするエンドポイント（開発用）"""
    try:
        # 既存のデータを全て削除
        db.query(SaunaDB).delete()
        db.query(ScrapingState).delete()
        
        # スクレイピング状態を初期化
        initial_state = ScrapingState(key="last_page", value=1)
        db.add(initial_state)
        
        db.commit()
        
        return {
            "message": "データベースを正常にリセットしました",
            "status": "success",
            "saunas_count": db.query(SaunaDB).count(),
            "next_page": 1
        }
    except Exception as e:
        db.rollback()
        logger.error(f"データベースリセット中にエラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )

# ---- 穴場関連のエンドポイント ----

@router.get("/api/github-action-scraping")
async def run_github_action_scraping(db: Session = Depends(get_db)) -> Dict:
    """穴場キーワードのスクレイピングを実行"""
    try:
        scraped_saunas = sauna_scraper.run_scheduled_scraping(
            db, 
            num_pages=1,
            keyword="穴場",
            key_prefix="last_page"
        )
        
        saved_saunas = bulk_upsert_saunas(db, scraped_saunas, SaunaDB)
        
        return {
            "message": "穴場キーワードのスクレイピングが完了しました",
            "count": len(saved_saunas)
        }
        
    except Exception as e:
        logger.error(f"スクレイピング失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )

@router.get("/api/ranking", response_model=List[SaunaRanking])
async def get_ranking(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """穴場サウナのランキングデータを取得"""
    return get_sauna_ranking(db, limit, SaunaDB)

# ---- 貸切関連のエンドポイント ----

@router.get("/api/github-action-kashikiri")
async def run_github_action_kashikiri(db: Session = Depends(get_db)) -> Dict:
    """貸切キーワードのスクレイピングを実行"""
    try:
        scraped_saunas = sauna_scraper.run_scheduled_scraping(
            db, 
            num_pages=1,
            keyword="貸切",
            key_prefix="last_page_kashikiri"
        )
        
        # HttpUrlを文字列に変換
        for sauna in scraped_saunas:
            sauna.url = str(sauna.url)
        
        saved_saunas = bulk_upsert_saunas(db, scraped_saunas, SaunaKashikiriDB)
        
        return {
            "message": "貸切キーワードのスクレイピングが完了しました",
            "count": len(saved_saunas)
        }
        
    except Exception as e:
        logger.error(f"貸切スクレイピング失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Kashikiri scraping failed: {str(e)}"
        )

@router.get("/api/ranking/kashikiri", response_model=List[SaunaRankingKashikiri])
async def get_kashikiri_ranking(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """貸切サウナのランキングデータを取得"""
    return get_sauna_ranking(db, limit, SaunaKashikiriDB)