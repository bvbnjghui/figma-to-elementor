# Dockerfile

# 步驟 1: 選擇一個官方的 Python 基礎映像檔
# 我們選擇 slim 版本，它比較小，可以加快部署速度
FROM python:3.9-slim

# 步驟 2: 設定容器內的工作目錄
# 之後的所有指令都會在這個 /app 資料夾內執行
WORKDIR /app

# 步驟 3: 複製「購物清單」並安裝所有需要的套件
# 我們先把這個檔案複製進去，這樣 Docker 就可以快取安裝好的套件
# 如果 requirements.txt 沒有變動，下次建置時就不用重新安裝，速度會快很多
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 步驟 4: 將你專案資料夾裡的所有檔案，複製到容器的 /app 目錄下
COPY . .

# 步驟 5: 設定容器啟動時要執行的命令
# 這會執行 "python main.py"，也就是啟動我們的 Flask 網路服務
CMD ["python", "main.py"]