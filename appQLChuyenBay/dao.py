import json
import logging
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from mailbox import Message
import re
from multiprocessing import connection

from flask import session, current_app, jsonify
from flask_sqlalchemy import pagination
from sqlalchemy import func, extract
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from models import NguoiDung, SanBay, NguoiDung_VaiTro, UserRole, ChuyenBay, TuyenBay, SBayTrungGian, VeChuyenBay, \
    ThongTinHanhKhach, QuyDinhSanBay, QuyDinhBanVe, QuyDinhVe, GioiTinh, BangGiaVe

from appQLChuyenBay import app, db, mail
import hashlib
import cloudinary.uploader
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import and_



def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    return NguoiDung.query.filter(NguoiDung.Email.__eq__(username.strip()),
                                  NguoiDung.MatKhau.__eq__(password)).first()


def add_user(name, email, password, avatar):
    # Mã hóa mật khẩu
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    # Tạo đối tượng người dùng mới
    u = NguoiDung(HoTen=name, TenDangNhap=email, Email=email, MatKhau=password, Avt='u.avatar')

    # Upload avatar nếu có
    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    # Lưu người dùng vào cơ sở dữ liệu
    db.session.add(u)
    db.session.commit()

    # Sau khi commit, ID_User của u sẽ có giá trị
    role = NguoiDung_VaiTro(ID_User=u.ID_User, ID_VaiTro=UserRole.KhachHang)

    # Lưu vai trò của người dùng
    db.session.add(role)
    db.session.commit()


def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)  # Trả về None nếu không tìm thấy


def get_san_bay():
    # Truy vấn tất cả các sân bay
    return SanBay.query.all()


def check_email_exists(email):
    Session = sessionmaker(bind=db.engine)
    session = Session()
    try:
        # Tìm người dùng với email đã cho
        user = session.query(NguoiDung).filter_by(Email=email).first()
        return user is not None  # Trả về True nếu email tồn tại
    finally:
        session.close()


# Tạo cache enum cho việc đối chiếu
role_map = {role.value: name for name, role in UserRole.__members__.items()}


def get_all_user_roles(user_id):
    user_roles = db.session.query(NguoiDung_VaiTro.ID_VaiTro).filter_by(ID_User=user_id).all()
    role_ids = [role.ID_VaiTro for role in user_roles]
    return [role_map.get(role_id) for role_id in role_ids if role_id in role_map]


def load_flight(noiDi=None, noiDen=None, ngayDi=None):
    query = ChuyenBay.query
    gioquydinh = QuyDinhBanVe.query.filter(QuyDinhBanVe.ID_QuyDinh == 3).first()
    gioquydinh = gioquydinh.ThoiGianKetThucBan * 24  # Giới hạn giờ tính theo quy định (tính giờ theo ngày)

    # Lấy giờ hiện tại và cộng thêm 'gioquydinh' giờ
    now = datetime.now()
    limit_time = now + timedelta(hours=gioquydinh)  # Thời gian hiện tại cộng với quy định giờ

    if noiDi and noiDen and ngayDi:
        query = query.join(TuyenBay).filter(
            and_(
                TuyenBay.id_SanBayDi == noiDi,  # Lọc sân bay đi
                TuyenBay.id_SanBayDen == noiDen,  # Lọc sân bay đến
                db.func.date(ChuyenBay.gio_Bay) == ngayDi,  # Lọc ngày bay
                ChuyenBay.gio_Bay > limit_time  # Lọc giờ bay lớn hơn giờ quy định
            )
        )
    return query.all()



def get_id_San_Bay(tenSanBay=None):
    query = SanBay.query.with_entities(SanBay.id_SanBay) #chỉ truy suất cột id
    if tenSanBay:
        query = query.filter(SanBay.ten_SanBay.__eq__(tenSanBay))
    return query.scalar()

def load_TuyenBay(flight=None):
    query = TuyenBay.query
    if flight:
        query = query.filter(TuyenBay.id_TuyenBay == flight)
    return query.all()


def load_flights_paginated(page=1, per_page=10):
    query = ChuyenBay.query
    return query.paginate(page=page, per_page=per_page, error_out=False)

def get_route_sanbaytrunggian_by_id(route_id):
    # Lấy danh sách sân bay trung gian theo ID chuyến bay
    route = db.session.query(SanBay.ten_SanBay).join(SBayTrungGian, SBayTrungGian.ID_SanBay == SanBay.id_SanBay).filter(SBayTrungGian.ID_ChuyenBay == route_id).all()
    return route


# Hàm lấy các chuyến bay sắp cất cánh
def get_upcoming_flights():
    # Truy vấn các chuyến bay có thời gian bay lớn hơn thời gian hiện tại
    flights = db.session.query(ChuyenBay).filter(ChuyenBay.gio_Bay > datetime.now()).order_by(ChuyenBay.gio_Bay).limit(
        10).all()
    return flights


