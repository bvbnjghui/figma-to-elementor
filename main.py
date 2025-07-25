# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

# 建立一個 Flask 應用程式實例
app = Flask(__name__)
# 將 CORS 套用到你的 app 上，允許所有來源的請求
CORS(app)

# --- 核心轉換邏輯 (正式版本) ---

def transform_node_to_element(node):
    """
    遞迴主控函式：判斷節點類型，並呼叫對應的轉換函式。
    """
    if not node:
        return None
        
    node_type = node.get('type')
    element = None

    # 將可包含子元素的容器節點轉換為 Elementor 的 Section
    if node_type in ['FRAME', 'COMPONENT', 'INSTANCE', 'CANVAS']:
        section = {"elType": "section", "elements": []}
        column = {"elType": "column", "elements": []}
        
        if 'children' in node:
            for child_node in node['children']:
                child_element = transform_node_to_element(child_node)
                if child_element:
                    column['elements'].append(child_element)
        
        section['elements'].append(column)
        element = section

    # 將文字節點轉換為 Heading Widget
    elif node_type == 'TEXT':
        element = {
            "elType": "widget",
            "widgetType": "heading",
            "settings": {
                "title": node.get('characters', ''),
                # TODO: 增加顏色、字體大小等樣式轉換
            }
        }
    
    # 將矩形轉換為圖片 Widget (假設它是一個圖片佔位)
    elif node_type == 'RECTANGLE':
        element = {
            "elType": "widget",
            "widgetType": "image",
            "settings": {
                # TODO: 增加偵測 Rectangle 的 fills 是否為 IMAGE 的邏輯
                "image": {
                    "url": "https://placehold.co/600x400/E2E8F0/AAAAAA?text=Image",
                    "id": ""
                }
            }
        }
        
    if element:
        # 為每個元素加上唯一的 ID，這是 Elementor 的要求
        element['id'] = node.get('id', '')
    
    return element


# --- API 端點 (Endpoint) 的定義 ---

@app.route("/")
def index():
    """建立一個根路徑，用來確認服務是否正常運行"""
    return "<h1>Figma-to-Elementor 轉換器已啟動！</h1><p>請使用 POST 請求到 /convert 端點來進行轉換。</p>"

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
        
        response = requests.get(api_url, headers=headers, timeout=30) # 增加30秒超時
        response.raise_for_status()  # 如果 API 回傳 4xx 或 5xx 錯誤，會在此拋出例外
        
        figma_data = response.json()
        print("成功從 Figma API 獲取資料。")

        # 2. 執行轉換
        print("開始執行轉換...")
        # 我們假設要轉換的是檔案中的第一個畫布 (Canvas)
        target_canvas = figma_data.get('document', {}).get('children', [{}])[0]
        
        elementor_json = transform_node_to_element(target_canvas)
        if not elementor_json:
             return jsonify({"error": "無法從 Figma 檔案中轉換出任何內容，檔案可能是空的。"}), 500
        
        final_output = [elementor_json] # Elementor 的最終格式是一個陣列
        print("轉換成功。")

        # 3. 回傳成功的 JSON 結果
        return jsonify(final_output)

    except requests.exceptions.HTTPError as e:
        # 處理 Figma API 回傳的 HTTP 錯誤 (4xx, 5xx)
        status_code = e.response.status_code
        error_message = f"Figma API 錯誤: {status_code}"
        if status_code == 403:
            error_message = "Figma API 錯誤: 權限不足，請檢查你的 API Token。"
        elif status_code == 404:
            error_message = "Figma API 錯誤: 找不到檔案，請檢查你的 File Key。"
        print(f"錯誤: {error_message}")
        return jsonify({"error": error_message}), status_code
        
    except requests.exceptions.RequestException as e:
        # 處理網路連線層級的錯誤 (例如 DNS 解析失敗、超時)
        print(f"錯誤: 無法連接到 Figma API。 {e}")
        return jsonify({"error": f"網路錯誤: 無法連接到 Figma API。"}), 503

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # 處理資料解析錯誤 (回傳的不是 JSON，或是結構不符預期)
        print(f"錯誤: 解析 Figma 回應失敗。 {e}")
        return jsonify({"error": "解析 Figma 資料結構失敗，請確認檔案內容是否正確或不是空的。"}), 500

    except Exception as e:
        # 處理所有其他未預期的錯誤
        print(f"發生未預期的伺服器錯誤: {e}")
        return jsonify({"error": "發生未預期的伺服器錯誤，請稍後再試。"}), 500


# --- 讓服務在本機和 Cloud Run 上都能運行的設定 ---
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
