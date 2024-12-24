import json
import math
import os
from datetime import timedelta, datetime

import requests
from flask import render_template, request, redirect, url_for, jsonify, flash, current_app
from sqlalchemy.dialects.mssql.information_schema import sequences
from sqlalchemy.testing.plugin.plugin_base import post_begin
from payos import PaymentData, ItemData, PayOS
import dao
from appQLChuyenBay import app, login, mail, db
from flask_mail import Message
import random, datetime
from flask import session

from flask_login import login_user, logout_user, current_user

# from dotenv import load_dotenv
#
# load_dotenv()

client_id = "acd90926-de08-4e7f-bb5d-1c5b2ba7997d"
api_key = "e533c9d0-6d93-4986-8699-fedd9947c51a"
checksum_key = "8db231c6edefe49255362836a6ef9debd289e70023b384147e18dfc10aeeba92"
payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)
# payOS = PayOS(client_id=os.environ.get('PAYOS_CLIENT_ID'), api_key=os.environ.get('PAYOS_API_KEY'), checksum_key=os.environ.get('PAYOS_CHECKSUM_KEY'))

@app.route("/", methods=['get', 'post'])
def index():
    # Lấy danh sách chuyến bay sắp cất cánh
    flights = dao.get_upcoming_flights()
    flight_info = []
    for flight in flights:
        # Lấy tên tuyến bay từ ID_TuyenBay
        route = dao.get_route_name_by_id(flight.id_TuyenBay)

        if route:
            # Lưu thông tin chuyến bay vào danh sách flight_info
            flight_info.append({
                "hành_trình": route.tenTuyen,
                "thời_gian": flight.gio_Bay.strftime('%d-%m-%Y %H:%M'),  # Giả sử gioBay là kiểu datetime
            })

    return render_template('index.html', flights=flight_info)


@app.route('/api/danhsachchuyenbay', methods=['POST'])
def api_danhsachchuyenbay():
    data = request.get_json()  # Nhận dữ liệu JSON từ yêu cầu POST
    print(data)  # Debug dữ liệu

    # Lấy id sân bay đi và đến
    id_NoiDi = dao.get_id_san_bay(data.get('SanBayDi'))
    id_NoiDen = dao.get_id_san_bay(data.get('SanBayDen'))

    if data and id_NoiDi is not None and id_NoiDen is not None:
        # Gán giá trị cho các biến
        san_bay_di = id_NoiDi
        san_bay_den = id_NoiDen
        thoi_gian = data.get('ThoiGian')
        gh1 = int(data.get('GH1', 0))  # Đảm bảo gh1 là số nguyên
        gh2 = int(data.get('GH2', 0))  # Đảm bảo gh2 là số nguyên
        print(f"Searching flights with: {san_bay_di}, {san_bay_den}, {thoi_gian}, {gh1}, {gh2}")  # Debug

        # Lấy danh sách chuyến bay
        flights = dao.get_flights(san_bay_di, san_bay_den, thoi_gian, gh1, gh2)

        # Trả về kết quả dưới dạng JSON
        return jsonify(flights), 200
    else:
        return jsonify({"error": "Invalid input or unknown airport"}), 400