# Hàm lấy tên tuyến bay từ id_TuyenBay
def get_route_name_by_id(route_id):
    # Truy vấn tên tuyến bay từ bảng TuyenBay
    route = db.session.query(TuyenBay.tenTuyen).filter(TuyenBay.id_TuyenBay == route_id).first()
    return route


def get_user_role(user_id):
    role = db.session.query(NguoiDung_VaiTro.ID_VaiTro).filter(NguoiDung_VaiTro.ID_User == user_id).all()
    return role

def get_SanBayTrungGian_name_by_id(id_ChuyenBay):
    results = (
        db.session.query(SanBay.ten_SanBay)
        .join(SBayTrungGian, SBayTrungGian.ID_SanBay == SanBay.id_SanBay)
        .filter(SBayTrungGian.ID_SanBay == id_ChuyenBay)
        .all()
    )
    # Trả về danh sách tên sân bay
    return [result.ten_SanBay for result in results]

def get_filtered_flights(san_bay_di=None, san_bay_den=None, thoi_gian=None, gh1=None, gh2=None, page=1, per_page=10):
    query = ChuyenBay.query.join(TuyenBay)

    if san_bay_di:
        query = query.filter(TuyenBay.id_SanBayDi == san_bay_di)
    if san_bay_den:
        query = query.filter(TuyenBay.id_SanBayDen == san_bay_den)
    if thoi_gian:
        query = query.filter(db.func.date(ChuyenBay.gio_Bay) == thoi_gian)  # Sử dụng db.func.date để lọc theo ngày
    if gh1:
        query = query.filter(ChuyenBay.GH1 >= int(gh1))
    if gh2:
        query = query.filter(ChuyenBay.GH2 >= int(gh2))

    # Thêm ràng buộc chỉ trả về chuyến bay trước 4 giờ kể từ thời điểm hiện tại
    four_hours_from_now = datetime.now() + timedelta(hours=4)
    query = query.filter(ChuyenBay.gio_Bay >= four_hours_from_now)

    # Trả về kết quả với phân trang
    return query.paginate(page=page, per_page=per_page)


def get_flights(san_bay_di, san_bay_den, thoi_gian, gh1, gh2):
    from datetime import datetime, timedelta

    # Chuyển đổi 'thoi_gian' từ dạng chuỗi sang đối tượng datetime
    thoi_gian_date = datetime.strptime(thoi_gian, '%Y-%m-%d')

    # Tính thời gian hiện tại cộng thêm 4 giờ
    gio_bay_toi_da = datetime.now() + timedelta(hours=4)

    # Tạo truy vấn SQL
    query = text("""
        SELECT 
            TuyenBay.tenTuyen,
            ChuyenBay.gio_Bay, 
            ChuyenBay.GH1 - ChuyenBay.GH1_DD AS ghe_hang_1_con_trong,
            ChuyenBay.GH2 - ChuyenBay.GH2_DD AS ghe_hang_2_con_trong,
            ChuyenBay.id_TuyenBay,
            ChuyenBay.GH1,
            ChuyenBay.GH2
        FROM TuyenBay
        JOIN ChuyenBay ON TuyenBay.id_TuyenBay = ChuyenBay.id_TuyenBay
        WHERE TuyenBay.id_SanBayDi = :san_bay_di
          AND TuyenBay.id_SanBayDen = :san_bay_den
          AND ChuyenBay.gio_Bay >= :thoi_gian
          AND ChuyenBay.gio_Bay <= :gio_bay_toi_da
          AND (ChuyenBay.GH1 - ChuyenBay.GH1_DD) >= :gh1
          AND (ChuyenBay.GH2 - ChuyenBay.GH2_DD) >= :gh2
    """)

    # Thực thi truy vấn và lấy kết quả dưới dạng dictionary
    result = db.session.execute(query, {
        'san_bay_di': san_bay_di,
        'san_bay_den': san_bay_den,
        'thoi_gian': thoi_gian_date,
        'gio_bay_toi_da': gio_bay_toi_da,
        'gh1': gh1,
        'gh2': gh2
    }).mappings()  # Trả về kết quả dưới dạng dictionary

    # Chuyển kết quả thành danh sách dict
    flights = []
    for row in result:
        flights.append({
            "id": row['id_TuyenBay'],  # Truy cập bằng tên cột
            "hành_trình": row['tenTuyen'],
            "thời_gian": row['gio_Bay'].strftime('%Y-%m-%d %H:%M:%S'),
            "ghế_hạng_1_còn_trống": row['ghe_hang_1_con_trong'],
            "GH1": row['GH1'],
            "ghế_hạng_2_còn_trống": row['ghe_hang_2_con_trong'],
            "GH2": row['GH2'],
            "sân_bay_trung_gian": "N/A",  # Tạm thời để giá trị mặc định
        })

    return flights


