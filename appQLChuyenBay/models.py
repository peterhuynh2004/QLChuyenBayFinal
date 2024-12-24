from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from appQLChuyenBay import db, app

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Float, Date
)
# Đổi tên Enum của SQLAlchemy
from sqlalchemy import Enum as SqlAlchemyEnum

# Đổi tên Enum của Python
from enum import Enum as PyEnum

from sqlalchemy.orm import relationship
from flask_login import UserMixin
import hashlib

# Khai báo Enum Python cho vai trò và giới tính
class UserRole(PyEnum):
    NhanVien = 1
    NguoiQuanTri = 2
    KhachHang = 3
    NguoiKiemDuyet = 4

class GioiTinh(PyEnum):
    Nam = 1
    Nu = 2

# ----------------------------------------------------------------------
# MODELS
# ----------------------------------------------------------------------

class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'NguoiDung'
    ID_User = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(String(255), nullable=False)
    Email = Column(String(255), nullable=False)
    SDT = Column(String(15), nullable=False)  # để lưu SĐT có thể chứa '0' đầu
    TenDangNhap = Column(String(255), nullable=False)
    MatKhau = Column(String(255), nullable=False)
    NgaySinh = Column(DateTime, nullable=True)
    # Dùng Enum của SQLAlchemy, tham chiếu class GioiTinh (Python Enum)
    GioiTinh = Column(SqlAlchemyEnum(GioiTinh, native_enum=False), nullable=False)

    ID_DiaChi = Column(Integer, ForeignKey('DiaChi.ID_DC', ondelete='CASCADE'))
    Avt = Column(String(255), default="https://res.cloudinary.com/ddgxultsd/image/upload/v1732958968/tu5tpwmkwetp4ico5liv.png")

    # Thêm mối quan hệ với bảng NguoiDung_VaiTro
    roles = relationship('NguoiDung_VaiTro', backref='nguoidung', lazy='dynamic')

    def get_id(self):
        return str(self.ID_User)


class NguoiDung_VaiTro(db.Model):
    __tablename__ = 'NguoiDung_VaiTro'
    ID_ND_VT = Column(Integer, primary_key=True, autoincrement=True)
    ID_User = Column(Integer, ForeignKey('NguoiDung.ID_User', ondelete='CASCADE'))
    # Dùng Enum của SQLAlchemy, tham chiếu UserRole
    ID_VaiTro = Column(SqlAlchemyEnum(UserRole, native_enum=False), nullable=False)

    __table_args__ = (
        UniqueConstraint('ID_User', 'ID_VaiTro', name='UC_User_VaiTro'),
    )


class NguoiDungQuyDinh(db.Model):
    __tablename__ = 'NguoiDung_QuyDinh'
    ID_ND_QD = Column(Integer, primary_key=True, autoincrement=True)
    ID_NguoiDung = Column(Integer, ForeignKey('NguoiDung.ID_User'), nullable=False)
    ID_QuyDinh = Column(Integer, ForeignKey('QuyDinh.ID_QuyDinh'), nullable=False)
    thoiGianSua = Column(DateTime, nullable=True)
    lyDoSua = Column(String(255), nullable=True)

    nguoi_dung = relationship('NguoiDung', foreign_keys=[ID_NguoiDung])
    quy_dinh = relationship('QuyDinh', foreign_keys=[ID_QuyDinh])

    __table_args__ = (
        UniqueConstraint('ID_NguoiDung', 'ID_QuyDinh', 'thoiGianSua', name='unique_nguoidung_quydinh'),
    )


class BaoCao(db.Model):
    __tablename__ = 'BaoCao'
    id_BaoCao = Column(Integer, primary_key=True, autoincrement=True)
    thoiGian = Column(DateTime, nullable=False)
    thang = Column(DateTime, nullable=False)
    tongDoanhThu = Column(Integer)
    id_TuyenBay = Column(Integer, ForeignKey('TuyenBay.id_TuyenBay'))
    id_NguoiDung = Column(Integer, ForeignKey('NguoiDung.ID_User'))
    __table_args__ = (
        UniqueConstraint('thang', 'id_TuyenBay', name='UC_Thang'),
    )


