import smtplib
import logging
import ssl
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str, use_tls = True, timeout = 0) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.timeout = timeout

        self.server = smtplib.SMTP(self.host, self.port, timeout=timeout)
        if use_tls:
            ssl_context = ssl.create_default_context()
            self.server.starttls(context=ssl_context)

        self.server.login(self.username, self.password)
        self._closed = False

    def send_email_simple(self, dest_addr: str, subject: str, message_text: Optional[None] = None,
                          message_html: Optional[None] = None) -> bool:
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_addr
            message['To'] = dest_addr

            if message_text:
                message.attach(MIMEText(message_text, 'plain'))
            if message_html:
                message.attach(MIMEText(message_html, 'html'))

            self.server.sendmail(self.from_addr, dest_addr, message.as_string())
        except Exception as ex:
            logging.getLogger(__name__).error('Error on send_email_simple', exc_info=ex)
            return False

        return True

    def close(self):
        if not self._closed:
            self.server.quit()
            self._closed = True
