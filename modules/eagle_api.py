import requests
import json
import os
from urllib.parse import unquote
from .util import load_image
from .debug_logger import debug_print


# デバッグモード（環境変数で制御）
DEBUG = os.getenv('EAGLE_DEBUG', 'false').lower() == 'true'
DEBUG_LIMIT = 5
MAX_FILE_SIZE = 768
QUALITY = 85

class EagleApi:
    def __init__(self):
        self.base_url = 'http://localhost:41595'

    def get_list(self, limit=200, offset=0, orderBy=None, keyword=None, ext=None, tags=None, folders=None):
        """
        画像一覧を取得
        Args:
            limit (int): 取得する画像の最大数
            folder_id (str, optional): 指定されたフォルダーIDの画像のみを取得
        """
        try:
            # URLパラメータを構築
            params = f'limit={limit}&offset={offset}'
            if orderBy:
                params += f'&orderBy={orderBy}'
            if keyword:
                params += f'&keyword={keyword}'
            if ext:
                params += f'&ext={ext}'
            if tags:
                params += f'&tags={tags}'
            if folders:
                params += f'&folders={folders}'
            
            url = f'{self.base_url}/api/item/list?{params}'
            debug_print(f"Requesting images from Eagle API with params: {params}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            debug_print(f"Eagle API response received. Status: {response.status_code}")

            if 'data' in data and isinstance(data['data'], list):
                if DEBUG:
                    debug_print(f"DEBUG MODE: Limiting results to {DEBUG_LIMIT} items")
                    data['data'] = data['data'][:DEBUG_LIMIT]
                debug_print(f"Processing {len(data['data'])} items")
                
                # starプロパティをintに変換
                for item in data['data']:
                    if 'star' in item:
                        try:
                            item['star'] = int(item['star']) if item['star'] is not None else 0
                        except (ValueError, TypeError):
                            item['star'] = 0
            else:
                debug_print("Unexpected data structure:", data)

            return data
        except requests.exceptions.RequestException as e:
            error_msg = f"Eagle API error: {str(e)}"
            debug_print(error_msg)
            if hasattr(response, 'text'):
                debug_print(f"Response content: {response.text}")
            return {"status": "error", "message": error_msg}

    def get_folder_list(self):
        """フォルダ一覧を取得"""
        try:
            response = requests.get(f'{self.base_url}/api/folder/list')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            debug_print(f"Eagle API error: {e}")
            return {"status": "error", "message": str(e)}

    def get_thumbnail_image(self, image_id):
        """
        指定したIDのサムネイル画像を取得して Base64で返す
        """
        try:
            response = requests.get(f"{self.base_url}/api/item/thumbnail?id={image_id}")
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'success' and 'data' in data:
                # URLエンコードされたパスをデコード
                decoded_path = unquote(data['data'])
                # ローカルファイルパスから画像を読み込む
                return load_image(decoded_path)
            else:
                debug_print(f"Unexpected response: {data}")
                return None
                
        except (requests.exceptions.RequestException, IOError) as e:
            debug_print(f"Error getting thumbnail image: {e}")
            return None

    def get_image(self, image_id, ext="png", max_file_size=MAX_FILE_SIZE, quality=QUALITY):
        """
        - 指定したIDのオリジナル画像を返す
        - サムネイルはオリジナルと同じフォルダにあり、`{ファイル名}_thumbnail.png` という名前なので、そこからオリジナルを取得する
        - サムネイルファイル名に `_thumbnail.png` が無ければオリジナルがサムネイルとして使われている
        - 拡張子は引数 ext を使う
        """
        try:
            response = requests.get(f"{self.base_url}/api/item/thumbnail?id={image_id}")
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'success' and 'data' in data:
                path = unquote(data['data'])
                if path.endswith('_thumbnail.png'):
                    # サムネイルの場合、オリジナルのパスを生成
                    # '_thumbnail.png' を削除してオリジナルの拡張子に変更
                    base_path = path[:-14]  # '_thumbnail.png' の長さ(14)を削除
                    original_path = f"{base_path}.{ext}"
                else:
                    # サムネイルが作られていない場合は、パスをそのまま使用
                    original_path = path
                # ローカルファイルパスから画像を読み込む
                return load_image(original_path, max_file_size, quality)
            else:
                debug_print(f"Unexpected response: {data}")
                return None
                
        except (requests.exceptions.RequestException, IOError) as e:
            debug_print(f"Error getting image: {e}")
            return None


    def get_image_info(self, image_id):
        """
        画像の詳細情報を取得
        しかし /item/list で取得できるものとほぼ同じ（？）なので今回は使わないのでは？
        """
        try:
            response = requests.get(f'{self.base_url}/api/item/info?id={image_id}')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            debug_print(f"Error getting image detail: {e}")
            return None

    def update_item(self, item_id: str, data: dict):
        """
        画像情報を更新する
        Args:
            item_id (str): 更新する画像のID
            data (dict): 更新するデータ（tags, annotation, url, starなど）
        """
        try:
            url = f'{self.base_url}/api/item/update'
            data['id'] = item_id

            if 'star' in data and isinstance(data['star'], (int, float)):
                data['star'] = str(data['star'])

            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            debug_print(f"Error updating item: {e}")
            return {"status": "error", "message": str(e)}

    def move_to_trash(self, item_ids: list):
        """
        指定したアイテムをゴミ箱に移動する
        Args:
            item_ids (list): 削除する画像のIDリスト
        """
        try:
            url = f'{self.base_url}/api/item/moveToTrash'
            data = {"itemIds": item_ids}

            debug_print(f"Moving items to trash: {item_ids}")
            response = requests.post(url, json=data)
            debug_print(f"Move to trash response: {response.status_code} {response.text}")
            response.raise_for_status()
            result = response.json()

            # レスポンス形式を正規化
            if "status" not in result:
                result["status"] = "success" if response.status_code == 200 else "error"

            return result
        except requests.exceptions.RequestException as e:
            debug_print(f"Error moving items to trash: {e}")
            return {"status": "error", "message": str(e)}

    def get_uncategorized_list(self, limit=200, offset=0):
        """
        未分類（フォルダなし）アイテムを取得
        Args:
            limit (int): 取得する画像の最大数
            offset (int): ページネーションオフセット
        """
        try:
            # 全アイテムを取得
            all_data = self.get_list(limit=10000, offset=0)
            if 'data' not in all_data or not isinstance(all_data['data'], list):
                return all_data

            # folders が空のアイテムのみ抽出
            uncategorized = [
                item for item in all_data['data']
                if not item.get('folders') or len(item['folders']) == 0
            ]

            debug_print(f"Uncategorized items: {len(uncategorized)} out of {len(all_data['data'])}")

            # ページネーション適用
            paginated = uncategorized[offset:offset + limit]
            return {"status": "success", "data": paginated}
        except Exception as e:
            debug_print(f"Error getting uncategorized list: {e}")
            return {"status": "error", "message": str(e)}

eagle_api = EagleApi()
