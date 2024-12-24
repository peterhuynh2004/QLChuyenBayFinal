from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager, current_user
import cloudinary
from flask_mail import Mail, Message
from datetime import timedelta


app = Flask(__name__)
app.secret_key = 'ạkdgasfu324234afssdffdsg'

app.secret_key = 'HGHJAHA^&^&*AJAVAHJ*^&^&*%&*^GAFGFAG'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/qlchuyenbay?charset=utf8mb4" % quote(
    'Leviethaiquan2206@')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8

db = SQLAlchemy(app=app)

login = LoginManager(app)

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(hours=1)  # Cookie hết hạn sau 1 giờ

cloudinary.config(
    cloud_name="ddgxultsd",
    api_key="186632124732842",
    api_secret="iE7EGw6Lk-LMs1CMy7JpcX3fj3A",
    secure=True
)

# Cấu hình Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'lucius.nuxi@gmail.com'  # Email gửi
app.config['MAIL_PASSWORD'] = 'rdia ltsu neuj rcgj'  # Mật khẩu ứng dụng hoặc mã xác thực
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# Khởi tạo Flask-Mail
mail = Mail(app)