def get_id_san_bay(ten_san_bay_full):
    """
    Tách chuỗi để lấy tên sân bay và dùng nó truy vấn lấy id_SanBay từ bảng SanBay.
    :param ten_san_bay_full: Chuỗi định dạng "sb.ten_SanBay (sb.DiaChi)"
    :return: id_SanBay nếu tìm thấy, None nếu không tìm thấy
    """
    # Tách chuỗi để lấy ten_SanBay
    ten_san_bay = ten_san_bay_full.split('(')[0].strip()

    # Truy vấn để lấy id_SanBay
    query = text("""
        SELECT id_SanBay
        FROM SanBay
        WHERE ten_SanBay = :ten_san_bay
    """)
    result = db.session.execute(query, {'ten_san_bay': ten_san_bay}).fetchone()

    # Trả về id nếu tìm thấy, None nếu không
    return result[0] if result else None  # Truy cập cột đầu tiên (id_SanBay) qua chỉ mục

def get_TuyenBay(id_ChuyenBay):
    # Thực hiện truy vấn và lấy tên tuyến bay tương ứng với id_ChuyenBay
    tuyenbay = db.session.query(TuyenBay.tenTuyen) \
        .join(ChuyenBay, TuyenBay.id_TuyenBay == ChuyenBay.id_TuyenBay) \
        .filter(ChuyenBay.id_ChuyenBay == id_ChuyenBay) \
        .first()

    if tuyenbay:
        return tuyenbay[0]  # Lấy tên tuyến bay (vì first() trả về tuple)
    else:
        return None  # Trường hợp không có dữ liệu, trả về None

def get_flight_by_id(id_chuyen_bay):
    # Truy vấn dữ liệu từ bảng ChuyenBay và TuyenBay
    flight = db.session.query(
        TuyenBay.tenTuyen,
        ChuyenBay.gio_Bay,
        ChuyenBay.GH1 - ChuyenBay.GH1_DD,
        ChuyenBay.GH2 - ChuyenBay.GH2_DD,
        ChuyenBay.GH1,
        ChuyenBay.GH2,
        ChuyenBay.ghes_dadat,
    ).join(ChuyenBay, TuyenBay.id_TuyenBay == ChuyenBay.id_TuyenBay) \
     .filter(ChuyenBay.id_ChuyenBay == id_chuyen_bay).first()

    if flight:
        # Trả về thông tin chuyến bay dưới dạng dictionary
        return {
            'id': id_chuyen_bay,
            'hành_trình': flight.tenTuyen,
            'thời_gian': flight.gio_Bay.strftime('%Y-%m-%d %H:%M'),
            'ghế_hạng_1_còn_trống': flight[2],  # Số ghế hạng 1 còn trống
            'GH1': flight[4],
            'ghế_hạng_2_còn_trống': flight[3],  # Số ghế hạng 2 còn trống
            'GH2': flight[5],
            'ghe_dadat': flight[6],
            'sân_bay_trung_gian': 'N/A'  # Tạm thời, có thể thay đổi sau
        }
    else:
        return None


def save_ticket_info(user_id, seats_info):
    try:
        current_app.logger.info("Bắt đầu lưu thông tin vé và hành khách.")
        current_app.logger.info(f"Dữ liệu đầu vào user_id: {user_id}")

        # Nếu seats_info là một chuỗi, có thể không cần json.loads nữa, chỉ cần xác nhận nó là dictionary hoặc list
        if isinstance(seats_info, str):
            # Nếu dữ liệu là chuỗi, thử chuyển thành dictionary (nếu có thể)
            # Lưu ý: nếu chuỗi này không phải JSON hợp lệ, bạn cần xử lý trường hợp này.
            seats_info = eval(
                seats_info)  # Chỉ nên dùng eval khi bạn chắc chắn dữ liệu hợp lệ (cẩn thận với lỗi bảo mật)

        current_app.logger.info(f"Dữ liệu sau khi xử lý seats_info: {seats_info}")

        # Kiểm tra session
        id_chuyen_bay = session.get('id_chuyen_bay')
        if not id_chuyen_bay:
            current_app.logger.error("Không tìm thấy 'id_chuyen_bay' trong session.")
            return False

        current_app.logger.info(f"ID Chuyến bay: {id_chuyen_bay}")

        # Bắt đầu xử lý từng ghế và hành khách
        for idx, seat_passenger in enumerate(seats_info, start=1):
            current_app.logger.info(f"Xử lý ghế và hành khách thứ {idx}: {seat_passenger}")

            # Lưu thông tin hành khách
            passenger = seat_passenger['passenger']
            current_app.logger.info(f"Dữ liệu hành khách: {passenger}")

            passenger_record = ThongTinHanhKhach(
                HoTen=passenger['name'],
                CCCD=passenger['cccd'],
                SDT=passenger['phone'],
                ID_User=user_id
            )
            db.session.add(passenger_record)
            db.session.commit()  # Lưu và lấy ID
            passenger_id = passenger_record.ID_HanhKhach
            current_app.logger.info(f"Lưu hành khách thành công với ID: {passenger_id}")

            # Lưu thông tin vé
            seat = seat_passenger['seat']
            current_app.logger.info(f"Dữ liệu ghế: {seat}")

            ticket = VeChuyenBay(
                maThongTin=passenger_id,
                giaVe=seat['price'],
                hangVe=1 if seat['class'] == 'Hạng nhất' else 2,
                soGhe=seat['seatNumber'],
                giaHanhLy=0,
                thoiGianDat=datetime.now(),
                id_user=user_id,
                id_ChuyenBay=id_chuyen_bay
            )
            db.session.add(ticket)
            current_app.logger.info(f"Lưu vé thành công cho ghế: {seat['seatNumber']}")

            # Cập nhật `ghes_dadat`
            chuyen_bay = ChuyenBay.query.get(id_chuyen_bay)
            if chuyen_bay:
                current_app.logger.info(f"Trước khi cập nhật ghes_dadat: {chuyen_bay.ghes_dadat}")
                if chuyen_bay.ghes_dadat:
                    chuyen_bay.ghes_dadat += f",{seat['seatNumber']}"
                else:
                    chuyen_bay.ghes_dadat = seat['seatNumber']

                if seat['class'] == 'Hạng nhất':
                    chuyen_bay.GH1_DD += 1  # Tăng GH1_DD nếu là ghế hạng nhất
                else:
                    chuyen_bay.GH2_DD += 1  # Tăng GH2_DD nếu không phải ghế hạng nhất

                db.session.add(chuyen_bay)
                current_app.logger.info(f"Sau khi cập nhật ghes_dadat: {chuyen_bay.ghes_dadat}")
            else:
                current_app.logger.error(f"Không tìm thấy chuyến bay với ID: {id_chuyen_bay}")

        # Commit tất cả thay đổi
        db.session.commit()
        current_app.logger.info("Lưu tất cả thông tin vé và hành khách thành công.")
        return True

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi xảy ra: {e}")
        return False

