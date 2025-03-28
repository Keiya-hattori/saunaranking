import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# FastAPI エンドポイントのURL
API_BASE_URL = "https://saunaranking-ver2-fastapi.onrender.com"

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
    .ranking-table {
        width: 100%;
        margin-top: 2rem;
    }
    .ranking-table th {
        background-color: #FF4B4B;
        color: white;
        padding: 1rem;
    }
    .ranking-table td {
        padding: 1rem;
        border-bottom: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

#@st.cache_data(ttl=660)  # 2分間キャッシュ
def get_sauna_ranking():
    """FastAPIエンドポイントからランキングデータを取得"""
    try:
        # まずヘルスチェックを実行してサービスを起動
        health_response = requests.get(f"{API_BASE_URL}/health",timeout=5)
        if health_response.status_code != 200:
            st.warning("APIサービスの起動中です。少々お待ちください...")
            time.sleep(5)  # 5秒待機
        
        # ランキングデータを取得
        response = requests.get(f"{API_BASE_URL}/api/ranking",timeout=10)
        response.raise_for_status()
        
        # JSONデータをDataFrameに変換
        df = pd.DataFrame(response.json())
        
        if df.empty:
            st.warning("ランキングデータがまだありません")
            return df
        
        # last_updatedをdatetime型に変換
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        return df
        
    except requests.RequestException as e:
        if "502" in str(e):
            st.warning("APIサービスが起動中です。30秒後に自動的に再試行します...")
            time.sleep(30)  # 30秒待機して再試行
            return get_sauna_ranking()  # 再帰的に再試行
        
        st.error(f"APIからのデータ取得に失敗しました: {str(e)}")
        return pd.DataFrame()

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
        with st.spinner("ランキングデータを取得中..."):
            df = get_sauna_ranking()
        
        if df.empty:
            st.warning("ランキングデータがありません。")
            return
        
        # 最終更新日時を表示（日本時間に変換して表示）
        last_updated = df['last_updated'].max()
        if last_updated:
            formatted_date = last_updated.strftime('%Y年%m月%d日 %H:%M')
            st.markdown(
                f'<p class="last-updated">最終更新: {formatted_date}</p>',
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
        - データは15分ごとに更新されます（GitHub Actions による自動収集）
        - サウナ名をクリックすると、サウナイキタイの詳細ページが開きます
        """)
        
    except Exception as e:
        st.error(f"データの表示中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 