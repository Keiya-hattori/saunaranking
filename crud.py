from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from typing import List, Optional
from datetime import datetime
from models.database import SaunaDB
from models.sauna import SaunaBase
import logging

logger = logging.getLogger(__name__)

def get_sauna_by_name(db: Session, name: str) -> Optional[SaunaDB]:
    return db.query(SaunaDB).filter(SaunaDB.name == name.strip()).first()


def upsert_sauna(db: Session, sauna: SaunaBase) -> SaunaDB:
    db_sauna = get_sauna_by_name(db, sauna.name)

    if db_sauna:
        db_sauna.review_count += sauna.review_count
        db_sauna.last_updated = datetime.now()
    else:
        db_sauna = SaunaDB(
            name=sauna.name,
            url=str(sauna.url),
            review_count=sauna.review_count,
            last_updated=datetime.now()
        )
        db.add(db_sauna)
    
    return db_sauna


def bulk_upsert_saunas(db: Session, saunas: List[SaunaBase]) -> List[SaunaDB]:
    """
    複数のサウナ情報をまとめて追加または更新
    """
    try:
        updated_saunas = []
        
        for sauna in saunas:
            # UPSERT処理（merge使用）
            stmt = select(SaunaDB).where(SaunaDB.url == sauna.url)
            existing = db.execute(stmt).scalar_one_or_none()
            
            if existing:
                # 既存レコードの更新
                existing.review_count += sauna.review_count
                existing.last_updated = sauna.last_updated
                db_sauna = existing
            else:
                # 新規レコードの作成
                db_sauna = SaunaDB(
                    name=sauna.name,
                    url=sauna.url,
                    review_count=sauna.review_count,
                    last_updated=sauna.last_updated
                )
                db.add(db_sauna)
            
            updated_saunas.append(db_sauna)
            
            # 個別にフラッシュして問題があればすぐに検出
            db.flush()

        # 全ての処理が成功したらコミット
        db.commit()
        return updated_saunas

    except Exception as e:
        logger.error(f"一括保存中にエラーが発生: {e}")
        db.rollback()
        raise

def get_sauna_ranking(db: Session, limit: int = 10) -> List[SaunaDB]:
    """
    レビュー数の多い順にサウナをランキング取得

    Args:
        db: データベースセッション
        limit: 取得する上位件数

    Returns:
        List[SaunaDB]: ランキング順のサウナリスト
    """
    return db.query(SaunaDB)\
        .order_by(SaunaDB.review_count.desc())\
        .limit(limit)\
        .all() 