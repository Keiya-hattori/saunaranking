from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from typing import List, Optional, Type, Any
from datetime import datetime
from models.database import SaunaDB, SaunaKashikiriDB
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


def bulk_upsert_saunas(db: Session, saunas: List[SaunaBase], db_model: Type[Any] = SaunaDB) -> List[Any]:
    """
    複数のサウナ情報をまとめて追加または更新
    
    Args:
        db: データベースセッション
        saunas: 保存するサウナ情報のリスト
        db_model: 保存先のモデルクラス（デフォルトはSaunaDB）
        
    Returns:
        List: 保存されたレコードのリスト
    """
    try:
        updated_saunas = []
        
        for sauna in saunas:
            # 既存のレコードを検索
            stmt = select(db_model).where(db_model.url == sauna.url)
            existing = db.execute(stmt).scalar_one_or_none()
            
            if existing:
                # 既存レコードの更新
                existing.review_count += sauna.review_count
                existing.last_updated = sauna.last_updated
                db_sauna = existing
            else:
                # 新規レコードの作成
                db_sauna = db_model(
                    name=sauna.name,
                    url=sauna.url,
                    review_count=sauna.review_count,
                    last_updated=sauna.last_updated
                )
                db.add(db_sauna)
            
            updated_saunas.append(db_sauna)
            db.flush()

        # 全ての処理が成功したらコミット
        db.commit()
        return updated_saunas

    except Exception as e:
        logger.error(f"一括保存中にエラーが発生: {e}")
        db.rollback()
        raise

def get_sauna_ranking(db: Session, limit: int = 50, db_model: Type[Any] = SaunaDB) -> List[Any]:
    """
    レビュー数の多い順にサウナをランキング取得
    """
    return db.query(db_model)\
        .order_by(db_model.review_count.desc())\
        .limit(limit)\
        .all() 