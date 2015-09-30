
from ..config import EMAIL_FROM, EMAIL_SMTP
from . import logging
import smtplib
from email.mime.text import MIMEText

def send(to, subject, message, from_=None):
	from_ = from_ or EMAIL_FROM
	logging.log(category="mail", to=to, subject=subject, message=message)
	if isinstance(to, list):
		to = ", ".join(to)
	msg = MIMEText(message)
	msg['Subject'] = subject
	msg['From'] = from_
	msg['To'] = to
	try:
		s = smtplib.SMTP(EMAIL_SMTP)
		s.sendmail(from_, to, msg.as_string())
		s.quit()
	except:
		logging.logException()