class TuyenBay(db.Model):
    __tablename__ = 'TuyenBay'
    id_TuyenBay = Column(Integer, primary_key=True, autoincrement=True)
    tenTuyen = Column(String(255), nullable=False)
    id_SanBayDi = Column(Integer, ForeignKey('SanBay.id_SanBay'))
    id_SanBayDen = Column(Integer, ForeignKey('SanBay.id_SanBay'))
    doanhThu = Column(Integer, nullable=True)
    soLuotBay = Column(Integer, nullable=True)
    tyLe = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('id_SanBayDi', 'id_SanBayDen', name='UQ_SanBay'),
    )


class ChuyenBay(db.Model):
    __tablename__ = 'ChuyenBay'
    id_ChuyenBay = Column(Integer, primary_key=True, autoincrement=True)
    id_TuyenBay = Column(Integer, ForeignKey('TuyenBay.id_TuyenBay'))
    gio_Bay = Column(DateTime)
    tG_Bay = Column(DateTime)
    GH1 = Column(Integer)
    GH2 = Column(Integer)
    GH1_DD = Column(Integer)
    GH2_DD = Column(Integer)


class VeChuyenBay(db.Model):
    __tablename__ = 'VeChuyenBay'
    maVe = Column(Integer, primary_key=True, autoincrement=True)
    giaVe = Column(Integer, nullable=False)
    maThongTin = Column(Integer, ForeignKey('ThongTinHanhKhach.ID_HanhKhach'), nullable=False)
    hangVe = Column(Integer, nullable=False)
    soGhe = Column(Integer, nullable=False)
    giaHanhLy = Column(Integer, nullable=False)
    thoiGianDat = Column(DateTime, nullable=False, default=datetime.utcnow)
    id_user = Column(Integer, ForeignKey('NguoiDung.ID_User'), nullable=False)
    id_ChuyenBay = Column(Integer, ForeignKey('ChuyenBay.id_ChuyenBay'), nullable=False)

    user = relationship('NguoiDung', backref='ve_chuyen_bay')
    chuyen_bay = relationship('ChuyenBay', backref='ve_chuyen_bay')


class DiaChi(db.Model):
    __tablename__ = 'DiaChi'
    ID_DC = Column(Integer, primary_key=True, autoincrement=True)
    ChiTiet = Column(String(255), nullable=False)
    TenDuong = Column(String(255), nullable=False)
    QuanHuyen = Column(String(255), nullable=False)
    TinhTP = Column(String(255), nullable=False)


class SanBay(db.Model):
    __tablename__ = 'SanBay'
    id_SanBay = Column(Integer, primary_key=True, autoincrement=True)
    ten_SanBay = Column(String(255), nullable=False, unique=True)
    DiaChi = Column(String(255), nullable=True)


class SBayTrungGian(db.Model):
    __tablename__ = 'SBayTrungGian'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    ID_ChuyenBay = Column(Integer, ForeignKey('ChuyenBay.id_ChuyenBay'), nullable=False)
    ID_SanBay = Column(Integer, ForeignKey('SanBay.id_SanBay'), nullable=False)
    ThoiGianDung = Column(Integer, nullable=False)
    GhiChu = Column(String(255), nullable=True)


class QuyDinh(db.Model):
    __tablename__ = 'QuyDinh'
    ID_QuyDinh = Column(Integer, primary_key=True, autoincrement=True)
    TenQuyDinh = Column(String(255), nullable=False, unique=True)
    ID_QuyDinhBanVe = Column(Integer, ForeignKey('QuyDinhBanVe.ID'), nullable=False)
    ID_QuyDinhVe = Column(Integer, ForeignKey('QuyDinhVe.ID_QuyDinhVe'), nullable=False)
    ID_QuyDinhSanBay = Column(Integer, ForeignKey('QuyDinhSanBay.ID_QuyDinhSanBay'), nullable=False)
    MoTa = Column(String(500), nullable=True)


class QuyDinhBanVe(db.Model):
    __tablename__ = 'QuyDinhBanVe'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    ThoiGianBatDauBan = Column(Integer, nullable=False)
    ThoiGianKetThucBan = Column(Integer, nullable=False)


class QuyDinhVe(db.Model):
    __tablename__ = 'QuyDinhVe'
    ID_QuyDinhVe = Column(Integer, primary_key=True, autoincrement=True)
    SoLuongHangGhe1 = Column(Integer, nullable=False)
    SoLuongHangGhe2 = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('SoLuongHangGhe1 > 0', name='quydinhve_chk_1'),
        CheckConstraint('SoLuongHangGhe2 > 0', name='quydinhve_chk_2'),
    )