def format_seats_info(data):
    """
    Hàm này nhận chuỗi dữ liệu gốc và chuyển đổi thành định dạng JSON hợp lệ.
    """
    # Thay thế tất cả dấu '+' bằng dấu cách
    data = data.replace('+', ' ')

    # Loại bỏ dấu chấm trong số tiền (1.500.000 VNĐ -> 1500000 VNĐ)
    data = re.sub(r'(\d+)\.(\d+)\.(\d+)', r'\1\2\3', data)

    # Đảm bảo tất cả các thuộc tính trong chuỗi JSON đều có dấu nháy kép
    # Thêm dấu nháy kép xung quanh các tên thuộc tính như seatNumber, price
    data = re.sub(r'(\w+):', r'"\1":', data)

    # Đảm bảo rằng giá trị của các chuỗi như class, name cũng được bao quanh bởi dấu nháy kép
    data = re.sub(r'("class":|, "name":|, "cccd":|, "phone":)(\w+)', r'\1"\2"', data)

    # Giải quyết phần passengerInfo nếu cần thiết, đảm bảo mọi chuỗi trong đó đều hợp lệ
    data = re.sub(r'(\[.*?\])', lambda m: m.group(0).replace('\'', '"'), data)

    # Thử phân tích chuỗi thành JSON hợp lệ
    try:
        formatted_data = json.loads(data)  # Chuyển đổi thành JSON hợp lệ
        return formatted_data
    except json.JSONDecodeError as e:
        print(f"Lỗi khi phân tích chuỗi JSON: {e}")
        return None



def checkrole(user_roles):
    # Danh sách các vai trò cần kiểm tra
    valid_roles = {UserRole.NhanVien, UserRole.NguoiKiemDuyet, UserRole.NguoiQuanTri}

    # Kiểm tra nếu user_roles là một danh sách, so sánh từng phần tử
    if isinstance(user_roles, list):
        for role in user_roles:
            # So sánh giá trị bên trong ENUM
            if role[0] in valid_roles:  # role[0] là giá trị thực tế của ENUM
                return True
        return False

    # Nếu user_roles là một giá trị đơn lẻ, so sánh trực tiếp
    return user_roles[0] in valid_roles  # So sánh giá trị của ENUM


def change_user_role(user_roles):
    # Nếu user_roles là một danh sách, xử lý từng phần tử trong danh sách
    if isinstance(user_roles, list):
        # Duyệt qua danh sách và lấy tên của mỗi giá trị Enum
        return [role[0].name if isinstance(role[0], Enum) else None for role in user_roles]

    # Nếu user_roles là một giá trị đơn lẻ, trả về tên của phần tử đó
    elif isinstance(user_roles, tuple) and isinstance(user_roles[0], Enum):
        return [user_roles[0].name]

    # Trả về danh sách trống nếu không phải kiểu Enum
    return []


def get_all_tuyen_bay():
    return TuyenBay.query.all()


