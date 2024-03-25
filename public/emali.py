from email import encoders
from email.mime.base import MIMEBase
import os
import smtplib
import traceback
from email.mime.text import MIMEText
from django.conf import settings
import logging

smtpserver = settings.SMTP_SERVER
smtpport = settings.SMTP_PORT
from_mail = settings.SMTP_FROM_EMAIL
to_mail = [""]
password = settings.SMTP_FROM_PASSWORD

def send_mail_with_html_mimetext(to_addrs=[], title='', content='', file_path=''):

    # 文件正文
    _msg = MIMEText(content, 'html', 'utf-8')
    _msg['Subject'] = title
    _msg['from'] = from_mail
    
    # 附件
    filename = os.path.basename(file_path)
    attachment = open(file_path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    _msg.attach(part)

    if settings.SMTP_ADMIN_EMAIL_LIST and isinstance(settings.SMTP_ADMIN_EMAIL_LIST, list):
        to_addrs.extend(settings.SMTP_ADMIN_EMAIL_LIST)
    _msg['to'] = ','.join(to_addrs)
    try:
        smtp = smtplib.SMTP_SSL(smtpserver, smtpport)
        smtp.login(from_mail, password)
        smtp.sendmail(from_mail, to_addrs, _msg.as_string())
    except Exception as ex:
        logging.error(ex)
        traceback.print_exc(ex)
    finally:
        smtp.quit()
