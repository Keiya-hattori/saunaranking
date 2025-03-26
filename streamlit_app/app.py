import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="穴場サウナランキング",
    page_icon="🧖",
    layout="centered"
)

# CSSでスタイルを調整
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stDataFrame {
        font-size: 1.2rem;
    }
    .sauna-title {
        color: #FF4B4B;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .last-updated {
        color: #666;
        font-size: 0.9rem;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

def get_db_connection():
    # ✅ プロジェクトルート（app.pyの親の親）を基準にする
    BASE_DIR = Path(__file__).resolve().parent.parent
    DB_PATH = BASE_DIR / "data" / "saunas.db"

    if not DB_PATH.exists():
        st.error("データベースファイルが見つかりません！")
        st.stop()

    return sqlite3.connect(DB_PATH)

def get_sauna_ranking():
    """サウナランキングデータを取得"""
    conn = get_db_connection()
    query = """
    SELECT 
        name,
        url,
        review_count,
        last_updated
    FROM saunas 
    ORDER BY review_count DESC 
    LIMIT 50
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    # タイトル
    st.markdown('<p class="sauna-title">🧖 穴場サウナランキング</p>', unsafe_allow_html=True)
    
    # サブタイトル
    st.markdown("""
    サウナイキタイのレビューから「穴場」と評価されているサウナをランキング形式で紹介します。
    各サウナ名をクリックすると、サウナイキタイの詳細ページに移動できます。
    """)
    
    try:
        # ランキングデータ取得
        df = get_sauna_ranking()
        
        if df.empty:
            st.warning("ランキングデータがありません。")
            return
        
        # 最終更新日時を表示
        last_updated = df['last_updated'].max()
        st.markdown(
            f'<p class="last-updated">最終更新: {last_updated}</p>',
            unsafe_allow_html=True
        )
        
        # ランキング表示用にデータを加工
        df['rank'] = range(1, len(df) + 1)
        df['name_with_link'] = df.apply(
            lambda x: f'<a href="{x["url"]}" target="_blank">{x["name"]}</a>',
            axis=1
        )
        
        # 表示用のデータフレームを作成
        display_df = pd.DataFrame({
            '順位': df['rank'],
            'サウナ施設': df['name_with_link'],
            '穴場レビュー数': df['review_count']
        })
        
        # ランキング表示
        st.write(
            display_df.to_html(
                escape=False,
                index=False,
                classes=['ranking-table'],
                justify='center'
            ),
            unsafe_allow_html=True
        )
        
        # 補足情報
        st.markdown("""
        ---
        ### 📝 このランキングについて
        
        - 「穴場」というキーワードを含むレビューの数を集計しています
        - データは定期的に更新されます（GitHub Actions による自動収集）
        - サウナ名をクリックすると、サウナイキタイの詳細ページが開きます
        """)
        
    except Exception as e:
        st.error(f"データの取得中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 