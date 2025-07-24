# main.py

from flask import Flask, request, jsonify
import requests
import json

# 建立一個 Flask 應用程式實例
app = Flask(__name__)

# -------------------------------------------------------------------
#  未來你的 Figma-to-Elementor 核心轉換邏輯會放在這裡
#  為了讓部署流程可以順利走完，我們先用假資料來模擬
# -------------------------------------------------------------------
def get_figma_data_from_api(api_token, file_key):
    """模擬從 Figma API 獲取資料"""
    print(f"正在嘗試用 Token: {api_token[:5]}... 和 File Key: {file_key} 獲取資料")
    # 在這裡，你會放入真實的 requests.get() 邏輯
    # 現在我們先回傳一個假的 Figma 節點結構
    return {
        "name": "My Awesome Design",
        "document": {
            "children": [{
                "name": "Landing Page",
                "type": "CANVAS",
                "children": [{
                    "name": "Hero Section",
                    "type": "FRAME",
                    "children": [{
                        "name": "Title",
                        "type": "TEXT",
                        "characters": "歡迎來到我的網站！"
                    }]
                }]
            }]
        }
    }

def convert_to_elementor_json(figma_data):
    """模擬將 Figma 資料轉換為 Elementor JSON"""
    print(f"正在轉換 Figma 檔案: {figma_data['name']}")
    # 在這裡，你會放入我們之前設計的遞迴轉換邏輯
    # 現在我們先回傳一個假的 Elementor 結構
    title_text = figma_data['document']['children'][0]['children'][0]['children'][0]['characters']
    
    elementor_widget = {
        "elType": "widget",
        "widgetType": "heading",
        "settings": {
            "title": title_text
        }
    }
    elementor_column = {"elType": "column", "elements": [elementor_widget]}
    elementor_section = {"elType": "section", "elements": [elementor_column]}
    
    return [elementor_section] # Elementor 的 JSON 最終需要是一個陣列

# -------------------------------------------------------------------
#  API 端點 (Endpoint) 的定義
# -------------------------------------------------------------------
@app.route("/")
def index():
    """建立一個根路徑，用來確認服務是否正常運行"""
    return "<h1>Figma-to-Elementor 轉換器已啟動！</h1><p>請使用 POST 請求到 /convert 端點來進行轉換。</p>"

@app.route("/convert", methods=['POST'])
def handle_conversion():
    """
    這是我們主要的 API 端點，負責接收請求並回傳轉換結果。
    """
    # 1. 檢查請求的格式是否為 JSON
    if not request.is_json:
        return jsonify({"error": "請求格式錯誤，請使用 application/json"}), 400

    # 2. 從請求的 JSON Body 中取得資料
    data = request.get_json()
    api_token = data.get('figma_token')
    file_key = data.get('file_key')

    if not api_token or not file_key:
        return jsonify({"error": "請求中缺少 'figma_token' 或 'file_key'"}), 400

    # 3. 呼叫我們的核心邏輯
    print("接收到請求，開始執行轉換...")
    figma_data = get_figma_data_from_api(api_token, file_key)
    elementor_json = convert_to_elementor_json(figma_data)

    # 4. 回傳成功的 JSON 結果
    return jsonify(elementor_json)

# --- 讓服務在本機和 Cloud Run 上都能運行的設定 ---
if __name__ == "__main__":
    # Cloud Run 會透過環境變數 PORT 來告訴我們要在哪個埠號上運行
    import os
    port = int(os.environ.get("PORT", 8080))
    # 設為 '0.0.0.0' 讓容器可以從外部接收請求
    app.run(host='0.0.0.0', port=port)