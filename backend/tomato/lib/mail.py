
from ..config import EMAIL_FROM, EMAIL_SMTP, EMAIL_MESSAGE_TEMPLATE, EMAIL_SUBJECT_TEMPLATE
from . import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.message import Message
from email.utils import formataddr

def send(to_realname, to_addr, subject, message, from_realname=None, from_addr=None):
	msg = Message()
	msg['Subject'] = Header(EMAIL_SUBJECT_TEMPLATE % {'subject': subject}, 'iso-8859-1')
	msg['From'] = formataddr((Header(from_realname, 'iso-8859-1'), from_addr)) if from_realname and from_addr else EMAIL_FROM
	msg['To'] = formataddr((Header(to_realname, 'iso-8859-1'), to_addr))
	msg.set_payload(EMAIL_MESSAGE_TEMPLATE % {'realname': to_realname, 'message': message})
	print "here"
	print msg.as_string()
	print "__jfdklsajfkdlsa"
	print msg

	try:
		s = smtplib.SMTP(EMAIL_SMTP)
		s.sendmail(from_addr or EMAIL_FROM, to_addr, msg.as_string())
		s.quit()
	except:
		logging.logException()