class BangGiaVe(db.Model):
    __tablename__ = 'BangGiaVe'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    LoaiHangGhe = Column(SqlAlchemyEnum('GH1', 'GH2', name='loai_hang_ghe'), nullable=False)
    ThoiGian = Column(Integer, nullable=False)
    ID_SanBayDi = Column(Integer, ForeignKey('SanBay.id_SanBay'), nullable=False)
    ID_SanBayDen = Column(Integer, ForeignKey('SanBay.id_SanBay'), nullable=False)
    ID_PhuThu = Column(Integer, ForeignKey('PhuThuDacBiet.ID'), nullable=True)
    ID_QuyDinhVe = Column(Integer, ForeignKey('QuyDinhVe.ID_QuyDinhVe'), nullable=True)

    san_bay_di = relationship('SanBay', foreign_keys=[ID_SanBayDi])
    san_bay_den = relationship('SanBay', foreign_keys=[ID_SanBayDen])
    phu_thu = relationship('PhuThuDacBiet', backref='bang_gia_ve')

    __table_args__ = (
        UniqueConstraint('ID_SanBayDi', 'ID_SanBayDen', 'LoaiHangGhe', name='unique_sanbay_hangghe'),
    )


class PhuThuDacBiet(db.Model):
    __tablename__ = 'PhuThuDacBiet'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    TenDipLe = Column(String(255), nullable=False)
    NgayBatDau = Column(Date, nullable=False)
    NgayKetThuc = Column(Date, nullable=False)
    PhanTramTang = Column(Float, default=0.0)
    SoTienTang = Column(Float, default=0.0)


class QuyDinhSanBay(db.Model):
    __tablename__ = 'QuyDinhSanBay'
    ID_QuyDinhSanBay = Column(Integer, primary_key=True, autoincrement=True)
    SoLuongSanBay = Column(Integer, nullable=False)
    ThoiGianBayToiThieu = Column(Integer, nullable=False)
    SanBayTrungGianToiDa = Column(Integer, nullable=False)
    ThoiGianDungToiThieu = Column(Integer, nullable=False)
    ThoiGianDungToiDa = Column(Integer, nullable=False)


class ThongTinHanhKhach(db.Model):
    __tablename__ = 'ThongTinHanhKhach'
    ID_HanhKhach = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(String(255), nullable=False)
    CCCD = Column(String(20), nullable=False, unique=True)
    SDT = Column(String(15), nullable=False)
    ID_User = Column(Integer, ForeignKey('NguoiDung.ID_User'), nullable=False)


