import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from models.sauna import SaunaBase
from urllib.parse import urljoin
import logging
import time
import os
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

class SaunaScraper:
    def __init__(self):
        self.base_url = "https://sauna-ikitai.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # 設定ファイルのパスを指定
        self.last_page_file = Path("data/last_page.txt")
        self.last_page_file.parent.mkdir(parents=True, exist_ok=True)
        
        # ページ間の待機時間（秒）
        self.wait_time = 3

    def _get_page_content(self, url: str) -> BeautifulSoup:
        """指定URLのページコンテンツを取得してBeautifulSoupオブジェクトを返す"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # デバッグ出力
            print("=== ステータスコード:", response.status_code)
            print("=== タイトル:", soup.title.text if soup.title else "タイトルなし")
            print("=== HTML冒頭 ===")
            print(soup.prettify()[:1000])  # 長すぎ防止

            return soup

        except requests.RequestException as e:
            logger.error(f"ページの取得に失敗しました: {e}")
            raise
    
    def scrape_sauna_reviews(self, target_url: str = None) -> List[SaunaBase]:
        """
        「穴場」キーワードを含むレビューページから、サウナ情報をスクレイピング

        Args:
            target_url: スクレイピング対象のURL（Noneの場合はself.base_urlを使用）

        Returns:
            List[SaunaBase]: サウナ情報のリスト
        """
        saunas = []
        url_to_scrape = target_url or self.base_url
        soup = self._get_page_content(url_to_scrape)
        print("🔗 アクセスしてるURL:", url_to_scrape)
        print("📄 HTML先頭1000文字:\n", soup.prettify()[:1000])
        try:
            # レビュー一覧の要素を取得
            review_items = soup.select(".p-postCard")
            print(f"review_items 件数: {len(review_items)}")  
            for item in review_items:
                try:
                    # サウナ名とURLを取得
                    name_link_element = item.select_one(".p-postCard_facility a")
                    
                    if name_link_element:
                        name = name_link_element.text.strip()
                        url = name_link_element.get("href")
                        
                        # URLが相対パスでなく完全URLになっているならそのまま使う
                        full_url = url if url.startswith("http") else urljoin(self.base_url, url)

                        # 各レビュー = 1カウントとして扱う
                        review_count = 1

                        sauna = SaunaBase(
                            name=name,
                            url=full_url,
                            review_count=review_count,
                            last_updated=datetime.now()
                        )
                        saunas.append(sauna)

                except Exception as e:
                    logger.error(f"サウナ情報の解析中にエラーが発生しました: {e}")
                    continue

        except Exception as e:
            logger.error(f"スクレイピング中にエラーが発生しました: {e}")
            raise

        return saunas
   
    def aggregate_saunas(self, sauna_list: List[SaunaBase]) -> List[SaunaBase]:
        """同一URLのサウナを1つにまとめて、review_countを合算する"""
        aggregated = {}

        for sauna in sauna_list:
            key = str(sauna.url)
            if key in aggregated:
                aggregated[key].review_count += sauna.review_count
            else:
                # copyしないと元のオブジェクトを再利用することになるので deepcopyでも可
                aggregated[key] = SaunaBase(
                    name=sauna.name,
                    url=sauna.url,
                    review_count=sauna.review_count,
                    last_updated=sauna.last_updated
                )

        return list(aggregated.values())

    def get_review_count(self, sauna_url: str) -> int:
        """
        個別のサウナページからレビュー数を取得（必要な場合に実装）
        
        Args:
            sauna_url: サウナの詳細ページURL
            
        Returns:
            int: レビュー数
        """
        try:
            soup = self._get_page_content(sauna_url)
            # レビュー数を含む要素を取得（セレクタは実際のものに変更してください）
            review_element = soup.select_one(".review-count")
            if review_element:
                count_text = review_element.text.strip()
                return int(''.join(filter(str.isdigit, count_text)))
            return 0
        except Exception as e:
            logger.error(f"レビュー数の取得に失敗しました: {e}")
            return 0 

    def generate_page_url(self, page: int) -> str:
        """ページ番号からURLを生成"""
        return f"{self.base_url}/posts?keyword=穴場&page={page}&prefecture[0]=tokyo"

    def load_last_scraped_page(self) -> int:
        """前回スクレイピングした最後のページ番号を読み込む"""
        try:
            if self.last_page_file.exists():
                with open(self.last_page_file, "r") as f:
                    return int(f.read().strip())
            return 1
        except Exception as e:
            logger.error(f"前回のページ情報の読み込みに失敗しました: {e}")
            return 1

    def save_last_scraped_page(self, page: int) -> None:
        """次回のスタートページ番号を保存"""
        try:
            with open(self.last_page_file, "w") as f:
                f.write(str(page))
            logger.info(f"次回の開始ページ（{page}）を保存しました")
        except Exception as e:
            logger.error(f"ページ情報の保存に失敗しました: {e}")

    def scrape_multiple_pages(self, start_page: int, num_pages: int = 1) -> List[SaunaBase]:
        """
        指定したページ数分のサウナ情報をスクレイピング

        Args:
            start_page: 開始ページ番号
            num_pages: スクレイピングするページ数（デフォルト3）

        Returns:
            List[SaunaBase]: 収集したサウナ情報のリスト
        """
        all_saunas = []
        end_page = start_page + num_pages

        for page in range(start_page, end_page):
            try:
                logger.info(f"ページ {page} のスクレイピングを開始します")
                url = self.generate_page_url(page)
                page_saunas = self.scrape_sauna_reviews(url)
                all_saunas.extend(page_saunas)
                
                # 最後のページ以外で待機
                if page < end_page - 1:
                    logger.info(f"{self.wait_time}秒待機します...")
                    time.sleep(self.wait_time)

            except Exception as e:
                logger.error(f"ページ {page} のスクレイピングに失敗しました: {e}")
                break

        return all_saunas

    def run_scheduled_scraping(self, num_pages: int = 3) -> List[SaunaBase]:
        """
        前回の続きから指定ページ数分のスクレイピングを実行

        Args:
            num_pages: スクレイピングするページ数（デフォルト3）

        Returns:
            List[SaunaBase]: 収集したサウナ情報のリスト
        """
        # 前回の続きのページを読み込む
        start_page = self.load_last_scraped_page()
        logger.info(f"ページ {start_page} からスクレイピングを開始します")

        # スクレイピングを実行
        saunas = self.scrape_multiple_pages(start_page, num_pages)
        print(f"取得したサウナ数: {len(saunas)}") 

        aggregated_saunas = self.aggregate_saunas(saunas)
        print(f"集約後サウナ数: {len(aggregated_saunas)}")

        # 次回の開始ページを保存
        next_start_page = start_page + num_pages
        self.save_last_scraped_page(next_start_page)

        return saunas 