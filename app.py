from flask import Flask, redirect, url_for, render_template, request

import flask_login as login

from wtforms import form, fields, validators
from werkzeug.security import generate_password_hash, check_password_hash

import flask_admin as admin
from flask_admin import helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField
from flask_admin.form import FileUploadInput

from flask_babelex import Babel
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listens_for

import os
import os.path as op

import db_operation as dn

app = Flask(__name__)
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
babel = Babel(app)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/db_tjj_flask'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:linkage@54321@localhost:3306/db_tjj_flask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
app.config['SECRET_KEY'] = '123456'
app.config['FLASK_ADMIN_SWATCH'] = 'Lumen'
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_hans_CN'

file_path = op.join(op.dirname(__file__), 'files')
try:
    os.mkdir(file_path)
except OSError:
    pass

hdjl_left_list = [{'name': '互动交流', 'href': ''},
                  {'name': '统计局统计违法...', 'href': 'report'},
                  {'name': '在线咨询', 'href': 'consult'},
                  {'name': '领导信箱', 'href': 'mail'},
                  {'name': '在线访谈', 'href': 'interview_list'},
                  {'name': '网上调查', 'href': 'survey_theme'},
                  {'name': '常见问题', 'href': 'fqa'}, ]

tjsj_left_list = [{'name': '统计数据', 'href': ''},
                  {'name': '本省数据', 'href': 'report'},
                  {'name': '全国数据', 'href': 'consult'},
                  {'name': '统计制度', 'href': 'consult'},
                  {'name': '统计公报', 'href': 'mail'}, ]

flfgyjd_left_list = [{'name': '法律法规与解读', 'href': ''},
                     {'name': '规范性文件', 'href': 'law_comprehension', 'cate': 'file'},
                     {'name': '相关法律法规', 'href': 'law_comprehension', 'cate': 'law'},
                     {'name': '政策解读', 'href': 'law_comprehension', 'cate': 'policy'}, ]

tjgk_left_list = [{'name': '统计概况', 'href': ''},
                  {'name': '领导介绍', 'href': 'leader_intro'},
                  {'name': '主要职责', 'href': 'main_responsibility'},
                  {'name': '机构设置', 'href': 'organization_list'}]

dftjdcxmgl_left_list = [{'name': '地方统计调查项目管理', 'href': ''},
                        {'name': '有关文件', 'href': 'integration', 'cate': 'relatives'},
                        {'name': '审批程序', 'href': 'integration', 'cate': 'procedure'},
                        {'name': '表格下载', 'href': 'integration', 'cate': 'table'},
                        {'name': '审批公告', 'href': 'integration', 'cate': 'notice'},
                        {'name': '统计制度下载', 'href': 'integration', 'cate': 'sys'},
                        {'name': '统计报表下载', 'href': 'integration', 'cate': 'report'}, ]

czzj_left_list = [{'name': '财政资金', 'href': ''}]
ztjj_left_list = [{'name': '专题聚焦', 'href': ''}]
jsjf_left_list = [{'name': '减税降费', 'href': ''}]
gzdt_left_list = [{'name': '工作动态', 'href': ''}]


class t_user(db.Model):  # 用户表
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String, )
    phone = db.Column(db.String, )
    pwd = db.Column(db.String, )
    role = db.Column(db.String, )

    @property
    def is_authenticated(self):  # flask_login的方法
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.username


class LoginForm(form.Form):  # 登陆表单、验证
    name = fields.StringField(
        validators=[validators.required()],
        render_kw={
            "placeholder": u"姓名",
        },
    )
    phone = fields.StringField(
        validators=[validators.required()],
        render_kw={
            "placeholder": u"手机号",
        },
    )
    password = fields.PasswordField(
        validators=[validators.required()],
        render_kw={
            "placeholder": u"密码",
        },
    )

    def validate_login(self, field):
        user = self.get_user()
        print(user.password)

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.phone != self.phone.data:
            raise validators.ValidationError('Invalid phone number')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(t_user).filter_by(name=self.name.data).first()


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(t_user).get(user_id)


