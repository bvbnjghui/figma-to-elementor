# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import random
import string

# 建立一個 Flask 應用程式實例
app = Flask(__name__)
# 將 CORS 套用到你的 app 上，允許所有來源的請求
CORS(app)

# --- 輔助函式 ---
def generate_elementor_id(length=7):
    """產生一個類似 Elementor 的隨機7位數小寫字母和數字 ID。"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# --- 核心轉換邏輯 (V5 - 修正 forEach 錯誤並強化 ID 生成) ---

def transform_node_to_element(node):
    """
    遞迴主控函式：判斷節點類型，並呼叫對應的轉換函式。
    """
    if not node:
        return None
        
    node_type = node.get('type')

    # 將可包含子元素的容器節點轉換為 Elementor 的 Section
    if node_type in ['FRAME', 'COMPONENT', 'INSTANCE']:
        column_elements = []
        if 'children' in node:
            for child_node in node['children']:
                child_element = transform_node_to_element(child_node)
                if child_element:
                    column_elements.append(child_element)
        
        column = {
            "id": generate_elementor_id(),
            "elType": "column",
            "isInner": False,
            "settings": {
                "_column_size": 100, # 預設為單欄
            },
            "elements": column_elements,
        }
        
        return {
            "id": generate_elementor_id(),
            "elType": "section",
            "isInner": False,
            "settings": {},
            "elements": [column],
        }

    # 將文字節點轉換為 Heading Widget
    elif node_type == 'TEXT':
        return {
            "id": generate_elementor_id(),
            "elType": "widget",
            "isInner": False,
            "widgetType": "heading",
            "settings": {
                "title": node.get('characters', '預設文字'),
            }
        }
    
    # 將矩形轉換為圖片 Widget
    elif node_type == 'RECTANGLE':
        return {
            "id": generate_elementor_id(),
            "elType": "widget",
            "isInner": False,
            "widgetType": "image",
            "settings": {
                "image": {
                    "url": "https://placehold.co/600x400/E2E8F0/AAAAAA?text=Image",
                    "id": ""
                }
            }
        }
    
    # 如果是不支援的類型，就返回 None
    return None


# --- API 端點 (Endpoint) 的定義 ---

@app.route("/")
def index():
    """建立一個根路徑，用來確認服務是否正常運行"""
    return "<h1>Figma-to-Elementor 轉換器已啟動！(v5)</h1><p>請使用 POST 請求到 /convert 端點來進行轉換。</p>"

@app.route("/convert", methods=['POST'])
def handle_conversion():
    """
    這是我們主要的 API 端點，負責接收請求並回傳轉換結果。
    """
    try:
        if not request.is_json:
            return jsonify({"error": "請求格式錯誤，請使用 application/json"}), 400

        data = request.get_json()
        api_token = data.get('figma_token')
        file_key = data.get('file_key')

        if not api_token or not file_key:
            return jsonify({"error": "請求中缺少 'figma_token' 或 'file_key'"}), 400

        # 1. 真實地呼叫 Figma API
        print(f"正在呼叫 Figma API，File Key: {file_key}")
        api_url = f"https://api.figma.com/v1/files/{file_key}"
        headers = {"X-Figma-Token": api_token}
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        figma_data = response.json()
        print("成功從 Figma API 獲取資料。")

        # 2. 執行轉換
        print("開始執行轉換...")
        target_canvas = figma_data.get('document', {}).get('children', [{}])[0]
        
        elementor_data_array = []
        if target_canvas.get('children'):
            for top_level_frame in target_canvas['children']:
                 section = transform_node_to_element(top_level_frame)
                 if section:
                     elementor_data_array.append(section)

        if not elementor_data_array:
             return jsonify({"error": "無法從 Figma 檔案中轉換出任何內容，檔案可能是空的。"}), 500
        
        # 3. 直接回傳純粹的元素陣列，以符合「貼上」功能的需求
        print("轉換成功，已產生 Elementor 元素陣列。")
        return jsonify(elementor_data_array)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_message = f"Figma API 錯誤: {status_code}"
        if status_code == 403:
            error_message = "Figma API 錯誤: 權限不足，請檢查你的 API Token。"
        elif status_code == 404:
            error_message = "Figma API 錯誤: 找不到檔案，請檢查你的 File Key。"
        print(f"錯誤: {error_message}")
        return jsonify({"error": error_message}), status_code
        
    except requests.exceptions.RequestException as e:
        print(f"錯誤: 無法連接到 Figma API。 {e}")
        return jsonify({"error": f"網路錯誤: 無法連接到 Figma API。"}), 503

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"錯誤: 解析 Figma 回應失敗。 {e}")
        return jsonify({"error": "解析 Figma 資料結構失敗，請確認檔案內容是否正確或不是空的。"}), 500

    except Exception as e:
        print(f"發生未預期的伺服器錯誤: {e}")
        return jsonify({"error": "發生未預期的伺服器錯誤，請稍後再試。"}), 500


# --- 讓服務在本機和 Cloud Run 上都能運行的設定 ---
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
