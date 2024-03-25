from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import os
import smtplib
import traceback
from email.mime.text import MIMEText
from django.conf import settings
import logging

to_mail = [""]
smtpserver = settings.SMTP_SERVER
smtpport = settings.SMTP_PORT
from_mail = settings.SMTP_FROM_EMAIL
password = settings.SMTP_FROM_PASSWORD

def send_mail_with_content(to_addrs=[], title='', content='', file_path=''):
    # 文件正文
    message =  MIMEMultipart()
    message['Subject'] = title
    message['from'] = from_mail
    if settings.SMTP_ADMIN_EMAIL_LIST and isinstance(settings.SMTP_ADMIN_EMAIL_LIST, list):
        to_addrs.extend(settings.SMTP_ADMIN_EMAIL_LIST)
    message['to'] = ','.join(to_addrs)
    message.attach(MIMEText(content, 'html', 'utf-8'))
    # _msg = MIMEText(content, 'html', 'utf-8')
    # 附件
    filename = os.path.basename(file_path)
    attachment = open(file_path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    message.attach(part)

    try:
        smtp = smtplib.SMTP_SSL(smtpserver, smtpport)
        smtp.login(from_mail, password)
        smtp.sendmail(from_mail, to_addrs, message.as_string())
    except Exception as ex:
        logging.error(ex)
        traceback.print_exc(ex)
    finally:
        attachment.close()
        smtp.quit()
