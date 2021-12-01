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

    def create_admin(self, sess: Session, email: str, senha: str)\
            -> Tuple[bool, Union[str, AdminEstacio]]:
        try:
            hash_senha = self.crypto.hash_password(senha.encode('utf8'))
            admin = AdminEstacio(email=email, senha=hash_senha, admin_mestre=False)
            sess.add(admin)
            sess.commit()

            return True, admin
        except IntegrityError:
            sess.rollback()

            return False, self.EMAIL_JA_CADASTRADO
        except Exception:
            sess.rollback()
            raise