def get_id_TuyenBay(flight_duration):
    id_TuyenBay = db.session.query(TuyenBay.id_TuyenBay).filter(TuyenBay.tenTuyen == flight_duration).first()
    return id_TuyenBay[0]


def save_ChuyenBay(flight_date, flight_duration, first_class_seats, economy_class_seats, id_TuyenBay):
    try:
        print("Debug: Đang lưu chuyến bay với thông tin sau:")
        print(f"- Ngày giờ bay: {flight_date}")
        print(f"- Thời gian bay: {flight_duration} phút")
        print(f"- Số ghế hạng 1: {first_class_seats}")
        print(f"- Số ghế hạng 2: {economy_class_seats}")
        print(f"- ID tuyến bay: {id_TuyenBay}")

        flight = ChuyenBay(
            gio_Bay=flight_date,
            tG_Bay=flight_duration,
            GH1=first_class_seats,
            GH2=economy_class_seats,
            id_TuyenBay=id_TuyenBay
        )

        db.session.add(flight)
        db.session.commit()  # Lưu chuyến bay vào database

        print("Debug: Chuyến bay đã được lưu thành công. ID chuyến bay:", flight.id_ChuyenBay)

        # Cập nhật số lượt bay (soLuotBay) trong bảng TuyenBay
        route = TuyenBay.query.get(id_TuyenBay)
        if route:
            route.soLuotBay += 1  # Tăng số lượt bay lên 1
            db.session.commit()  # Lưu thay đổi
            print(f"Debug: Cập nhật số lượt bay cho tuyến bay {id_TuyenBay} thành công.")
        else:
            print(f"Warning: Không tìm thấy tuyến bay với ID {id_TuyenBay}.")

        return flight
    except Exception as e:
        print("Error: Xảy ra lỗi khi lưu chuyến bay.")
        print(str(e))
        db.session.rollback()  # Quay lại trạng thái trước khi lỗi xảy ra
        raise e


def save_sbbaytrunggian(intermediate_airports, flight):
    try:
        print("Debug: Đang lưu các sân bay trung gian cho chuyến bay ID:", flight.id_ChuyenBay)

        for idx, airport in enumerate(intermediate_airports):
            print(f"Debug: Sân bay trung gian {idx + 1}:")
            print(f"- Thời gian dừng: {airport['duration']} phút")
            print(f"- Ghi chú: {airport['notes']}")
            print(f"- ID sân bay: {airport['id']}")

            intermediate_airport = SBayTrungGian(
                ThoiGianDung=airport['duration'],
                GhiChu=airport['notes'],
                ID_ChuyenBay=flight.id_ChuyenBay,
                ID_SanBay=getID_SanBay(airport['id'])
            )
            db.session.add(intermediate_airport)

        db.session.commit()  # Lưu tất cả sân bay trung gian vào database
        print("Debug: Các sân bay trung gian đã được lưu thành công.")
    except Exception as e:
        print("Error: Xảy ra lỗi khi lưu các sân bay trung gian.")
        print(str(e))
        db.session.rollback()  # Quay lại trạng thái trước khi lỗi xảy ra
        raise e


def extract_ten_SanBay(full_string):
    """
    Tách tên sân bay từ chuỗi có định dạng 'ten_SanBay (DiaChi)'

    Args:
        full_string (str): Chuỗi chứa thông tin sân bay và địa chỉ.

    Returns:
        str: Tên sân bay (ten_SanBay).
    """
    if '(' in full_string:
        return full_string.split(' (')[0]  # Lấy phần trước dấu '('
    return full_string  # Nếu không có dấu '(', trả về chuỗi ban đầu

def getID_SanBay(param):
    ID_SanBay = db.session.query(SanBay.id_SanBay).filter(SanBay.ten_SanBay == extract_ten_SanBay(param)).first()
    return ID_SanBay[0]


def getquydinhsanbay(id):
    quy_dinh = db.session.query(QuyDinhSanBay).filter_by(ID_QuyDinh=id).first()
    return quy_dinh


def thaydoiquydinhsanbay(id, data):
    # Tìm quy định sân bay trong database
    quy_dinh_san_bay = QuyDinhSanBay.query.get(id)
    if not quy_dinh_san_bay:
        return jsonify({"message": "Không tìm thấy quy định"}), 404

    # Cập nhật dữ liệu từ yêu cầu
    quy_dinh_san_bay.SoLuongSanBay = data.get("SoLuongSanBay", quy_dinh_san_bay.SoLuongSanBay)
    quy_dinh_san_bay.ThoiGianBayToiThieu = data.get("ThoiGianBayToiThieu", quy_dinh_san_bay.ThoiGianBayToiThieu)
    quy_dinh_san_bay.SanBayTrungGianToiDa = data.get("SanBayTrungGianToiDa", quy_dinh_san_bay.SanBayTrungGianToiDa)
    quy_dinh_san_bay.ThoiGianDungToiThieu = data.get("ThoiGianDungToiThieu", quy_dinh_san_bay.ThoiGianDungToiThieu)
    quy_dinh_san_bay.ThoiGianDungToiDa = data.get("ThoiGianDungToiDa", quy_dinh_san_bay.ThoiGianDungToiDa)

    # Lưu thay đổi vào database
    db.session.commit()

    return jsonify({"message": "Cập nhật quy định sân bay thành công"}), 200


