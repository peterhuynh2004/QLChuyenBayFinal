import math
from datetime import timedelta
from dbm import error

from click import password_option
from flask import Flask, url_for, flash
from flask import render_template, request, redirect
from flask.cli import routes_command
from payos import PayOS
from sqlalchemy import except_
from sqlalchemy.testing.pickleable import User

import dao
from  dao import UserRole, update_user_roles, get_user_by_id, add_user
from appQLChuyenBay import app, login, mail, db #Thêm dòng database
from appQLChuyenBay import utils
from flask_mail import Message
import random
from flask import render_template
from flask import session

from flask_login import login_user, logout_user, current_user

# from dotenv import load_dotenv
#
#
# load_dotenv()

client_id = "acd90926-de08-4e7f-bb5d-1c5b2ba7997d"
api_key = "e533c9d0-6d93-4986-8699-fedd9947c51a"
checksum_key = "8db231c6edefe49255362836a6ef9debd289e70023b384147e18dfc10aeeba92"
payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)
# payOS = PayOS(client_id=os.environ.get('PAYOS_CLIENT_ID'), api_key=os.environ.get('PAYOS_API_KEY'), checksum_key=os.environ.get('PAYOS_CHECKSUM_KEY'))

@app.route("/", methods=['get', 'post'])

def index():
    return render_template('index.html')



@app.route("/trangchu")
def trangchudangnhap():
    name = request.args.get('user_name')
    return render_template('index.html')


