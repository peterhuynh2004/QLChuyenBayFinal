import os.path

from sqlalchemy import func
from appQLChuyenBay import app
import json

#Tạo hàm đọc chung  json qua đường dẫn tương đối (path)
def read_json(path):
   with open(path, "r") as f:
       return json.load(f)
#Hàm tự động đóng


