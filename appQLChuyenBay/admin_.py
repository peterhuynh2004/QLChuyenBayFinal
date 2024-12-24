from flask_mail import Mail
from sqlalchemy.sql.functions import current_user

from appQLChuyenBay import app, db
from flask_admin import Admin, expose
from flask_admin.contrib.sqla import ModelView
from appQLChuyenBay.models import BaoCao, QuyDinh, UserRole


# def is_accessible(self):
#     return current_user.is_authenticated
#
# # class ViewThongKeBaoCao (ModelView):
# #     @expose('/')
# #     def index(self):
# #         return self.render('admin/thongkebaocao.html')
# #
# #     def is_accessible(self):
# #         return current_user.is_authenticated and current_user.user_role == UserRole.NguoiQuanTri
#
#
# admin.add_view(ModelView(BaoCao , db.session))
# admin.add_view(ModelView(QuyDinh, db.session))
# admin.add_view(ViewThongKeBaoCao(name= 'Stats'))
#
