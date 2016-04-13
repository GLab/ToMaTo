import smtplib
from email.mime.text import MIMEText
from email.header import Header
from .error import Error, ErrorType
from settings import settings, Config
from .exceptionhandling import on_error_continue

@ErrorType
class MailError(Error):
	TYPE = "mail"
	FAILED_TO_SEND = "failed_to_send"
	FAILED_TO_BUILD = "failed_to_build"
	RECEIVER_MISSING = "receiver"
	SUBJECT_MISSING = "subject missing"
	MESSAGE_MISSING = "message missing"

# this is a problem to be solved by admins or debuggers: don't disturb the rest of the code with non-working e-mail stuff.
# email notifications are not vital to the functionality of the current call, since there is also a notification.
@on_error_continue(errorcls_func=lambda e: MailError)
def send(to_realname, to_addr, subject, message, from_realname=None, from_addr=None):
	MailError.check(to_realname and to_addr, MailError.RECEIVER_MISSING, "E-Mail receiver is missing", todump=False)
	MailError.check(subject, MailError.SUBJECT_MISSING, "E-mail subject is missing", todump=True)
	MailError.check(message, MailError.MESSAGE_MISSING, "E-mail body is missing", todump=True)

	mail_settings = settings.get_email_settings(Config.EMAIL_NOTIFICATION)

	msg = MIMEText(mail_settings['body'] % {'realname': to_realname, 'message': message}, 'plain', 'utf-8')
	msg['Subject'] = Header(mail_settings['subject'] % {'subject': subject}, 'utf-8')
	msg['From'] = "%s <%s>" %(Header(from_realname, 'utf-8'), from_addr) if from_realname and from_addr else mail_settings['from']
	msg['To'] = "%s <%s>" % (Header(to_realname, 'utf-8'), to_addr)

	s = smtplib.SMTP(mail_settings['smtp-server'])
	s.sendmail(from_addr or mail_settings['from'], to_addr, msg.as_string())
	s.quit()