class UserAdmin(ModelView):
    column_labels = {
        'name': u'用户名',
        'phone': u'手机号',
        'pwd': u'密码',
        'role': u'管理角色',
    }

    def is_accessible(self):
        return login.current_user.role == u'用户管理员'


class MyAdminIndexView(admin.AdminIndexView):  # 登录view
    @admin.expose("/")
    def home(self):
        if not login.current_user.is_authenticated:
            print('not login.current_user.is_authenticated')
            return redirect(url_for(".login_view"))  # url_for 函数名
        return super(MyAdminIndexView, self).index()

    @admin.expose("/login/", methods=("GET", "POST"))  # 登录表单
    def login_view(self):
        form = LoginForm(request.form)
        if request.method == 'GET':
            return render_template('admin/login.html', form=form)
        if helpers.validate_form_on_submit(form):  # 验证
            user = form.get_user()
            login.login_user(user)
        if login.current_user.is_authenticated:  # 验证成功
            return redirect(url_for(".home"))
        return super(MyAdminIndexView, self).index()

    @admin.expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.home'))


class t_work(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


# 领导介绍
class t_leader(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(), )
    leader_title = db.Column(db.String(), )
    intro = db.Column(db.Text(), )


# 江西省情
class t_circumstances(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


# 组织结构/机构设置
class t_organization(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    cate = db.Column(db.String())

    def dobule_to_dict(self):
        result = {}
        for key in self.__mapper__.c.keys():
            if getattr(self, key) is not None:
                result[key] = str(getattr(self, key))
            else:
                result[key] = getattr(self, key)
        return result

    def to_json(all_vendors):
        v = [ven.dobule_to_dict() for ven in all_vendors]
        return v


# 专题聚焦
class t_topic(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


class t_fund(db.Model):  # 财政资金
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )

    def dobule_to_dict(self):
        result = {}
        for key in self.__mapper__.c.keys():
            if getattr(self, key) is not None:
                result[key] = str(getattr(self, key))
            else:
                result[key] = getattr(self, key)
        return result

    def to_json(all_vendors):
        v = [ven.dobule_to_dict() for ven in all_vendors]
        return v


class t_law(db.Model):  # 法律法规
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


class t_policy(db.Model):  # 政策解读
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


class t_tax(db.Model):  # 减税降费
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


class t_file(db.Model):  # 规范性文件
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )


@listens_for(t_file, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_jx_data(db.Model):  # 本省数据
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )
    graph = db.Column(db.String(), )


@listens_for(t_jx_data, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_cn_data(db.Model):  # 全国数据
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )
    graph = db.Column(db.String(), )


@listens_for(t_cn_data, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_global_data(db.Model):  # 国际数据
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )
    graph = db.Column(db.String(), )


@listens_for(t_global_data, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_org_qualification(db.Model):  # 涉外机构资格认证
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    file = db.Column(db.String(), )
    datetime = db.Column(db.DateTime(), )
    cate = db.Column(db.String(), )


@listens_for(t_org_qualification, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_proj_exam(db.Model):  # 涉外调查项目审批
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    file = db.Column(db.String(), )
    datetime = db.Column(db.DateTime(), )
    cate = db.Column(db.String(), )


@listens_for(t_proj_exam, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_proj_manage(db.Model):  # 地方统计调查项目管理
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    file = db.Column(db.String(), )
    datetime = db.Column(db.DateTime(), )
    cate = db.Column(db.String(), )


@listens_for(t_proj_manage, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_system(db.Model):  # 统计制度
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    file = db.Column(db.String(), )  # path
    datetime = db.Column(db.DateTime(), )


@listens_for(t_system, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_jx_statistics(db.Model):  # 江西省统计公报
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    file = db.Column(db.String(), )
    datetime = db.Column(db.DateTime(), )


@listens_for(t_jx_statistics, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_jx_survey(db.Model):  # 江西省普查公报
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )


@listens_for(t_jx_survey, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_cn_statistics(db.Model):  # 国家统计公报
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )
    file = db.Column(db.String(), )


@listens_for(t_cn_statistics, 'after_delete')
def del_file(mapper, connection, target):
    if target.path:
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass


class t_interview(db.Model):  # 在线访谈
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


class t_consult(db.Model):  # 在线咨询
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    account = db.Column(db.String(), )
    is_encrypt = db.Column(db.Integer, )
    asker = db.Column(db.String(), )
    phone = db.Column(db.String(), )
    email = db.Column(db.String(), )
    theme = db.Column(db.String(), )
    question = db.Column(db.Text(), )
    ask_time = db.Column(db.Date(), )
    answer = db.Column(db.Text(), )
    ans_time = db.Column(db.Date(), )


class t_report_letter(db.Model):  # 举报信箱
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    account = db.Column(db.String(), )
    is_encrypt = db.Column(db.Integer, )
    asker = db.Column(db.String(), )
    phone = db.Column(db.String(), )
    email = db.Column(db.String(), )
    theme = db.Column(db.String(), )
    question = db.Column(db.Text(), )
    ask_time = db.Column(db.Date(), )
    answer = db.Column(db.Text(), )
    ans_time = db.Column(db.Date(), )


class t_mail(db.Model):  # 领导信箱
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    account = db.Column(db.String(), )
    is_encrypt = db.Column(db.Integer, )
    asker = db.Column(db.String(), )
    phone = db.Column(db.String(), )
    email = db.Column(db.String(), )
    theme = db.Column(db.String(), )
    question = db.Column(db.Text(), )
    ask_time = db.Column(db.Date(), )
    answer = db.Column(db.Text(), )
    ans_time = db.Column(db.Date(), )


class t_survey_theme(db.Model):
    theme_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    theme_title = db.Column(db.String(), )
    theme_start = db.Column(db.Date(), )
    theme_finish = db.Column(db.Date(), )


class t_survey_ques(db.Model):
    ques_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    ques_title = db.Column(db.String(), )
    ques_theme_id = db.Column(db.Integer(), )


class t_survey_ans(db.Model):
    ans_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    ans_title = db.Column(db.String(), )
    ans_ques_id = db.Column(db.Integer(), )


class t_fqa(db.Model):  # 常见问题
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(), )
    content = db.Column(db.Text(), )
    datetime = db.Column(db.DateTime(), )


@listens_for(t_user.pwd, "set", retval=True)
def hash_user_password(target, value, oldvalue, initiator):
    if value != oldvalue:
        return generate_password_hash(value)
    return value


class fileInput(FileUploadInput):
    FileUploadInput.data_template = ('<div>'
                                     ' <input style="border:0" %(text)s>&nbsp;&nbsp;&nbsp;&nbsp;'
                                     ' <input type="checkbox" name="%(marker)s">Delete</input>'
                                     '</div>'
                                     '<input %(file)s>')


class add_ckeditor(ModelView):
    """
        加富文本
    """
    form_overrides = dict(
        content=CKEditorField,
    )
    create_template = 'edit.html'
    edit_template = 'edit.html'


class FileView(add_ckeditor):
    """
        加文件框
    """
    widget = fileInput

    column_exclude_list = ['content', ]

    column_labels = {
        'file': u'文件路径',
        'id': u'序号',
        'title': u'标题',
        'content': u'正文',
        'datetime': u'发布时间',
        'leader_title': u'领导岗位',
        'account': u'查询编号',
        'is_encrypt': u'是否加密',
        'asker': u'提问者',
        'phone': u'预留手机号',
        'email': u'预留邮箱',
        'theme': u'提问主题',
        'question': u'提问正文',
        'ask_time': u'提问时间',
        'answer': u'回答',
        'ans_time': u'回答时间',
        'graph': u'图表',
        'cate': u'分类',
    }

    form_overrides = dict(content=CKEditorField, file=FileUploadField)

    form_args = {
        'file': {
            'base_path': file_path,
            'allow_overwrite': False
        },
        # 'cate': {
        #     'validators': [validators.AnyOf(['flask', 'chocolate'])]
        # },
    }

    def is_accessible(self):
        return login.current_user.role == u'管理员'


@app.route('/consult_list/')
def consult_list():  # 在线咨询列表
    consult_list = dn.get_all_consult()
    return render_template('mail_list.html', data=consult_list, cate='在线咨询',
                           left_list=hdjl_left_list, submit_type='consult', show_type='consult_show')


@app.route('/mail_list/')
def mail_list():  # 领导信箱列表
    mail_list = dn.get_all_mail()
    return render_template('mail_list.html', data=mail_list, cate='领导信箱',
                           left_list=hdjl_left_list, submit_type='mail', show_type='mail_show')


@app.route('/report_list/')
def report_list():  # 举报信列表
    report_list = dn.get_all_report()
    return render_template('mail_list.html', data=report_list, cate='统计违法举报信箱',
                           left_list=hdjl_left_list, submit_type='report', show_type='report_letter_show')


@app.route('/consult_show/<id>')
def consult_show(id):  # 在线咨询详细
    con = dn.get_1_consult(id)
    return render_template('mail_detail.html', con=con, submit_type='consult', left_list=hdjl_left_list)


@app.route('/mail_show/<id>')
def mail_show(id):  # 领导信箱详细
    con = dn.get_1_mail(id)
    return render_template('mail_detail.html', con=con, submit_type='mail', left_list=hdjl_left_list)


@app.route('/report_letter_show/<id>')
def report_letter_show(id):  # 举报信详细
    con = dn.get_1_report_letter(id)
    return render_template('mail_detail.html', con=con, submit_type='report', left_list=hdjl_left_list)


@app.route('/survey_theme/')
def survey_theme():
    theme = dn.get_all_theme()
    return render_template('survey_theme.html', theme=theme, left_list=hdjl_left_list)


@app.route('/data/<cate>')
def data(cate):  # 统计数据列表
    if cate == 'jx':  # 本省数据
        jx_data = dn.get_all_jx_data()
        return render_template('list.html', data=jx_data, left_list=tjsj_left_list)
    elif cate == 'cn':  # 全国数据
        cn_data = dn.get_all_cn_data()
        return render_template('list.html', data=cn_data, left_list=tjsj_left_list)
    elif cate == 'global':  # 国际数据
        global_data = dn.get_all_global_data()
        return render_template('list.html', data=global_data, left_list=tjsj_left_list)


@app.route('/fqa/')
def fqa():  # 常见问题
    fqa = dn.get_all_fqa()
    return render_template('list.html', data=fqa, left_list=hdjl_left_list)


@app.route('/interview_list/')
def interview_list():  # 在线访谈
    interview = dn.get_all_interview()
    return render_template("list.html", data=interview, left_list=hdjl_left_list)


@app.route('/')
def home():  # 主页
    work = dn.get_five_work()
    leader = dn.get_eight_leader()
    fund = dn.get_three_fund()
    fqa = dn.get_ten_fqa()
    work12 = dn.get_12_work()
    theme3 = dn.get_3_theme()
    int9 = dn.get_9_int()
    jx_data5 = dn.get_5_jx_data()
    system5 = dn.get_5_system()
    system9 = dn.get_9_system()
    consult4 = dn.get_4_consult()
    qua5 = dn.get_5_qua()
    qua_tab5 = dn.get_5_qua_tab()
    qua_exam5 = dn.get_5_qua_exam()
    qua_state5 = dn.get_5_qua_state()
    qua_real5 = dn.get_5_qua_real()
    qua_noti = dn.get_5_qua_noti()
    exam5 = dn.get_5_exam()
    exam_tab5 = dn.get_5_exam_table()
    exam_exam5 = dn.get_5_exam_exam()
    exam_state5 = dn.get_5_exam_state()
    exam_real5 = dn.get_5_exam_real()
    exam_noti = dn.get_5_exam_noti()
    mana5 = dn.get_5_mana()
    mana_tab5 = dn.get_5_mana_table()
    mana_real5 = dn.get_5_mana_real()
    mana_noti = dn.get_5_mana_noti()
    return render_template("base_view.html", work=work, fund=fund, leader=leader, fqa=fqa, work12=work12, theme3=theme3,
                           int9=int9, jx_data5=jx_data5, system5=system5, system9=system9, consult4=consult4,
                           qua5=qua5, qua_tab5=qua_tab5, qua_exam5=qua_exam5, qua_state5=qua_state5,
                           qua_real5=qua_real5, qua_noti=qua_noti,
                           exam5=exam5, exam_tab5=exam_tab5, exam_exam5=exam_exam5, exam_state5=exam_state5,
                           exam_real5=exam_real5, exam_noti=exam_noti,
                           mana5=mana5, mana_tab5=mana_tab5, mana_real5=mana_real5, mana_noti=mana_noti,
                           )


@app.route('/law_comprehension/<cate>', methods=['get', 'post'])
def law_comprehension(cate):  # 法律法规与解读
    if cate == "file":  # 规范性文件
        file = dn.get_all_file()
        return render_template("list.html", data=file, left_list=flfgyjd_left_list)
    elif cate == "law":  # 相关法律法规
        law = dn.get_all_law()
        return render_template("list.html", data=law, left_list=flfgyjd_left_list)
    elif cate == "policy":  # 政策解读
        policy = dn.get_all_policy()
        return render_template("list.html", data=policy, left_list=flfgyjd_left_list)


@app.route("/main_responsibility/")
def main_responsibility():
    return render_template("main_responsibility.html", left_list=tjgk_left_list)


@app.route('/integration/<cate>')
def integration(cate):  # 一体化服务
    data = []
    if cate == 'realtives':  # 有关文件
        data = dn.get_all_relatives()
    elif cate == 'procedure':  # 审批程序
        data = dn.get_all_procedure()
    elif cate == 'table':  # 表格下载
        data = dn.get_all_table()
    elif cate == 'notice':  # 审批公告
        data = dn.get_all_notice()
    elif cate == 'sys':  # 统计制度下载
        data = dn.get_all_sys()
    elif cate == 'report':  # 统计报表下载
        data = dn.get_all_statistics()
    return render_template('list.html', data=data, left_list=dftjdcxmgl_left_list)


@app.route("/work_list/")
def work_list():
    work = dn.get_all_work()
    return render_template("list.html", data=work, left_list=gzdt_left_list)


@app.route("/organization_list/")
def organization_list():
    query1 = t_organization.query.filter_by(cate="行政单位")
    cate1 = t_organization.to_json(query1)
    query2 = t_organization.query.filter_by(cate="事业单位")
    cate2 = t_organization.to_json(query2)
    return render_template("organization_list.html", cate1=cate1, cate2=cate2, left_list=tjgk_left_list)


@app.route("/leader_intro/")
def leader_intro():  # 领导介绍
    leader = dn.get_leader_intro()
    return render_template("leader_intro.html", leader=leader, left_list=tjgk_left_list)


@app.route("/fund_list/")
def fund_list():  # 财政资金
    query = t_fund.query.all()
    fund = t_fund.to_json(query)
    return render_template('list.html', data=fund, left_list=czzj_left_list)


@app.route('/consult/')
def consult():  # 在线咨询表单
    return render_template('mail_submit.html', left_list=hdjl_left_list, search_type='consult_list')


@app.route('/report/')
def report():  # 举报信表单
    return render_template('mail_submit.html', left_list=hdjl_left_list, search_type='report_list')


@app.route('/mail/')
def mail():  # 领导信箱表单
    return render_template('mail_submit.html', left_list=hdjl_left_list, search_type='mail_list')


@app.route('/subMail/', methods=['get', 'post'])  # 提交信箱
def subMail():
    account = request.form["account"]
    is_encrypt = request.form["is_encrypt"]
    asker = request.form["asker"]
    phone = request.form["phone"]
    email = request.form["email"]
    theme = request.form["theme"]
    question = request.form["question"]
    cate = request.form['submit_type']  # 提交类型
    if cate == 'mail_list':
        dn.add_2_mail(account, is_encrypt, asker, phone, email, theme, question)
        return redirect(url_for('mail_list'))
    elif cate == 'consult_list':
        dn.add_2_consult(account, is_encrypt, asker, phone, email, theme, question)
        return redirect(url_for('consult_list'))
    elif cate == 'report_list':
        dn.add_2_report_letter(account, is_encrypt, asker, phone, email, theme, question)
        return redirect(url_for('report_list'))


@app.route('/search_list/', methods=['get', 'post'])
def search_list():
    search_key = request.form["ss-k"]
    ans_list = []
    if search_key:
        ans_list.append(t_work.query.filter(t_work.content.like("%" + search_key + "%")))
        ans_list.append(t_circumstances.query.filter(t_circumstances.content.like("%" + search_key + "%")))
        ans_list.append(t_topic.query.filter(t_topic.content.like("%" + search_key + "%")))
        ans_list.append(t_fund.query.filter(t_fund.content.like("%" + search_key + "%")))
        ans_list.append(t_law.query.filter(t_law.content.like("%" + search_key + "%")))
        ans_list.append(t_policy.query.filter(t_policy.content.like("%" + search_key + "%")))
        ans_list.append(t_tax.query.filter(t_tax.content.like("%" + search_key + "%")))
        ans_list.append(t_file.query.filter(t_file.content.like("%" + search_key + "%")))
        ans_list.append(t_jx_data.query.filter(t_jx_data.content.like("%" + search_key + "%")))
        ans_list.append(t_cn_data.query.filter(t_cn_data.content.like("%" + search_key + "%")))
        ans_list.append(t_global_data.query.filter(t_global_data.content.like("%" + search_key + "%")))
        ans_list.append(t_org_qualification.query.filter(t_org_qualification.content.like("%" + search_key + "%")))
        ans_list.append(t_proj_exam.query.filter(t_proj_exam.content.like("%" + search_key + "%")))
        ans_list.append(t_proj_manage.query.filter(t_proj_manage.content.like("%" + search_key + "%")))
        ans_list.append(t_system.query.filter(t_system.content.like("%" + search_key + "%")))
        ans_list.append(t_jx_statistics.query.filter(t_jx_statistics.content.like("%" + search_key + "%")))
        ans_list.append(t_jx_survey.query.filter(t_jx_survey.content.like("%" + search_key + "%")))
        ans_list.append(t_cn_statistics.query.filter(t_cn_statistics.content.like("%" + search_key + "%")))
        ans_list.append(t_interview.query.filter(t_interview.content.like("%" + search_key + "%")))
        ans_list.append(t_fqa.query.filter(t_fqa.content.like("%" + search_key + "%")))
    return render_template('search_list.html', data=ans_list)


@app.route('/topic/')
def topic():  # 专题聚焦列表
    topic = dn.get_all_topic()
    return render_template('list.html', left_list=ztjj_left_list, data=topic)


@app.route('/tax/')
def tax():  # 专题聚焦列表
    tax = dn.get_all_tax()
    return render_template('list.html', left_list=ztjj_left_list, data=tax)


@app.route('/news/<cate>/<data>', methods=['get', 'post'])
def news(cate, data):
    return_data = {}
    print(cate, data)
    if cate == "circumstance":
        return_data = dn.get_circumstances(data)
    elif cate == "work":
        return_data = dn.get_one_work(data)
    elif cate == 'organization':
        return_data = dn.get_one_organization(data)
    elif cate == 'fqa':
        return_data = dn.get_one_fqa(data)
    elif cate == 'interview':
        return_data = dn.get_1_interview(data)
    elif cate == 'sys':
        return_data = dn.get_1_sys(data)
    elif cate == 'jx_data':
        return_data = dn.get_1_jx_data(data)
    elif cate == 'cn':
        return_data = dn.get_1_cn_data(data)
    elif cate == 'global':
        return_data = dn.get_1_global_data(data)
    print(return_data)
    return render_template("news.html", data=return_data)


init_login()
admin = admin.Admin(
    app,
    name=u"统计局管理系统",
    index_view=MyAdminIndexView(),
    base_template='my_master.html',
    template_mode="bootstrap3"
)
admin.add_view(UserAdmin(t_user, db.session, name=u"用户管理"))
admin.add_views(  # 政务公开页面的管理
    FileView(t_work, db.session, name=u"工作动态", category=u"政务公开", endpoint="work"),
    FileView(t_circumstances, db.session, name=u"江西省情", category=u"政务公开", endpoint="circumstances"),
    FileView(t_leader, db.session, name=u"领导介绍", category=u"政务公开", endpoint="leader"),
    FileView(t_organization, db.session, name=u"组织结构", category=u"政务公开", endpoint="organazation"),
    FileView(t_topic, db.session, name=u"专题聚焦", category=u"政务公开", endpoint="topic"),
    FileView(t_fund, db.session, name=u"财政资金", category=u"政务公开", endpoint="fund"),
    FileView(t_law, db.session, name=u"法律法规", category=u"政务公开", endpoint="law"),
    FileView(t_policy, db.session, name=u"政策解读", category=u"政务公开", endpoint="policy"),
    FileView(t_tax, db.session, name=u"减税降费", category=u"政务公开", endpoint="tax"),
)

admin.add_views(  # 统计数据页面的管理
    FileView(t_jx_data, db.session, name=u"本省数据", category=u"统计数据", endpoint="jx_data"),  # 新闻、文件、图表
    FileView(t_cn_data, db.session, name=u"全国数据", category=u"统计数据", endpoint="cn_data"),
    FileView(t_global_data, db.session, name=u"国际数据", category=u"统计数据", endpoint="global_data"),
    FileView(t_system, db.session, name=u"统计制度", category=u"统计数据", endpoint="system"),
    FileView(t_jx_statistics, db.session, name=u"江西省统计公报", category=u"统计数据", endpoint="jx_statistics"),  # pdf
    FileView(t_jx_survey, db.session, name=u"江西省普查公报", category=u"统计数据", endpoint="jx_survey"),  # pdf
    FileView(t_cn_statistics, db.session, name=u"国家统计公报", category=u"统计数据", endpoint="cn_statistics"),  # pdf
)

admin.add_views(  # 网上办事页面的管理
    FileView(t_org_qualification, db.session, name=u"涉外调查机构资格认证", category=u"网上办事", endpoint="org_qualificaton"),  #
    FileView(t_proj_exam, db.session, name=u"涉外调查项目审批", category=u"网上办事", endpoint="proj_exam"),
    FileView(t_proj_manage, db.session, name=u"地方统计调查项目管理", category=u"网上办事", endpoint="proj_manage"),
)

admin.add_views(  # 互动交流页面的管理
    FileView(t_interview, db.session, name=u"在线访谈", category=u"互动交流", endpoint="interview"),  #
    FileView(t_consult, db.session, name=u"在线咨询", category=u"互动交流", endpoint="consult"),
    FileView(t_fqa, db.session, name=u"常见问题", category=u"互动交流", endpoint="fqa"),
    FileView(t_mail, db.session, name=u"领导信箱", category=u"互动交流", endpoint="mail"),
    #     add_ckeditor(t_survey_theme, db.session, name=u"网上调查", category=u"互动交流", endpoint="tax"),  # 棘手啊
    #     add_ckeditor(t_survey_ques, db.session, name=u"网上调查", category=u"互动交流", endpoint="tax"),  # 棘手啊
    #     add_ckeditor(t_survey_ans, db.session, name=u"网上调查", category=u"互动交流", endpoint="tax"),  # 棘手啊
)

if __name__ == '__main__':
    app.run(
        debug=True,
        port=5002,
    )