# ----------------------------------------------------------------------
# TẠO BẢNG & CHÈN DỮ LIỆU MẪU
# ----------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        # Xóa toàn bộ bảng cũ, tạo lại DB sạch
        db.drop_all()
        db.create_all()

        # 1) Thêm NguoiDung trước
        users_data = [
            {
                "HoTen": "Lê Việt Hải Quân",
                "Email": "a@gmail.com",
                "SDT": "0123456789",
                "TenDangNhap": "userA",
                "MatKhau": str(hashlib.md5("pwdA".encode("utf-8")).hexdigest()),
                "NgaySinh": datetime(1990, 1, 1),
                "GioiTinh": GioiTinh.Nam
            },
            {
                "HoTen": "Huỳnh Xuân Chính",
                "Email": "b@gmail.com",
                "SDT": "0987654321",
                "TenDangNhap": "userB",
                "MatKhau": str(hashlib.md5("pwdB".encode("utf-8")).hexdigest()),
                "NgaySinh": datetime(1992, 5, 10),
                "GioiTinh": GioiTinh.Nu
            },
            {
                "HoTen": "Võ Văn Mãi",
                "Email": "c@gmail.com",
                "SDT": "0123123123",
                "TenDangNhap": "userC",
                "MatKhau": str(hashlib.md5("pwdC".encode("utf-8")).hexdigest()),
                "NgaySinh": datetime(1988, 12, 31),
                "GioiTinh": GioiTinh.Nam
            }
        ]

        for u_data in users_data:
            user_obj = NguoiDung(**u_data)
            db.session.add(user_obj)
        db.session.commit()
        print("Đã thêm 3 NguoiDung (User) mẫu.")


        # 2) Thêm dữ liệu mẫu cho bảng SanBay
        airports = [
            {"Sanbay": "Côn Đảo", "Tinh": "Bà Rịa – Vũng Tàu"},
            {"Sanbay": "Phù Cát", "Tinh": "Bình Định"},
            {"Sanbay": "Cà Mau", "Tinh": "Cà Mau"},
            {"Sanbay": "Cần Thơ", "Tinh": "Cần Thơ"},
            {"Sanbay": "Buôn Ma Thuột", "Tinh": "Đắk Lắk"},
            {"Sanbay": "Đà Nẵng", "Tinh": "Đà Nẵng"},
            {"Sanbay": "Điện Biên Phủ", "Tinh": "Điện Biên"},
            {"Sanbay": "Pleiku", "Tinh": "Gia Lai"},
            {"Sanbay": "Cát Bi", "Tinh": "Hải Phòng"},
            {"Sanbay": "Nội Bài", "Tinh": "Hà Nội"},
            {"Sanbay": "Tân Sơn Nhất", "Tinh": "Thành phố Hồ Chí Minh"},
            {"Sanbay": "Cam Ranh", "Tinh": "Khánh Hòa"},
            {"Sanbay": "Rạch Giá", "Tinh": "Kiên Giang"},
            {"Sanbay": "Phú Quốc", "Tinh": "Kiên Giang"},
            {"Sanbay": "Liên Khương", "Tinh": "Lâm Đồng"},
            {"Sanbay": "Vinh", "Tinh": "Nghệ An"},
            {"Sanbay": "Tuy Hòa", "Tinh": "Phú Yên"},
            {"Sanbay": "Đồng Hới", "Tinh": "Quảng Bình"},
            {"Sanbay": "Chu Lai", "Tinh": "Quảng Nam"},
            {"Sanbay": "Phú Bài", "Tinh": "Thừa Thiên Huế"},
            {"Sanbay": "Thọ Xuân", "Tinh": "Thanh Hóa"},
            {"Sanbay": "Vân Đồn", "Tinh": "Quảng Ninh"},
        ]

        for p in airports:
            sb = SanBay(ten_SanBay=p['Sanbay'], DiaChi=p['Tinh'])
            db.session.add(sb)
        db.session.commit()
        print("Đã thêm dữ liệu SanBay.")


        # 3) Thêm dữ liệu mẫu cho bảng TuyenBay
        tuyenbay_data = [
            {"tenTuyen": "Hà Nội - Hồ Chí Minh", "id_SanBayDi": 1, "id_SanBayDen": 2,
             "doanhThu": 100, "soLuotBay": 50, "tyLe": 40},
            {"tenTuyen": "Hà Nội - Đà Nẵng", "id_SanBayDi": 1, "id_SanBayDen": 3,
             "doanhThu": 60, "soLuotBay": 30, "tyLe": 25},
            {"tenTuyen": "Hồ Chí Minh - Đà Nẵng", "id_SanBayDi": 2, "id_SanBayDen": 3,
             "doanhThu": 80, "soLuotBay": 40, "tyLe": 35},
            {"tenTuyen": "Đà Nẵng - Hải Phòng", "id_SanBayDi": 3, "id_SanBayDen": 4,
             "doanhThu": 40, "soLuotBay": 20, "tyLe": 20},
            {"tenTuyen": "Hải Phòng - Cần Thơ", "id_SanBayDi": 4, "id_SanBayDen": 5,
             "doanhThu": 70, "soLuotBay": 35, "tyLe": 30},
        ]

        for data in tuyenbay_data:
            record = TuyenBay(**data)
            db.session.add(record)
        db.session.commit()
        print("Đã thêm dữ liệu TuyenBay.")


        # 4) Thêm dữ liệu mẫu cho bảng ChuyenBay
        chuyenbay_data = [
            {
                "id_TuyenBay": 1,
                "gio_Bay": datetime(2024, 12, 1, 8, 0),
                "tG_Bay": datetime(2024, 12, 1, 10, 0),
                "GH1": 150,
                "GH2": 200,
                "GH1_DD": 140,
                "GH2_DD": 190
            },
            {
                "id_TuyenBay": 2,
                "gio_Bay": datetime(2024, 12, 1, 10, 0),
                "tG_Bay": datetime(2024, 12, 1, 11, 30),
                "GH1": 120,
                "GH2": 180,
                "GH1_DD": 110,
                "GH2_DD": 170
            },
            {
                "id_TuyenBay": 3,
                "gio_Bay": datetime(2024, 12, 1, 14, 0),
                "tG_Bay": datetime(2024, 12, 1, 15, 45),
                "GH1": 130,
                "GH2": 190,
                "GH1_DD": 125,
                "GH2_DD": 185
            },
            {
                "id_TuyenBay": 4,
                "gio_Bay": datetime(2024, 12, 2, 8, 0),
                "tG_Bay": datetime(2024, 12, 2, 10, 0),
                "GH1": 140,
                "GH2": 210,
                "GH1_DD": 135,
                "GH2_DD": 200
            },
            {
                "id_TuyenBay": 5,
                "gio_Bay": datetime(2024, 12, 2, 9, 0),
                "tG_Bay": datetime(2024, 12, 2, 11, 0),
                "GH1": 160,
                "GH2": 220,
                "GH1_DD": 150,
                "GH2_DD": 210
            },
            {
                "id_TuyenBay": 5,
                "gio_Bay": datetime(2024, 12, 2, 9, 0),
                "tG_Bay": datetime(2024, 12, 2, 11, 0),
                "GH1": 160,
                "GH2": 220,
                "GH1_DD": 150,
                "GH2_DD": 210
            },
            {
                "id_TuyenBay": 5,
                "gio_Bay": datetime(2024, 12, 2, 9, 0),
                "tG_Bay": datetime(2024, 12, 2, 11, 0),
                "GH1": 160,
                "GH2": 220,
                "GH1_DD": 150,
                "GH2_DD": 210
            },
            {
                "id_TuyenBay": 5,
                "gio_Bay": datetime(2024, 12, 2, 9, 0),
                "tG_Bay": datetime(2024, 12, 2, 11, 0),
                "GH1": 160,
                "GH2": 220,
                "GH1_DD": 150,
                "GH2_DD": 210
            },
        ]

        for data in chuyenbay_data:
            record = ChuyenBay(**data)
            db.session.add(record)
        db.session.commit()
        print("Đã thêm dữ liệu ChuyenBay.")


        # 5) Thêm dữ liệu mẫu cho bảng BaoCao
        # CHÚ Ý: BaoCao đang tham chiếu id_TuyenBay (1->5) & id_NguoiDung (1->3)
        baocao_data = [
            {
                "thoiGian": datetime(2024, 12, 1, 12, 0),
                "thang": datetime(2024, 12, 1),
                "tongDoanhThu": 100,
                "id_TuyenBay": 1,
                "id_NguoiDung": 1
            },
            {
                "thoiGian": datetime(2024, 12, 1, 13, 0),
                "thang": datetime(2024, 12, 1),
                "tongDoanhThu": 60,
                "id_TuyenBay": 2,
                "id_NguoiDung": 1
            },
            {
                "thoiGian": datetime(2024, 12, 1, 14, 0),
                "thang": datetime(2024, 12, 1),
                "tongDoanhThu": 80,
                "id_TuyenBay": 3,
                "id_NguoiDung": 2
            },
            {
                "thoiGian": datetime(2024, 12, 2, 12, 0),
                "thang": datetime(2024, 12, 2),
                "tongDoanhThu": 40,
                "id_TuyenBay": 4,
                "id_NguoiDung": 2
            },
            {
                "thoiGian": datetime(2024, 12, 2, 13, 0),
                "thang": datetime(2024, 12, 2),
                "tongDoanhThu": 70,
                "id_TuyenBay": 5,
                "id_NguoiDung": 3
            },
        ]

        for data in baocao_data:
            record = BaoCao(**data)
            db.session.add(record)
        db.session.commit()
        print("Đã thêm dữ liệu BaoCao.")

        # 6 - Update) Thêm vai trò cho các NguoiDung đã tạo
        user_roles_data = [
            {"ID_User": 1, "ID_VaiTro": UserRole.NguoiQuanTri},
            {"ID_User": 2, "ID_VaiTro": UserRole.NguoiKiemDuyet},
            {"ID_User": 3, "ID_VaiTro": UserRole.NhanVien},
        ]

        for ur_data in user_roles_data:
            user_role_obj = NguoiDung_VaiTro(**ur_data)
            db.session.add(user_role_obj)
        db.session.commit()
        print("Đã thêm vai trò cho các người dùng.")

        print("TẤT CẢ DỮ LIỆU ĐÃ ĐƯỢC CHÈN THÀNH CÔNG!")
