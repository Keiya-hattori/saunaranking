import streamlit as st
import pandas as pd
import requests
import time
import os

# ページ設定は最初に行う必要があります
st.set_page_config(
    page_title="サウナランキング",
    page_icon="🧖",
    layout="centered"
)

# FastAPI エンドポイントのURL設定（ページ設定の後に実行）
API_BASE_URL = os.environ.get(
    "API_BASE_URL", 
    "https://saunaranking-ver2-fastapi.onrender.com"
)

# デバッグ情報（サイドバーに表示）
st.sidebar.write(f"API URL: {API_BASE_URL}")

# CSSでスタイルを調整
st.markdown("""
<style>
    .main {
        padding: 2rem;
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

@st.cache_data(ttl=600)  # 10分間キャッシュ
def get_sauna_ranking(endpoint="/api/ranking"):
    """FastAPIエンドポイントからランキングデータを取得"""
    try:
        # 現在のホストの同じポートにリクエスト
        url = f"{API_BASE_URL}{endpoint}"
        st.sidebar.info(f"Requesting: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # JSONデータをDataFrameに変換
        df = pd.DataFrame(response.json())
        
        if df.empty:
            return df
        
        # last_updatedをdatetime型に変換
        df['last_updated'] = pd.to_datetime(df['last_updated'])
        
        return df
    except requests.RequestException as e:
        st.error(f"APIからのデータ取得に失敗しました: {str(e)}")
        return pd.DataFrame()

def display_ranking(df, title):
    """ランキングを表示する関数"""
    if df.empty:
        st.warning(f"{title}のデータがありません。")
        return
    
    # 最終更新日時を表示
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
        'レビュー数': df['review_count']
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

def main():
    # タイトル
    st.markdown('<p class="sauna-title">🧖 サウナランキング</p>', unsafe_allow_html=True)
    
    # タブを作成
    tab1, tab2 = st.tabs(["穴場サウナ", "貸切サウナ"])
    
    with tab1:
        st.header("穴場サウナランキング")
        st.markdown("""
        サウナイキタイのレビューから「穴場」と評価されているサウナをランキング形式で紹介します。
        各サウナ名をクリックすると、サウナイキタイの詳細ページに移動できます。
        """)
        
        try:
            with st.spinner("穴場サウナのデータを取得中..."):
                df = get_sauna_ranking("/api/ranking")
            display_ranking(df, "穴場サウナ")
        except Exception as e:
            st.error(f"穴場サウナの表示中にエラーが発生しました: {str(e)}")
    
    with tab2:
        st.header("貸切サウナランキング")
        st.markdown("""
        サウナイキタイのレビューから「貸切」と評価されているサウナをランキング形式で紹介します。
        各サウナ名をクリックすると、サウナイキタイの詳細ページに移動できます。
        """)
        
        try:
            with st.spinner("貸切サウナのデータを取得中..."):
                df = get_sauna_ranking("/api/ranking/kashikiri")
            display_ranking(df, "貸切サウナ")
        except Exception as e:
            st.error(f"貸切サウナの表示中にエラーが発生しました: {str(e)}")
    
    # 補足情報
    st.markdown("""
    ---
    ### 📝 このランキングについて
    
    - 「穴場」「貸切」というキーワードを含むレビューの数を集計しています
    - データは15分ごとに更新されます（GitHub Actions による自動収集）
    - サウナ名をクリックすると、サウナイキタイの詳細ページが開きます
    """)

if __name__ == "__main__":
    main() 