
from ..config import EMAIL_FROM, EMAIL_SMTP, EMAIL_MESSAGE_TEMPLATE, EMAIL_SUBJECT_TEMPLATE
from . import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.message import Message
from email.utils import formataddr
from .error import Error, ErrorType
import sys, inspect

@ErrorType
class MailError(Error):
	TYPE = "mail"
	FAILED_TO_SEND = "failed_to_send"
	FAILED_TO_BUILD = "failed_to_build"
	SENDER_MISSING = "sender_missing"
	SUBJECT_MISSING = "subject missing"
	MESSAGE_MISSING = "message missing"

def send(to_realname, to_addr, subject, message, from_realname=None, from_addr=None):
	MailError.check(to_realname and to_addr, MailError.SENDER_MISSING, "E-Mail sender is missing", todump=False)
	MailError.check(subject, MailError.SUBJECT_MISSING, "E-mail subject is missing", todump=True)
	MailError.check(message, MailError.MESSAGE_MISSING, "E-mail body is missing", todump=True)

	try:
		msg = MIMEText(EMAIL_MESSAGE_TEMPLATE % {'realname': to_realname, 'message': message}, 'plain', 'utf-8')
		msg['Subject'] = Header(EMAIL_SUBJECT_TEMPLATE % {'subject': subject}, 'utf-8')
		msg['From'] = "%s <%s>" %(Header(from_realname, 'utf-8'), from_addr) if from_realname and from_addr else EMAIL_FROM
		msg['To'] = "%s <%s>" % (Header(to_realname, 'utf-8'), to_addr)

		s = smtplib.SMTP(EMAIL_SMTP)
		s.sendmail(from_addr or EMAIL_FROM, to_addr, msg.as_string())
		s.quit()
	except:
		from .dump import dumpException
		dumpException()
		# this is a problem to be solved by admins or debuggers: don't disturb the rest of the code with non-working e-mail stuff.
		# email notifications are not vital to the functionality of the current call, since there is also a notification.