def getquydinhbanve(id):
    quy_dinh = QuyDinhBanVe.query.get(id)
    print(quy_dinh)
    return jsonify({
            "ThoiGianBatDauBan": quy_dinh.ThoiGianBatDauBan,
            "ThoiGianKetThucBan": quy_dinh.ThoiGianKetThucBan
        }), 200


def thaydoiquydinhbanve(id, data):
    quy_dinh = QuyDinhBanVe.query.get(id)

    if not quy_dinh:
        return jsonify({"message": "Quy định không tồn tại"}), 404

    quy_dinh.ThoiGianBatDauBan = data.get("ThoiGianBatDauBan", quy_dinh.ThoiGianBatDauBan)
    quy_dinh.ThoiGianKetThucBan = data.get("ThoiGianKetThucBan", quy_dinh.ThoiGianKetThucBan)

    db.session.commit()
    return jsonify({"message": "Cập nhật quy định bán vé thành công"}), 200


def getquydinhve(id):
    quy_dinh=QuyDinhVe.query.get(id)
    if quy_dinh:
        return jsonify({
            "SoLuongHangGhe1": quy_dinh.SoLuongHangGhe1,
            "SoLuongHangGhe2": quy_dinh.SoLuongHangGhe2,
        }), 200


def setquydinhve(id, data):
    quy_dinh1=QuyDinhVe.query.get(id)

    if not quy_dinh1:
        return jsonify({"message": "Quy định không tồn tại"}), 404
    else:
        so_luong_1 = data.get("SoLuongHangGhe1")
        so_luong_2 = data.get("SoLuongHangGhe2")

        if so_luong_1 is None or int(so_luong_1) <= 0:
            return jsonify({"message": "Số lượng hạng ghế 1 phải lớn hơn 0"}), 400
        if so_luong_2 is None or int(so_luong_2) <= 0:
            return jsonify({"message": "Số lượng hạng ghế 2 phải lớn hơn 0"}), 400

        quy_dinh1.SoLuongHangGhe1 = so_luong_1
        quy_dinh1.SoLuongHangGhe2 = so_luong_2

        db.session.commit()
    return True

def get_quy_dinh_san_bay():
    quy_dinh = db.session.query(QuyDinhSanBay).filter(QuyDinhSanBay.ID_QuyDinh == 1).first()
    return quy_dinh

def save_customer_info(hoTen, cccd, sdt, id_user):
    try:
        new_customer = ThongTinHanhKhach(
            HoTen=hoTen,
            CCCD=cccd,
            SDT=sdt,
            ID_User=id_user
        )
        db.session.add(new_customer)
        db.session.commit()
        id_chuyenBay = session.get('maChuyenBay')
        if id_chuyenBay:
            chuyenBay = ChuyenBay.query.get(id_chuyenBay)
            if chuyenBay:
                if session['hangGhe'] == 1:
                    chuyenBay.GH1_DD += session['tongGhe']
                else:
                    chuyenBay.GH2_DD += session['tongGhe']
        db.session.add(chuyenBay)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback nếu có lỗi
        print(f"Error: {str(e)}")


def get_quy_dinh_ve():
    quy_dinh_ve = db.session.query(QuyDinhVe).filter(QuyDinhVe.ID_QuyDinh == 2).first()
    return quy_dinh_ve

def update_user_roles(user_id, new_roles):
    Session = sessionmaker(bind=db.engine)
    session = Session()
    try:
        # Xóa vai trò hiện tại
        existing_roles = session.query(NguoiDung_VaiTro).filter_by(ID_User=user_id).all()
        for role in existing_roles:
            session.delete(role)

        # Thêm vai trò mới
        for role in new_roles:
            new_role = NguoiDung_VaiTro(ID_User=user_id, ID_VaiTro=UserRole[role])
            session.add(new_role)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_chuyen_bay():
    chuyenbay = session.ChuyenBay.query.all()
    return chuyenbay


def dem_tong_tuyem_bay():
    tuyenbay = session.TuyenBay.query.count()
    return tuyenbay

def query_user():
    users = db.session.query(
        NguoiDung
    ).all()
    return users


def get_GioiTinh(gioiTinh):
    if gioiTinh == GioiTinh.Nam:
        return 'Nam'
    if gioiTinh == GioiTinh.Nu:
        return 'Nữ'
    return 'Chưa xác lập'


def get_roles(id_user):
    roles = db.session.query(NguoiDung_VaiTro.ID_VaiTro) \
        .filter(NguoiDung_VaiTro.ID_User == id_user).all()
    return roles


