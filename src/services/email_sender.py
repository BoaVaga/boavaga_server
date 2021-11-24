import smtplib
import logging
import ssl
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import exc


class EmailSender:
    def __init__(self, host: str, port: int, username: str, password: str, from_addr: str, use_tls = True, timeout = 0) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.timeout = timeout
        self.use_tls = use_tls

        self.connect()

    def connect(self):
        self.server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        if self.use_tls:
            ssl_context = ssl.create_default_context()
            self.server.starttls(context=ssl_context)

        self.server.login(self.username, self.password)
        self._closed = False

    def get_server(self):
        server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        if self.use_tls:
            ssl_context = ssl.create_default_context()
            server.starttls(context=ssl_context)

        server.login(self.username, self.password)
        self._closed = False

        return server

    def send_email_simple(self, dest_addr: str, subject: str, message_text: Optional[None] = None,
                          message_html: Optional[None] = None) -> bool:
        server = None
        try:
            server = self.get_server()

            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_addr
            message['To'] = dest_addr

            if message_text:
                message.attach(MIMEText(message_text, 'plain'))
            if message_html:
                message.attach(MIMEText(message_html, 'html'))

            server.sendmail(self.from_addr, dest_addr, message.as_string())
        except Exception as ex:
            logging.getLogger(__name__).error('Error on send_email_simple', exc_info=ex)
            return False
        finally:
            try:
                if server is not None:
                    server.close()
            except Exception as ex2:
                logging.getLogger(__name__).error('Error on send_email_simple [close]', exc_info=ex)

        return True

    def close(self):
        if not self._closed:
            self.server.quit()
            self._closed = True

    def _check_connect(self):
        try:
            status = self.server.noop()
        except:
            status = -1

        return status == 250
