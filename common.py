#!/bin/python
# -*- coding: utf-8 -*-
# Author: Syman Li
# @Time : 2019-06-05 10:57
from ldap3 import Connection, Server
from ldap3 import SIMPLE, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPConstraintViolationResult, \
    LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError, \
    LDAPSocketOpenError, LDAPExceptionError
from email.mime.text import MIMEText
from email.header import Header
from os import environ, path
import os
import time
import random
import smtplib
import sqlite3 as sql

def connect_ldap(conf, **kwargs):
    server = Server(host=conf['host'],
                    port=conf.getint('port', None),
                    use_ssl=conf.getboolean('use_ssl', False),
                    connect_timeout=5)

    return Connection(server, raise_exceptions=True, **kwargs)

def change_passwords(username, old_pass, new_pass):
    changed = []

    for key in (key for key in CONF.sections()
                if key == 'ldap' or key.startswith('ldap:')):

        LOG.debug("Changing password in %s for %s" % (key, username))
        try:
            change_password(CONF[key], username, old_pass, new_pass)
            changed.append(key)
        except Error as e:
            for key in reversed(changed):
                LOG.info("Reverting password change in %s for %s" % (key, username))
                try:
                    change_password(CONF[key], username, new_pass, old_pass)
                except Error as e2:
                    LOG.error('{}: {!s}'.format(e.__class__.__name__, e2))
            raise e

def change_password(conf, *args):
    try:
        if conf.get('type') == 'ad':
            change_password_ad(conf, *args)
        else:
            change_password_ldap(conf, *args)

    except (LDAPBindError, LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError):
        raise Error('Username or password is incorrect!')

    except LDAPConstraintViolationResult as e:
        # Extract useful part of the error message (for Samba 4 / AD).
        msg = e.message.split('check_password_restrictions: ')[-1].capitalize()
        raise Error(msg)

    except LDAPSocketOpenError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Error('Unable to connect to the remote server.')

    except LDAPExceptionError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Error('Encountered an unexpected error while communicating with the remote server.')

def change_password_ldap(conf, username, old_pass, new_pass):
    with connect_ldap(conf) as c:
        user_dn = find_user_dn(conf, c, username)

    # Note: raises LDAPUserNameIsMandatoryError when user_dn is None.
    with connect_ldap(conf, authentication=SIMPLE, user=user_dn, password=old_pass) as c:
        c.bind()
        c.extend.standard.modify_password(user_dn, old_pass, new_pass)

def change_password_ad(conf, username, old_pass, new_pass):
    user = username + '@' + conf['ad_domain']

    with connect_ldap(conf, authentication=SIMPLE, user=user, password=old_pass) as c:
        c.bind()
        user_dn = find_user_dn(conf, c, username)
        c.extend.microsoft.modify_password(user_dn, new_pass, old_pass)

def find_user_dn(conf, conn, uid):
    try:
        search_filter = conf['search_filter'].replace('{uid}', uid)
        conn.search(conf['base'], "(%s)" % search_filter, SUBTREE)

        return conn.response[0]['dn'] if conn.response else None
    except Exception as e:
        LOG.info("error dn" + e)

def find_user_dn_email(conf, conn, uid):
    try:
        search_filter = conf['search_filter'].replace('{uid}', uid)
        conn.search(conf['base'], "(%s)" % search_filter, SUBTREE,attributes=["*"])
        return (conn.response[0]['attributes']['mail'],conn.response[0]['attributes']['userAccountControl'],conn.response[0]['attributes']['cn']) if conn.response else None
    except Exception as e:
        LOG.info(e)

def reset_ldap_password(conf, conn, uid,new_password):
    user = uid + '@' + conf['ad_domain']

    with connect_ldap(conf, authentication=SIMPLE, user=conf['ldap_user'], password=conf['ldap_password']) as c:
        c.bind()
        user_dn = find_user_dn(conf, c, uid)
        cresult = c.extend.microsoft.modify_password(user_dn, new_password=new_password)
def checkcode():
    code = ''
    for i in range(4):
        current = random.randrange(0,4)
        if current == i:
            tep = chr(random.randint(65,90))
        else:
            tep = random.randint(0,9)
        code+=str(tep)
    return code

BASE_DIR = os.path.dirname(__file__)
class SqlLite_Conn():
    def __init__(self):
        self.conn = sql.connect(os.path.join(BASE_DIR, 'app.db'))
        self.cur = self.conn.cursor()
        self.conn.execute("CREATE TABLE IF NOT EXISTS verify_code(id primary key,uid ,code,recv_addr,times)")
    def select(self,uid,code):
        try:
            # self.cur.execute("select * from verify_code where uid=%s and code=%s and dates > 1 " %(uid,code))
            cur_time = int(time.time())
            select_result = self.cur.execute("select * from verify_code where uid='%s' and code='%s' and %d - times < 10000 " %(uid,code,cur_time))
            result = self.cur.fetchall()
            if result:
                return True
            return False
        except Exception as e:
            print(e)
            return False
    def insert(self,msg):
        try:
            if self.conn:
                #%(uid)s,%(code)s,%(times)s
                self.cur.execute("insert into  verify_code ('uid','code','recv_addr','times') values ('%(uid)s','%(code)s','%(recv_addr)s','%(times)s')" % msg)
                self.conn.commit()
                return True
        except Exception as e:
            print(e)
            return False

    def close(self):
        self.cur.close()
        self.conn.close()


def sendmail(CONF,msg):

    conf = CONF['mail']
    mail_host = conf['mail_host']
    mail_user = conf['mail_user']
    mail_pass = conf['mail_pass']
    subject = '密码重置验证(E-mail verification)'

    mail_msg = """
    <p>尊敬的 %(name)s :</p>
    <p>您重置AD登陆账户的验证码为 %(code)s,验证码将在5分钟后失效，请点击以下链接完成密码重置！</p>
    <p><a>重置连接:&nbsp;&nbsp;</a><a href="http://192.168.10.84/reset_confirm.html?uid=%(uid)s">http://192.168.10.84/reset_confirm.html?uid=%(uid)s</a></p>
    """% msg
    message = MIMEText(mail_msg, 'html', 'utf-8')
    message['From'] = Header(mail_user, 'utf-8')
    message['To'] = Header(msg['recv_addr'], 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host)
        smtpObj.login(mail_user,mail_pass)
        smtpObj.sendmail(mail_user, msg['recv_addr'], message.as_string())
        # LOG.info('发送成功')
        return  True
    except Exception as e:
        # LOG.info(e)
        return False