@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('email')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
            login_user(u)
            return redirect('/')

    return render_template('login.html')


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method.__eq__('POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        # Kiểm tra nếu email đã tồn tại
        if dao.check_email_exists(email):
            err_msg = 'Email đã tồn tại!'
        elif not password.__eq__(confirm):
            err_msg = 'Mật khẩu không khớp!'
        else:
            # Tạo OTP ngẫu nhiên
            otp = random.randint(100000, 999999)
            session['otp'] = otp  # Lưu OTP vào session
            session['user_data'] = request.form  # Lưu tạm dữ liệu người dùng

            # Gửi email OTP
            msg = Message('Xác thực OTP', recipients=[email])
            msg.body = f'Chào bạn, mã OTP để hoàn tất đăng ký của bạn là: {otp}'
            mail.send(msg)

            return redirect('/xacthucotp')

    return render_template('register.html', err_msg=err_msg)


@app.route('/xacthucotp', methods=['get', 'post'])
def verify_otp():
    err_msg = ''
    if request.method.__eq__('POST'):
        entered_otp = request.form.get('otp')
        if str(session.get('otp')) == entered_otp:  # So sánh OTP nhập vào
            # Lấy dữ liệu người dùng từ session và thêm vào DB
            data = session.get('user_data')
            del data['confirm']
            data.pop('dangky', None)  # Loại bỏ trường 'dangky' nếu tồn tại
            avatar = request.files.get('avatar')
            dao.add_user(avatar=avatar, **data)
            session.pop('otp', None)  # Xóa OTP khỏi session
            session.pop('user_data', None)  # Xóa dữ liệu người dùng khỏi session

            return redirect('/login')
        else:
            err_msg = 'Mã OTP không chính xác!'

    return render_template('xacthucotp.html', err_msg=err_msg)


@app.route("/huong_dan_dat_cho")
def huongdandatcho():
    return render_template('huong_dan_dat_cho.html')


@app.route("/kiem_tra_ma")
def kiemtrama():
    return render_template('kiem_tra_ma.html')


@app.route('/admin/')
def admin():
    tuyenbays = TuyenBay.query.all()
    chuyenbays = ChuyenBay.query.all()

    # Tính tổng doanh thu và tổng số chuyến bay
    total_revenue = sum(ty.doanhThu for ty in tuyenbays)
    total_flights = sum(ty.soLuotBay for ty in tuyenbays)

    # Tính tổng số ghế và số ghế đã đặt
    total_seats = sum(cb.GH1 + cb.GH2 for cb in chuyenbays)
    occupied_seats = sum(cb.GH1_DD + cb.GH2_DD for cb in chuyenbays)

    # Tính tổng giờ bay
    total_hours = sum((cb.tG_Bay - cb.gio_Bay).total_seconds() / 3600 for cb in chuyenbays)

    # Tính tỷ lệ ghế đã đặt
    if total_seats > 0:
        avg_occupancy_rate = round((occupied_seats / total_seats * 100), 2)
        #Hàm round dùng để hiển thị 2 số thập phân và được làm tròn 1 cách phù hợp
    else:
        avg_occupancy_rate = 0

    # Tính tỷ lệ trung bình thời gian bay (giả sử tất cả các chuyến bay đều cất cánh)
    if total_flights > 0:
        avg_flight_duration = total_hours / total_flights
    else:
        avg_flight_duration = 0

    # Tỷ lệ chuyến bay cất cánh thành công (mặc định  100%)
    success_rate = 100
    return render_template('admin.html', total_revenue=total_revenue, total_flights=total_flights,
                           avg_occupancy_rate=avg_occupancy_rate, avg_flight_duration=avg_flight_duration,
                           success_rate=success_rate, total_hours=total_hours)


@app.route('/admin/thongkebaocao')
def thongkebaocao():
    # Tính tổng số tuyến bay
    total_routes = TuyenBay.query.count()

    # Tính tổng số lượt bay (nếu null thì trả về 0)
    total_flights = db.session.query(func.sum(TuyenBay.soLuotBay)).scalar() or 0

    # Tính tổng doanh thu (nếu null thì trả về 0)
    total_revenue = db.session.query(func.sum(TuyenBay.doanhThu)).scalar() or 0

    # Tính tỷ lệ ghế đã đặt
    total_seats = sum(cb.GH1 + cb.GH2 for cb in ChuyenBay.query.all())
    occupied_seats = sum(cb.GH1_DD + cb.GH2_DD for cb in ChuyenBay.query.all())
    avg_occupancy_rate = round((occupied_seats / total_seats * 100), 2) if total_seats > 0 else 0

    # Chuẩn bị label và values cho Chart.js
    labels = ["Tổng tuyến bay", "Tổng lượt bay", "Tổng doanh thu", "Tỷ lệ ghế đã đặt"]
    values = [total_routes, total_flights, total_revenue, avg_occupancy_rate]

    return render_template(
        'thongkebaocao.html',
        labels=labels,
        values=values
    )

@app.route('/admin/quanlynguoidung', methods=['GET', 'POST'])
def quanlynguoidung():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_roles = request.form.getlist('new_roles')

        try:
            update_user_roles(user_id, new_roles)
            flash('Vai trò người dùng đã được cập nhật thành công.', 'success')
        except Exception as e:
            flash('Lỗi khi cập nhật vai trò: {}'.format(e), 'error')

        return redirect(url_for('quanlynguoidung'))

    # Truy vấn người dùng và vai trò tương ứng
    users = NguoiDung.query.all()
    user_roles = {user.ID_User: [role.ID_VaiTro.name for role in user.roles] for user in users}

    return render_template('quanlynguoidung.html', users=users, user_roles=user_roles)

@app.route('/update_user_roles/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('update_user_roles.html', user=user)


@app.route('/admin/quanly')
def quanly():
    return  render_template('quanly.html')

@login.user_loader
def load_user(user_id):
    try:
        # Chuyển user_id sang dạng số nguyên nếu cần
        user_id = int(user_id)

        # Lấy thông tin người dùng từ DAO
        user = dao.get_user_by_id(user_id)

        # Kiểm tra xem user có tồn tại hay không
        if user:
            return user  # Trả về đối tượng người dùng
        return None  # Không tìm thấy người dùng
    except (ValueError, TypeError):
        # Xử lý trường hợp user_id không hợp lệ
        print("Invalid user_id:", user_id)
        return None
    except Exception as e:
        # Xử lý các lỗi khác
        print("Error loading user:", e)
        return None

# @app.route('/admin-login', methods=['POST'])
# def signin_admin():
#
#         username = request.form['username']
#         password = request.form['password']
#
#         user = utils.check_user(username = username, password = password)
#         if user:
#             login_user(user=user)
#             return redirect('/admin')
#         if not user:
#             return render_template('admin_login.html'
#                                    , err_msg="Tên đăng nhập hoặc mật khẩu không đúng")




if __name__ == '__main__':
    with app.app_context():
        app.run(port=8000, debug=True)
