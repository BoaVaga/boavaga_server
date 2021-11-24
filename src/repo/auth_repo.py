from datetime import datetime
import logging
from typing import Optional, Tuple

from dependency_injector.wiring import Provide, inject
from sqlalchemy.orm import Session

from src.container import Container
from src.enums import UserType
from src.models import AdminSistema, AdminEstacio, SenhaRequest
from src.classes import UserSession
from src.services import Crypto, Cached
from src.services.email_sender import EmailSender


class AuthRepo:
    SENHA_INCORRETA = 'senha_incorreta'
    EMAIL_NAO_ENCONTRADO = 'email_nao_encontrado'
    ERRO_ENVIO_EMAIL = 'erro_envio_email'
    ERRO_CODIGO_INVALIDO = 'codigo_invalido'

    SESS_TOKEN_GROUP = 'sess_token'
    REVERSE_SESS_TOKEN_GROUP = 'rev_sess_token'

    RESET_PASSWD_SUBJECT = 'Recuperação de Senha BoaVaga'

    @inject
    def __init__(self, crypto: Crypto = Provide[Container.crypto], cached: Cached = Provide[Container.cached],
                 email_sender: EmailSender = Provide[Container.email_sender]):
        self.crypto = crypto
        self.cached = cached
        self.email_sender = email_sender

    def login(self, sess: Session, email: str, senha: str, tipo: UserType) -> Tuple[bool, str]:
        if tipo == UserType.SISTEMA:
            admin = sess.query(
                AdminSistema.id, AdminSistema.senha
            ).filter(AdminSistema.email == email).first()
        else:
            admin = sess.query(
                AdminEstacio.id, AdminEstacio.senha
            ).filter(AdminEstacio.email == email).first()

        if admin is not None:
            if self.crypto.check_password(senha.encode('utf8'), admin.senha):
                reverse_key = self._gen_reverse_session_key(tipo, admin.id)
                old_token = self.cached.get(self.REVERSE_SESS_TOKEN_GROUP, reverse_key)

                if old_token is not None:
                    self.cached.remove(self.SESS_TOKEN_GROUP, old_token)

                user_session = UserSession(tipo, admin.id)
                token = self._gen_token(old_token)

                self.cached.set(self.SESS_TOKEN_GROUP, token, user_session.to_simple_user_sess())
                self.cached.set(self.REVERSE_SESS_TOKEN_GROUP, reverse_key, token)

                return True, token
            else:
                return False, self.SENHA_INCORRETA
        else:
            return False, self.EMAIL_NAO_ENCONTRADO

    def enviar_email_senha(self, sess: Session, email: str, tipo: UserType) -> Tuple[bool, Optional[str]]:
        code = self.crypto.random_hex_string(4)
        if tipo == UserType.ESTACIONAMENTO:
            user = sess.query(AdminEstacio.id).filter(AdminEstacio.email == email).first()
        else:
            user = sess.query(AdminSistema.id).filter(AdminSistema.email == email).first()

        if user is None:
            return False, self.EMAIL_NAO_ENCONTRADO

        req = SenhaRequest(code=code, data_criacao=datetime.now())
        if tipo == UserType.ESTACIONAMENTO:
            req.admin_estacio_fk = user.id
            query_exists = sess.query(SenhaRequest).filter(SenhaRequest.admin_estacio_fk == user.id).exists()
        else:
            req.admin_sistema_fk = user.id
            query_exists = sess.query(SenhaRequest).filter(SenhaRequest.admin_sistema_fk == user.id).exists()

        try:
            success_email = self.email_sender.send_email_simple(email, self.RESET_PASSWD_SUBJECT, message_text=code, message_html=None)
        except Exception as ex:
            logging.getLogger(__name__).error('Error on enviar_email_senha()', exc_info=ex)
            success_email = False

        if success_email is not True:
            return False, self.ERRO_ENVIO_EMAIL

        if sess.query(query_exists).scalar():
            return True, None

        sess.add(req)
        sess.commit()

        return True, None

    def recuperar_senha(self, sess: Session, nova_senha: str, code: str) -> Tuple[bool, Optional[str]]:
        req = sess.query(SenhaRequest.admin_estacio_fk, SenhaRequest.admin_sistema_fk).filter(SenhaRequest.code == code).first()
        if req is None:
            return False, self.ERRO_CODIGO_INVALIDO

        if req.admin_estacio_fk is not None:
            user = sess.query(AdminEstacio).get(req.admin_estacio_fk)
        else:
            user = sess.query(AdminSistema).get(req.admin_sistema_fk)

        user.senha = self.crypto.hash_password(nova_senha.encode('utf8'))
        sess.query(SenhaRequest).filter(SenhaRequest.code == code).delete()

        sess.commit()

        return True, None

    @staticmethod
    def _gen_reverse_session_key(tipo: UserType, user_id: int) -> str:
        return str(tipo.value) + ':' + str(user_id)

    def _gen_token(self, old_token: str) -> str:
        token = None
        while token is None or self.cached.contains(self.SESS_TOKEN_GROUP, token) or token == old_token:
            token = self.crypto.random_hex_string(16)

        return token
