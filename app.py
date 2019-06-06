#!/usr/bin/env python3

import bottle
from bottle import get, post, static_file, request, route, template
from bottle import SimpleTemplate
from configparser import ConfigParser
from ldap3 import Connection, Server
from ldap3 import SIMPLE, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPConstraintViolationResult, \
    LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError, \
    LDAPSocketOpenError, LDAPExceptionError
import time
import logging
import os
import random
import smtplib
import sqlite3 as sql
from common import  *
from email.mime.text import MIMEText
from email.header import Header
from os import environ, path


print(__file__)
BASE_DIR = path.dirname(__file__)
LOG = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
VERSION = '2.1.0'


@get('/')
def get_index():
    return index_tpl()

@post('/')
def post_index():
    form = request.forms.getunicode
    def error(msg):
        return index_tpl(username=form('username'), alerts=[('error', msg)])

    if form('new-password') != form('confirm-password'):
        return error("两次密码不匹配！")

    if len(form('new-password')) < 8:
        return error("密码长度太短了，需要8位以上！")
    try:
        change_passwords(form('username'), form('old-password'), form('new-password'))
    except Error as e:
        LOG.warning("Unsuccessful attempt to change password for %s: %s" % (form('username'), e))
        return error(str(e))

    LOG.info("密码更新成功: %s" % form('username'))

    return index_tpl(alerts=[('success', "密码设置成功！")])

@get('/reset.html')
def get_index():
    return reset_tpl()

@post('/reset.html')
def post_reset():
    form = request.forms.getunicode

    def error(msg):
        return reset_tpl(username=form('username'), alerts=[('error', msg)])
    if form('username'):
        try:
            conf= CONF['ldap:0']
            server = Server(conf['host'],use_ssl=True, get_info='ALL')
            conn = Connection(server, auto_bind=True, client_strategy='SYNC', user=conf['ldap_user'],
                              password=conf['ldap_password'], authentication='SIMPLE', check_names=True)
            find_user_result = find_user_dn(conf,conn,form('username'))
            if find_user_result:
                find_mail_result = find_user_dn_email(conf, conn, form('username'))
                if find_mail_result:
                    if str(find_mail_result[1]) != '514':
                        msg={}
                        msg['code'] = checkcode()
                        msg['uid'] = form('username')
                        msg['name'] = find_mail_result[2]
                        msg['times']= int(time.time())
                        msg['recv_addr'] = find_mail_result[0]
                        conn = SqlLite_Conn()
                        db_result = conn.insert(msg)
                        conn.close()
                        mail_result = sendmail(CONF,msg)
                        if not mail_result and not db_result :
                            return reset_tpl(alerts=[('error', "系统故障，邮件发送失败，请联系管理员！")])
                        return reset_tpl(alerts=[('success', "已发送重置邮件至 %s" % find_mail_result[0])])
                    else:
                        return reset_tpl(alerts=[('error', "用户禁用状态，禁止重置密码,请联系管理员！")])
                else:
                    return reset_tpl(alerts=[('error', "找到用户,邮箱未配置,无法接收重置邮件,请联系管理员！")])
            else:
                return reset_tpl(alerts=[('error', "未找到用户！")])

        except Exception as e:
            LOG.info(e)

@get('/reset_confirm.html')
def get_reset_confirm():
    uid=request.GET.get('uid')
    return template('reset_confirm',{'uid':uid})

@post('/reset_confirm.html')
def post_reset_confirm():
    uid = request.GET.get('uid') if request.GET.get('uid') else None
    form = request.forms.getunicode

    confirm_code = form('code-confirm')

    def error(msg):
        return reset_confirm_tpl(uid=uid, alerts=[('error', msg)])

    db_conn = SqlLite_Conn()
    db_result = db_conn.select(uid,confirm_code)
    if not confirm_code:
        return error("请输入验证码！")

    if not db_result:
        return error("验证码输入错误！")

    if form('new-password') != form('confirm-password'):
        return error("两次密码不匹配！")

    if len(form('new-password')) < 8:
        return error("密码长度太短，至少8位并且包含大小写、数字！")

    try:
        conf = CONF['ldap:0']
        server = Server(conf['host'], use_ssl=True, get_info='ALL')
        conn = Connection(server, auto_bind=True, client_strategy='SYNC', user=conf['ldap_user'],
                          password=conf['ldap_password'], authentication='SIMPLE', check_names=True)
        reset_ldap_password(conf,conn, uid, form('new-password'))
    except Error as e:
        LOG.warning("Unsuccessful attempt to change password for %s: %s" % (form('username'), e))
        return error(str(e))

    LOG.info("密码更新成功: %s" % form('username'))

    return reset_confirm_tpl(uid=uid,alerts=[('success', "密码设置成功！")])

@route('/static/<filename>', name='static')
def serve_static(filename):
    return static_file(filename, root=path.join(BASE_DIR, 'static'))

def index_tpl(**kwargs):
    return template('index', **kwargs)

def reset_tpl(**kwargs):
    return template('reset', **kwargs)

def reset_confirm_tpl(**kwargs):
    return template('reset_confirm', **kwargs)

class Error(Exception):
    pass

class MyParser(ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k]=dict(d[k])
        return d
def read_config():
    config = MyParser()
    config.read([path.join(BASE_DIR, 'settings.ini'), os.getenv('CONF_FILE', '')],encoding='utf-8')
    return config



if environ.get('DEBUG'):
    bottle.debug(True)

# Set up logging.
logging.basicConfig(format=LOG_FORMAT)
LOG.setLevel(logging.DEBUG)
LOG.info("Starting AD-passwd-webui %s" % VERSION)
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
LOG.addHandler(console_handler)



CONF = read_config()

bottle.TEMPLATE_PATH = [BASE_DIR]

# Set default attributes to pass into templates.
SimpleTemplate.defaults = dict(CONF['html'])
SimpleTemplate.defaults['url'] = bottle.url


# Run bottle internal server when invoked directly (mainly for development).
if __name__ == '__main__':
    bottle.run(**CONF['server'])
# Run bottle in application mode (in production under uWSGI server).
else:
    application = bottle.default_app()