def get_role_name(ID_VaiTro):
    role_mapping = {
        UserRole.NhanVien.value: 'Nhân Viên',
        UserRole.NguoiQuanTri.value: 'Người Quản Trị',
        UserRole.KhachHang.value: 'Khách Hàng',
        UserRole.NguoiKiemDuyet.value: 'Người Kiểm Duyệt',
    }
    return role_mapping.get(ID_VaiTro, 'Không xác định')

def get_all_roles():
    # Truy vấn ID_User và VaiTro từ bảng NguoiDung_VaiTro
    roles = db.session.query(NguoiDung_VaiTro.ID_User, NguoiDung_VaiTro.ID_VaiTro).all()

    # Chuyển giá trị VaiTro thành tên từ enum
    role_data = [(user_id, UserRole(vai_tro).name) for user_id, vai_tro in roles]
    return role_data

# Hàm lấy tất cả UserRole và chuyển thành chữ
def get_all_role_names():
    # Lấy tất cả giá trị của UserRole và chuyển thành tên
    role_names = [role.name for role in UserRole]
    return role_names

def get_GiaVeByByIDSanBay(sanBayDi = None, sanBayDen=None, loaiGhe=None):
    query = BangGiaVe.query.with_entities(BangGiaVe.Gia_Ve)
    if sanBayDi and sanBayDen and loaiGhe:
        query = query.filter(BangGiaVe.ID_SanBayDi == sanBayDi ,
                             BangGiaVe.ID_SanBayDen == sanBayDen,
                             BangGiaVe.LoaiHangGhe.__eq__(loaiGhe))
    return query.first()[0]


def check_email_exists2(email):
    try:
        logging.debug("Đang kiểm tra email: %s", email)
        # Truy vấn ORM để kiểm tra email
        result = db.session.query(NguoiDung).filter(NguoiDung.Email == email).first() is not None
        logging.debug("Kết quả kiểm tra email: %s", result)
        return result
    except SQLAlchemyError as e:
        logging.error("Lỗi khi kiểm tra email: %s", e)
        raise


def add_user2(hoten, email, matkhau, sdt, gioitinh):
    try:
        logging.debug("Đang thêm người dùng với thông tin: Họ tên: %s, Email: %s, SĐT: %s, Giới tính: %s", hoten, email,
                      sdt, gioitinh)

        # Chuyển giá trị giới tính từ số sang Enum
        gioi_tinh_mapping = {
            '1': GioiTinh.Nam,  # Enum.Nam
            '2': GioiTinh.Nu  # Enum.Nu
        }
        gioitinh_enum = gioi_tinh_mapping.get(str(gioitinh))

        if not gioitinh_enum:
            raise ValueError("Giá trị GioiTinh không hợp lệ")

        # Mã hóa mật khẩu
        matkhau_hashed = str(hashlib.md5(matkhau.strip().encode('utf-8')).hexdigest())
        logging.debug("Mật khẩu đã được mã hóa.")

        # Tạo đối tượng người dùng
        new_user = NguoiDung(
            HoTen=hoten,
            Email=email,
            MatKhau=matkhau_hashed,
            SDT=sdt,
            GioiTinh=gioitinh_enum.name  # Lưu tên Enum như 'Nam' hoặc 'Nu'
        )

        # Thêm vào cơ sở dữ liệu
        db.session.add(new_user)
        db.session.commit()
        logging.debug("Người dùng mới đã được thêm với ID: %s", new_user.ID_User)

        return new_user.ID_User  # Trả về ID của người dùng mới
    except SQLAlchemyError as e:
        logging.error("Lỗi khi thêm người dùng: %s", e)
        db.session.rollback()
        raise
    except Exception as ex:
        logging.error("Lỗi ngoại lệ: %s", ex)
        raise


def assign_role_to_user(user_id, role):
    try:
        logging.debug("Đang gán vai trò: %s cho người dùng ID: %s", role, user_id)

        # Chuyển đổi vai trò từ chuỗi sang Enum
        role_mapping = {
            "NhanVien": UserRole.NhanVien,
            "NguoiQuanTri": UserRole.NguoiQuanTri,
            "KhachHang": UserRole.KhachHang,
            "NguoiKiemDuyet": UserRole.NguoiKiemDuyet
        }

        role_enum_value = role_mapping.get(role)

        if not role_enum_value:
            raise ValueError("Vai trò không hợp lệ")

        # Tạo đối tượng ánh xạ giữa người dùng và vai trò
        new_role_mapping = NguoiDung_VaiTro(
            ID_User=user_id,
            ID_VaiTro=role_enum_value
        )

        # Thêm vào cơ sở dữ liệu
        db.session.add(new_role_mapping)
        db.session.commit()
        logging.debug("Vai trò %s đã được gán cho người dùng ID: %s", role_enum_value.name, user_id)
    except SQLAlchemyError as e:
        logging.error("Lỗi khi gán vai trò: %s", e)
        db.session.rollback()
        raise
    except Exception as ex:
        logging.error("Lỗi ngoại lệ: %s", ex)
        raise