@app.route('/api/get_tuyenbay', methods=['GET'])
def api_get_tuyenbay():
    try:
        # Lấy danh sách tất cả các tuyến bay từ bảng TuyenBay
        tuyen_bay_list = dao.get_all_tuyen_bay()  # Giả sử dao có phương thức này
        # Trả về danh sách dưới dạng JSON
        return jsonify([{
            'tenTuyen': tb.tenTuyen,
            'id_SanBayDi': tb.id_SanBayDi,
            'id_SanBayDen': tb.id_SanBayDen,
            'id_TuyenBay': tb.id_TuyenBay
        } for tb in tuyen_bay_list])
    except Exception as e:
        app.logger.error(f"Error fetching SanBay: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500



@app.route('/api/get_sanbay', methods=['GET'])
def get_sanbay():
    try:
        sanbay_list = dao.get_san_bay()

        # Trả về dữ liệu dưới dạng JSON
        return jsonify([{
            'ten_SanBay': sb.ten_SanBay + ' (' + sb.DiaChi + ')'
        } for sb in sanbay_list])
    except Exception as e:
        app.logger.error(f"Error fetching SanBay: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/trangchu")
def trangchudangnhap():
    name = request.args.get('user_name')
    return render_template('index.html')


@app.route('/api/user/roles', methods=['GET'])
def get_user_roles():
    if current_user.is_authenticated:
        user_id = current_user.ID_User  # Kiểm tra vai trò của người dùng
        user_role = dao.get_user_role(user_id)
        checkrole = dao.checkrole(user_role)

        if checkrole:
            return jsonify(True)  # Trả về True dưới dạng JSON

    return jsonify(False)  # Trả về False nếu không có vai trò hợp lệ

    return False


@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__('POST'):
        username = request.form.get('email')
        password = request.form.get('password')

        u = dao.auth_user(username=username, password=password)
        if u:
            login_user(u)

            # Lấy id người dùng
            user_id = u.ID_User  # Kiểm tra vai trò của người dùng
            user_role = dao.get_user_role(user_id)
            checkrole = dao.checkrole(user_role)
            if checkrole:
                return redirect('/nhan_vien')

            # Nếu không phải nhân viên, chuyển về trang chủ
            return redirect('/')

    return render_template('login.html')


@app.route("/logout")
def logout_process():
    logout_user()
    session["user_role"] = ""
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


# @app.route("/ket_qua_tim_kiem")
# def huongdandatcho():
#     return render_template('huong_dan_dat_cho.html')

@app.route("/huong_dan_dat_cho")
def huongdandatcho():
    return render_template('huong_dan_dat_cho.html')


@app.route("/chuc_nang")
def chucnang():
    user_id = session.get('_user_id')  # Kiểm tra vai trò của người dùng
    user_role = dao.get_user_role(user_id)
    user_role_change = dao.change_user_role(user_role)
    if 'NhanVien' in user_role_change:
        return render_template('chuc_nang.html', user_role_change=user_role_change)
    else:
        return render_template('index.html')


@app.route("/lap_lich_chuyen_bay", endpoint="lap_lich_chuyen_bay", methods=["GET", "POST"])
def laplichchuyenbay():
    if request.method == "POST":
        flight_date = request.form['flight_date']
        TuyenBay = request.form['TuyenBay']
        flight_duration = int(request.form['flight_duration'])
        first_class_seats = int(request.form['first_class_seats'])
        economy_class_seats = int(request.form['economy_class_seats'])

        # Lấy các quy định từ bảng QuyDinhSanBay
        quy_dinh = dao.get_quy_dinh_san_bay()

        # Kiểm tra thời gian bay tối thiểu
        thoi_gian_bay_toi_thieu = quy_dinh.ThoiGianBayToiThieu
        if flight_duration < thoi_gian_bay_toi_thieu:
            flash(f"Thời gian bay phải lớn hơn {thoi_gian_bay_toi_thieu} phút.", "error")
            return render_template('lap_lich_chuyen_bay.html')

        # Kiểm tra số lượng sân bay trung gian
        san_bay_trung_gian_toi_da = quy_dinh.SanBayTrungGianToiDa
        intermediate_airports = request.form.getlist('intermediate_airports')
        if len(intermediate_airports) > san_bay_trung_gian_toi_da:
            flash(f"Chỉ được phép thêm tối đa {san_bay_trung_gian_toi_da} sân bay trung gian.", "error")
            return render_template('lap_lich_chuyen_bay.html')

        # Lấy id tuyến bay
        id_TuyenBay = dao.get_id_TuyenBay(TuyenBay)
        flight = dao.save_ChuyenBay(flight_date=flight_date, flight_duration=flight_duration,
                                    first_class_seats=first_class_seats,
                                    economy_class_seats=economy_class_seats, id_TuyenBay=id_TuyenBay)

        # Lấy thông tin sân bay trung gian
        intermediate_airports = []
        for key, value in request.form.items():
            if key.startswith("intermediate_airports"):
                parts = key.split("[")
                index = int(parts[1].split("]")[0])
                field = parts[2].split("]")[0]
                if len(intermediate_airports) <= index:
                    intermediate_airports.append({})
                intermediate_airports[index][field] = value

        # Kiểm tra thời gian dừng tại sân bay trung gian
        thoi_gian_dung_toi_thieu = quy_dinh.ThoiGianDungToiThieu
        thoi_gian_dung_toi_da = quy_dinh.ThoiGianDungToiDa
        for airport in intermediate_airports:
            thoi_gian_dung = int(airport.get("duration", 0))
            if thoi_gian_dung < thoi_gian_dung_toi_thieu:
                flash(f"Thời gian dừng tại sân bay trung gian phải lớn hơn {thoi_gian_dung_toi_thieu} phút.", "error")
                return render_template('lap_lich_chuyen_bay.html')
            if thoi_gian_dung > thoi_gian_dung_toi_da:
                flash(f"Thời gian dừng tại sân bay trung gian không được vượt quá {thoi_gian_dung_toi_da} phút.",
                      "error")
                return render_template('lap_lich_chuyen_bay.html')

                # Lưu sân bay trung gian
                luusbaytrunggian = dao.save_sbbaytrunggian(intermediate_airports=intermediate_airports, flight=flight)

        return redirect(url_for('lap_lich_chuyen_bay'))

    return render_template('lap_lich_chuyen_bay.html')


from dao import get_filtered_flights


@app.route("/danhsachchuyenbay")
def danhsachchuyenbay():
    # Lấy tham số từ yêu cầu GET
    san_bay_di = request.args.get('SanBayDi', None)
    san_bay_den = request.args.get('SanBayDen', None)
    thoi_gian = request.args.get('ThoiGian', None)
    gh1 = request.args.get('GH1', None)
    gh2 = request.args.get('GH2', None)

    # Gọi hàm từ dao để lấy danh sách chuyến bay
    page = request.args.get('page', 1, type=int)
    flights = get_filtered_flights(san_bay_di, san_bay_den, thoi_gian, gh1, gh2, page=page, per_page=10)

    flight_info = []
    for flight in flights.items:
        route = dao.get_route_name_by_id(flight.id_TuyenBay)
        sân_bay_trung_gian = dao.get_route_sanbaytrunggian_by_id(flight.id_ChuyenBay)
        # Chuyển danh sách các đối tượng Row thành một danh sách các chuỗi
        san_bay_trung_gian_list = [row.ten_SanBay for row in sân_bay_trung_gian]

        # Kết hợp các tên sân bay vào một chuỗi
        sân_bay_trung_gian = ', '.join(san_bay_trung_gian_list)
        if route:
            flight_info.append({
                "id": flight.id_ChuyenBay,
                "hành_trình": route.tenTuyen,
                "thời_gian": flight.gio_Bay.strftime('%d-%m-%Y %H:%M'),
                "ghế_hạng_1_còn_trống": flight.GH1_DD,
                "ghế_hạng_2_còn_trống": flight.GH2_DD,
                "GH1": flight.GH1,
                "GH2": flight.GH2,
                "sân_bay_trung_gian": sân_bay_trung_gian,
            })

    return render_template('danhsachchuyenbay.html', flights=flight_info, pagination=flights)


@app.route('/ban_ve/<int:id_chuyen_bay>', methods=['get', 'post'])
def banve(id_chuyen_bay):
    session['id_chuyen_bay'] = id_chuyen_bay
    flight = dao.get_flight_by_id(id_chuyen_bay)
    print(flight['GH1'])
    print(flight['GH2'])
    print(flight['ghe_dadat'])
    first_class_seats = flight['GH1']  # Số ghế hạng nhất
    economy_class_seats = flight['GH2']  # Số ghế hạng phổ thông
    return render_template(
        'ban_ve.html',
        first_class_seats=first_class_seats,
        economy_class_seats=economy_class_seats,
        flight=flight  # Truyền flight vào template
    )


@app.route("/nhan_vien")
def nhanvien():
    user_id = session.get('_user_id')  # Kiểm tra vai trò của người dùng
    user_role = dao.get_user_role(user_id)
    user_role_change = dao.change_user_role(user_role)
    return render_template('nhan_vien.html', user_role_change=user_role_change)


@app.route("/kiem_tra_ma")
def kiemtrama():
    return render_template('kiem_tra_ma.html')


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


@app.route("/timkiemchuyenbay", methods=['get', 'post'])
def timkiemchuyenbay():
    airport = dao.get_san_bay()
    SanBayDi = request.args.get('NoiDi').split('(')[0].strip()
    SanBayDen = request.args.get('NoiDen').split('(')[0].strip()
    ngayDi = request.args.get('Date')
    veNguoiLon = request.args.get('SLNguoiLon')
    veTreEm = request.args.get('SLTreEm')
    veEmBe = request.args.get('SLEmBe')
    tongVe = int(veNguoiLon) + int(veTreEm) + int(veEmBe)
    session['veNguoiLon'] = veNguoiLon
    session['veTreEm'] = veTreEm
    session['veEmBe'] = veEmBe
    session['tongGhe'] = tongVe
    id_SanBayDi = dao.get_id_San_Bay(SanBayDi)
    id_SanBayDen = dao.get_id_san_bay(SanBayDen)
    session['sanBayDi'] = id_SanBayDi
    session['sanBayDen'] = id_SanBayDen
    flight = dao.load_flight(noiDi=id_SanBayDi, noiDen=id_SanBayDen, ngayDi=ngayDi)
    giaChuyenBay=None
    if flight:
        giaChuyenBay = dao.get_GiaVeByByIDSanBay(sanBayDi=id_SanBayDi, sanBayDen=id_SanBayDen, loaiGhe = "GH1")
    return render_template('timkiemchuyenbay.html',
                           airport=airport, flight=flight,
                           giaChuyenBay=giaChuyenBay,
                           SanBayDi=SanBayDi, SanBayDen=SanBayDen, id_SanBayDi=id_SanBayDi, id_SanBayDen=id_SanBayDen, ngayDi=ngayDi, tongVe=tongVe)


@app.route("/datveonline", methods=['GET', 'POST'])
def datveonline():
    if request.method == 'GET':
        maChuyenBay = request.args.get('maChuyenBay')
        if maChuyenBay:
            session['maChuyenBay'] = maChuyenBay

    elif request.method == 'POST':
        # Lấy giá trị từ form
        session['hangGhe'] = request.form.get('hangGhe')
        # Các trường cần lấy thông tin
        fields1 = ['fullNameNguoiLon', 'phone', 'email', 'ngaySinhNguoiLon', 'cccd']
        # Tạo một từ điển để lưu trữ dữ liệu
        data = {field: [] for field in fields1}
        for i in range(int(session['veNguoiLon'])):
            for field in fields1:
                data[field].append(request.form.getlist(f'{field}[{i}]'))
        # Lưu thông tin vào session
        session.update(data)

        #trẻ em:

        fields2 = ['fullNameTreEm', 'ngaySinhTreEm']
        # Tạo một từ điển để lưu trữ dữ liệu
        data2 = {field: [] for field in fields2}
        for i in range(int(session['veTreEm'])):
            for field in fields2:
                data2[field].append(request.form.getlist(f'{field}[{i}]'))
        # Lưu thông tin vào session
        session.update(data2)
        # Em bé:
        fields3 = ['fullNameEmBe', 'ngaySinhEmBe']
        # Tạo một từ điển để lưu trữ dữ liệu
        data3 = {field: [] for field in fields3}
        for i in range(int(session['veEmBe'])):
            for field in fields3:
                data3[field].append(request.form.getlist(f'{field}[{i}]'))
        # Lưu thông tin vào session
        session.update(data3)
        print(session.get('emBeData'))

        # Chuyển sang bước tiếp theo
        return redirect('thongtindatve')
    # Hiển thị form đặt vé
    return render_template(
        'datveonline.html',
        veNguoiLon=int(session.get('veNguoiLon', 0)),
        veTreEm=int(session.get('veTreEm', 0)),
        veEmBe=int(session.get('veEmBe', 0))
    )


@app.route('/api/get_gia_ve', methods=['POST'])
def get_gia_ve():
    data = request.json
    sanBayDi = data.get('sanBayDi')
    sanBayDen = data.get('sanBayDen')
    hangGhe = data.get('hangGhe')

    # Lấy giá vé từ cơ sở dữ liệu
    giaVe = dao.get_GiaVeByByIDSanBay(sanBayDi, sanBayDen, hangGhe)
    return jsonify({'giaVe': giaVe})


@app.route("/thongtindatve", methods=['GET', 'POST'])
def thongtindatve():

    # Truy xuất dữ liệu từ session
    fullNameNguoiLon = session.get('fullNameNguoiLon', [])
    phone = session.get('phone', [])
    email = session.get('email', [])
    ngaySinhNguoiLon = session.get('ngaySinhNguoiLon', [])
    cccd = session.get('cccd', [])
    # Tạo danh sách hành khách
    hanhKhach = []
    for i in range(len(fullNameNguoiLon)):
        hanhKhach.append({
            'fullName': fullNameNguoiLon[i][0],  # Vì `getlist` trả về danh sách, cần lấy phần tử đầu tiên
            'phone': phone[i][0],
            'email': email[i][0],
            'ngaySinh': ngaySinhNguoiLon[i][0],
            'cccd': cccd[i][0],
            'loaiVe': 'Người lớn'
        })

    # Trẻ em
    fullNameTreEm = session.get('fullNameTreEm', [])
    ngaySinhTreEm = session.get('ngaySinhTreEm', [])
    print(f"Full Name Trẻ Em: {fullNameTreEm}")
    print(f"Ngày Sinh Trẻ Em: {ngaySinhTreEm}")
    treEm = []
    for i in range(len(fullNameTreEm)):
        hanhKhach.append({
            'fullName': fullNameTreEm[i][0],  # Vì `getlist` trả về danh sách, cần lấy phần tử đầu tiên
            'ngaySinh': ngaySinhTreEm[i][0],
            'loaiVe': 'Trẻ em'
        })

    # Em bé
    fullNameEmBe = session.get('fullNameEmBe', [])
    ngaySinhEmBe = session.get('ngaySinhEmBe', [])
    emBe = []

    for i in range(len(fullNameEmBe)):
        hanhKhach.append({
            'fullName': fullNameEmBe[i][0],  # Vì `getlist` trả về danh sách, cần lấy phần tử đầu tiên
            'ngaySinh': ngaySinhEmBe[i][0],
            'loaiVe': 'Em bé'
        })
    print(f"Han Khach: {hanhKhach}")
    print(f"Tre Em: {treEm}")
    print(f"Em Be: {emBe}")
    # Render ra giao diện
    return render_template('thongtindatve.html',
                           veNguoiLon=int(session['veNguoiLon']),
                           veTreEm=int(session['veTreEm']),
                           veEmBe=int(session['veEmBe']),
                           hanhKhach=hanhKhach, treEm=treEm, emBe=emBe)



@app.route('/thanhtoanbangtienmat', methods=['GET'])
def thanh_toan_bang_tien_mat():
    try:
        # Lấy dữ liệu từ URL
        seats_info = request.args.get('seats')
        total_cost = request.args.get('totalCost')
        passengerinfo = request.args.get('passengerInfo')

        # Kiểm tra và chuyển đổi dữ liệu JSON
        seats_info = json.loads(seats_info) if seats_info else []
        passengerinfo = json.loads(passengerinfo) if passengerinfo else []

        # Kết hợp thông tin ghế và hành khách nếu số lượng khớp nhau
        if len(seats_info) != len(passengerinfo):
            raise ValueError("Số lượng ghế và hành khách không khớp.")

        combined_info = [
            {
                "seat": seat,
                "passenger": passenger
            }
            for seat, passenger in zip(seats_info, passengerinfo)
        ]

        # Trả về template với thông tin đã xử lý
        return render_template(
            'thanhtoantienmat.html',
            total_cost=total_cost,
            combined_info=combined_info
        )
    except (ValueError, json.JSONDecodeError) as e:
        # Xử lý lỗi và hiển thị thông báo
        return f"Lỗi trong quá trình xử lý dữ liệu: {str(e)}", 400


@app.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    if request.method == 'POST':
        try:
            # Nhận chuỗi JSON từ form
            seats_info = request.form['seats-info']
            # id_user = session.get('id_user')   # Lấy id_user từ session
            id_user = 2
            # Lưu thông tin thanh toán vào cơ sở dữ liệu

            # Lưu thông tin vé
            if dao.save_ticket_info(id_user, seats_info):
                flash('Thanh toán thành công! Thông tin vé đã được lưu.')
                session['seats_info'] = seats_info  # Lưu dữ liệu vào session
            else:
                flash('Lỗi khi lưu thông tin vé.')

        except Exception as e:
            print("Lỗi trong quá trình xử lý: ", e)
            flash('Đã xảy ra lỗi trong quá trình thanh toán.')

        return redirect(url_for('thanhtoanthanhcong'))  # Trang xác nhận thanh toán thành công


@app.route('/thanhtoanthanhcong', methods=['GET', 'POST'])
def thanhtoanthanhcong():
    seats_info = session.get('seats_info')  # Lấy dữ liệu từ session
    id_ChuyenBay = session.get('id_chuyen_bay')
    if seats_info:
        if isinstance(seats_info, str):
            # Nếu dữ liệu là chuỗi, thử chuyển thành dictionary (nếu có thể)
            # Lưu ý: nếu chuỗi này không phải JSON hợp lệ, bạn cần xử lý trường hợp này.
            seats_info = eval(
                seats_info)  # Chỉ nên dùng eval khi bạn chắc chắn dữ liệu hợp lệ (cẩn thận với lỗi bảo mật)
        tenTuyen = dao.get_TuyenBay(id_ChuyenBay);
        return render_template('thanhtoanthanhcong.html', seats_info=seats_info, tenTuyen=tenTuyen)
    else:
        flash('Không tìm thấy thông tin vé.')
        return redirect(url_for('index'))  # Chuyển hướng về trang chủ hoặc trang khác nếu không có dữ liệu
    return render_template('thanhtoanthanhcong.html')



@app.route('/thaydoiquydinh')
def thaydoiquydinh():
    return render_template('thaydoiquydinh.html')


@app.route('/quydinhbanve')
def quydinhbanve():
    return render_template('quydinhbanve.html')


@app.route('/quydinhve')
def quydinhve():
    return render_template('quydinhve.html')


@app.route('/quydinhsanbay')
def quydinhsanbay():
    return render_template('quydinhsanbay.html')


@app.route('/api/quydinh/sanbay/<int:id>', methods=['GET'])
def get_quy_dinh_san_bay(id):
    quy_dinh = dao.getquydinhsanbay(id)
    if not quy_dinh:
        return jsonify({'message': 'Quy định không tồn tại'}), 404

    return jsonify({
        'SoLuongSanBay': quy_dinh.SoLuongSanBay,
        'ThoiGianBayToiThieu': quy_dinh.ThoiGianBayToiThieu,
        'SanBayTrungGianToiDa': quy_dinh.SanBayTrungGianToiDa,
        'ThoiGianDungToiThieu': quy_dinh.ThoiGianDungToiThieu,
        'ThoiGianDungToiDa': quy_dinh.ThoiGianDungToiDa,
    }), 200


@app.route('/api/quydinh/sanbay/<int:id>', methods=['PUT'])
def update_quy_dinh_san_bay(id):
    try:
        # Lấy dữ liệu JSON từ yêu cầu
        data = request.json
        if not data:
            return jsonify({"message": "Không có dữ liệu gửi lên"}), 400

        luutru = dao.thaydoiquydinhsanbay(id, data)

        return jsonify({"message": "Cập nhật quy định sân bay thành công"}), 200
    except Exception as e:
        return jsonify({"message": f"Có lỗi xảy ra: {str(e)}"}), 500


# API Lấy thông tin quy định bán vé
@app.route('/api/quydinh/banve/<int:id>', methods=['GET'])
def get_quy_dinh_ban_ve(id):
    quy_dinh = dao.getquydinhbanve(id)
    if quy_dinh:
        return quy_dinh
    else:
        return jsonify({"message": "Quy định không tồn tại"}), 404


# API Cập nhật thông tin quy định bán vé
@app.route('/api/quydinh/banve/<int:id>', methods=['PUT'])
def update_quy_dinh_ban_ve(id):
    data = request.json
    quy_dinh = dao.thaydoiquydinhbanve(id, data)
    try:
        if quy_dinh:
            return jsonify({"message": "Cập nhật quy định bán vé thành công"}), 200
    except Exception as e:
        return jsonify({"message": "Cập nhật thất bại", "error": str(e)}), 400


# API Lấy thông tin quy định vé
@app.route('/api/quydinh/ve/<int:id>', methods=['GET'])
def get_quy_dinh_ve(id):
    quy_dinh = dao.getquydinhve(id)
    if quy_dinh:
        return quy_dinh
    return jsonify({"message": "Quy định không tồn tại"}), 404


# API Cập nhật quy định vé
@app.route('/api/quydinh/ve/<int:id>', methods=['PUT'])
def update_quy_dinh_ve(id):
    data = request.json
    quy_dinh = dao.setquydinhve(id, data)

    try:
        if quy_dinh:
            return jsonify({"message": "Cập nhật thành công"}), 200
    except Exception as e:
        return jsonify({"message": "Cập nhật thất bại", "error": str(e)}), 400


@app.route("/thanhtoanonline", methods=['get', 'post'])
def thanhtoanonline():
    hangGhe = session['hangGhe']
    tenHangGhe = ''
    if hangGhe == 'GH1':
        tenHangGhe = 'Hạng 1'
    elif hangGhe == 1:
        tenHangGhe = 'Hạng 2'
    veNguoiLon = int(session['veNguoiLon'])
    veTreEm = int(session['veTreEm'])
    veEmBe = int(session['veEmBe'])
    giaVe = dao.get_GiaVeByByIDSanBay(session['sanBayDi'], session['sanBayDen'], session['hangGhe'])
    tongVe = session['tongGhe']
    tongTien = tongVe * giaVe
    session['tongTien'] = tongTien
    return render_template('checkout.html', tenHangGhe=tenHangGhe,
                           veEmBe=veEmBe,
                           veNguoiLon=veNguoiLon,
                           veTreEm=veTreEm, tongTien=tongTien, tongVe=tongVe)


@app.route("/create_payment_link", methods=['POST'])
def creat_payment():
    domain="http://127.0.0.1:8000" #Xác định domain nội bộ (local) để sử dụng làm URL cho việc hủy hoặc hoàn tất thanh toán.
    try:
        paymentData = PaymentData(orderCode=random.randint(1000, 99999), amount=session['tongTien'], description=f"thanh toan ve may bay",
                                  cancelUrl=f"{domain}/cancel.html", returnUrl=f"{domain}/success.html")
        payouCreatePayment = payOS.createPaymentLink(paymentData)
        return jsonify(payouCreatePayment.to_json())
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route("/cancel.html")
def cancel():
    # Lấy các tham số từ URL query string
    cancel_code = request.args.get('code')
    order_code = request.args.get('orderCode')
    cancel_status = request.args.get('status')

    # Bạn có thể xử lý dữ liệu này hoặc ghi log
    return render_template("cancel.html", cancel_code=cancel_code, order_code=order_code, cancel_status=cancel_status)


@app.route("/success.html")
def success():
    # Lấy tham số từ URL query string
    order_code = request.args.get('orderCode')
    status = request.args.get('status', 'PAID')
    customer_info = session.get('customer_info', [])

    if status == 'PAID':
        try:
            fullNameNguoiLon = session.get('fullNameNguoiLon', [])
            phone = session.get('phone', [])
            email = session.get('email', [])
            cccd = session.get('cccd', [])

            # Kiểm tra dữ liệu từ session
            if not fullNameNguoiLon or not phone or not email or not cccd:
                raise ValueError("Dữ liệu khách hàng không đầy đủ!")
            # Tạo danh sách hành khách
            hanhKhach = []
            for i in range(len(fullNameNguoiLon)):
                hanhKhach.append({
                    'fullName': fullNameNguoiLon[i],  # Vì `getlist` trả về danh sách, cần lấy phần tử đầu tiên
                    'phone': phone[i],
                    'email': email[i],
                    'cccd': cccd[i]
                })

            # Lưu thông tin khách hàng
            for h in hanhKhach:
                dao.save_customer_info(h['fullName'], h['cccd'], h['phone'], 2)  # Chỉnh sửa cách truy cập các giá trị từ dict
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Lỗi khi lưu thông tin khách hàng: {str(e)}")
            return f"Có lỗi xảy ra khi lưu thông tin khách hàng! Error: {str(e)}", 500

    return render_template("success.html", order_code=order_code)


@app.route('/admin/')
def admin():
    tuyenbays = dao.get_san_bay()
    chuyenbays = dao.get_chuyen_bay()


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


@app.route('/admin/quanly')
def quanly():
    return  render_template('quanly.html')

@app.route('/quanlynguoidung', methods=['GET', 'POST'])
def user_list():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        hoten = request.form.get('HoTen')
        email = request.form.get('Email')
        matkhau = request.form.get('MatKhau')
        sdt = request.form.get('SDT')
        gioitinh = request.form.get('GioiTinh')
        # Lấy danh sách vai trò
        roles = request.form.getlist('roles[]')  # Lấy danh sách các giá trị
        print("Danh sách vai trò:", roles)

        # Kiểm tra email đã tồn tại
        if dao.check_email_exists2(email):  # Phương thức này kiểm tra xem email có tồn tại không
            error_message = 'Email đã tồn tại. Vui lòng nhập email khác.'
        else:
            # Nếu email không tồn tại, thêm người dùng mới
            new_user_id = dao.add_user2(hoten, email, matkhau, sdt, gioitinh)
            # Gán vai trò cho người dùng
            for role in roles:
                dao.assign_role_to_user(new_user_id, role)
            flash('Thêm người dùng thành công!', 'success')
    # Lấy danh sách người dùng từ cơ sở dữ liệu
    users = dao.query_user()

    # Lấy tất cả vai trò của người dùng cùng một lúc
    user_roles = dao.get_all_roles()  # Trả về danh sách (ID_User, VaiTro)

    # Chuẩn bị dữ liệu vai trò dưới dạng từ điển
    roles_dict = {}
    for user_id, role in user_roles:
        if user_id not in roles_dict:
            roles_dict[user_id] = []
        roles_dict[user_id].append(role)

    # Chuẩn bị danh sách kết hợp user, giới tính và vai trò
    user_data = []
    for user in users:
        # Lấy giới tính
        gender = dao.get_GioiTinh(user.GioiTinh)

        # Lấy vai trò từ từ điển
        user_roles = roles_dict.get(user.ID_User, [])
        role1 = user_roles[0] if len(user_roles) > 0 else ''
        role2 = user_roles[1] if len(user_roles) > 1 else ''

        # Thêm thông tin vào danh sách
        user_data.append((user, gender, role1, role2))
    all_roles = dao.get_all_role_names()
    return render_template('quanlynguoidung.html', user_data=user_data, all_roles=all_roles)

@app.route('/api/vai_tro/<int:id_user>', methods=['GET'])
def get_roles_by_user(id_user):
    try:
        # Truy vấn danh sách vai trò của người dùng dựa trên ID_User
        roles = dao.get_roles(id_user)

        # Chuyển vai trò từ Enum thành tên vai trò (danh sách)
        role_names = [dao.get_role_name(role.ID_VaiTro) for role in roles]

        return jsonify({
            'success': True,
            'id_user': id_user,
            'roles': role_names
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error retrieving roles.',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        app.run(port=8000, debug=True)

