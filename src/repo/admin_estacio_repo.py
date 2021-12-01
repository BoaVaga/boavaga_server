from typing import Tuple, Union

from dependency_injector.wiring import inject, Provide
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.container import Container
from src.enums import UserType
from src.models import AdminEstacio
from src.classes import UserSession
from src.services import Crypto


class AdminEstacioRepo:
    EMAIL_JA_CADASTRADO = 'email_ja_cadastrado'
    SEM_PERMISSAO = 'sem_permissao'

    @inject
    def __init__(self, crypto: Crypto = Provide[Container.crypto]):
        self.crypto = crypto

    def create_admin(self, user_sess: UserSession, sess: Session, email: str, senha: str)\
            -> Tuple[bool, Union[str, AdminEstacio]]:
        try:
            if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
                return False, self.SEM_PERMISSAO

            adm = user_sess.user
            estacio_fk = adm.estacio_fk
            if adm.admin_mestre is False or estacio_fk is None:
                return False, self.SEM_PERMISSAO

            hash_senha = self.crypto.hash_password(senha.encode('utf8'))
            admin = AdminEstacio(email=email, senha=hash_senha, estacio_fk=estacio_fk)
            sess.add(admin)
            sess.commit()

            return True, admin
        except IntegrityError:
            sess.rollback()

            return False, self.EMAIL_JA_CADASTRADO
        except Exception:
            sess.rollback()
            raise