#Hàm gọi tên tuyến bay được liên kết với bảng chuyến bay
def get_ten_tuyen_bay(id_tuyen_bay):
    tuyen_bay = TuyenBay.query.filter_by(id_TuyenBay=id_tuyen_bay).first()
    return tuyen_bay.tenTuyen if tuyen_bay else None

def get_chuyen_bay_by_month(month=None):
    """
    Lấy danh sách chuyến bay theo tháng.
    :param month: Tháng cần lọc (1-12). Nếu là None hoặc 'all' thì trả về tất cả chuyến bay.
    :return: Danh sách chuyến bay.
    """
    if month and month != 'all':
        return ChuyenBay.query.filter(extract('month', ChuyenBay.gio_Bay) == int(month)).all()
    return ChuyenBay.query.all()

def update_user(user_id, hoten, email, sdt, gioitinh):
    user = NguoiDung.query.get(user_id)
    if user:
        user.HoTen = hoten
        user.Email = email
        user.SDT = sdt
        user.GioiTinh = gioitinh
        db.session.commit()

def delete_user(user_id):
    user = NguoiDung.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()


# Lấy các vai trò hiện tại của người dùng từ bảng NguoiDung_VaiTro
def get_user_roles(user_id):
    roles = db.session.query(NguoiDung_VaiTro).filter(NguoiDung_VaiTro.ID_User == user_id).all()
    return [role.ID_VaiTro for role in roles]


# Cập nhật vai trò cho người dùng
def update_user_roles2(user_id, roles):
    # Xóa các vai trò cũ
    db.session.query(NguoiDung_VaiTro).filter(NguoiDung_VaiTro.ID_User == user_id).delete()

    # Thêm các vai trò mới
    for role in roles:
        new_role_mapping = NguoiDung_VaiTro(ID_User=user_id, ID_VaiTro=role)
        db.session.add(new_role_mapping)

    db.session.commit()


def cong_doanh_Thu(tbDoanhThu, ttien):
    tuyenBay = TuyenBay.query.filter(TuyenBay.tenTuyen==tbDoanhThu).first()
    if tuyenBay:
        tuyenBay.doanhThu += ttien
        db.session.commit()


# Phương thức lấy dữ liệu bảng BangGiaVe và SanBay kết hợp
def get_bang_gia_ve():
    # Tạo alias cho bảng SanBay
    sanbay_di = aliased(SanBay)
    sanbay_den = aliased(SanBay)

    # Thực hiện truy vấn với các alias
    return db.session.query(BangGiaVe.ID, BangGiaVe.LoaiHangGhe, sanbay_di.ten_SanBay.label('SanBayDi'),
                            sanbay_den.ten_SanBay.label('SanBayDen'), BangGiaVe.Gia_Ve) \
        .join(sanbay_di, BangGiaVe.ID_SanBayDi == sanbay_di.id_SanBay) \
        .join(sanbay_den, BangGiaVe.ID_SanBayDen == sanbay_den.id_SanBay) \
        .order_by(BangGiaVe.ID.asc()) \
        .all()

# Phương thức cập nhật giá vé
def update_gia_ve(id, gia_ve_moi):
    bang_gia_ve = BangGiaVe.query.get(id)
    if bang_gia_ve:
        bang_gia_ve.Gia_Ve = gia_ve_moi
        db.session.commit()
        return True
    return False


def cong_soluongghe(sanbaydi, sanbayden, hangGhe, tongGhe):
    # Truy vấn sân bay đi và đến
    sanBayDi = SanBay.query.filter(SanBay.ten_SanBay == sanbaydi).first()
    sanBayDen = SanBay.query.filter(SanBay.ten_SanBay == sanbayden).first()

    # Kiểm tra nếu sân bay không tồn tại
    if not sanBayDi or not sanBayDen:
        return None

    # Truy vấn tuyến bay
    tuyenbay = TuyenBay.query.filter(
        TuyenBay.id_SanBayDi == sanBayDi.id_SanBay,
        TuyenBay.id_SanBayDen == sanBayDen.id_SanBay
    ).first()

    # Kiểm tra nếu tuyến bay không tồn tại
    if not tuyenbay:
        return None

    # Truy vấn chuyến bay
    chuyenbay = ChuyenBay.query.filter(ChuyenBay.id_TuyenBay == tuyenbay.id_TuyenBay).first()

    # Kiểm tra nếu chuyến bay không tồn tại
    if not chuyenbay:
        return None

    # Cập nhật số lượng ghế đã đặt
    if hangGhe == 1:
        chuyenbay.GH1_DD += tongGhe
    else:
        chuyenbay.GH2_DD += tongGhe

    # Lưu lại thay đổi
    db.session.commit()

    return chuyenbay
