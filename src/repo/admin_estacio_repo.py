from typing import Tuple, Union, Optional

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
    EMAIL_NOT_FOUND = 'email_not_found'
    ALREADY_ASSIGNED = 'admin_already_assigned'

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

    def add_to_estacio(self, user_sess: UserSession, sess: Session, email: str) -> Tuple[bool, Optional[str]]:
        if user_sess is None or user_sess.tipo != UserType.ESTACIONAMENTO:
            return False, self.SEM_PERMISSAO

        estacio_fk = user_sess.user.estacio_fk
        if user_sess.user.admin_mestre is not True or estacio_fk is None:
            return False, self.SEM_PERMISSAO

        adm: AdminEstacio = sess.query(AdminEstacio).filter(AdminEstacio.email == email).first()
        if adm is None:
            return False, self.EMAIL_NOT_FOUND
        if adm.estacio_fk is not None:
            return False, self.ALREADY_ASSIGNED

        adm.estacio_fk = estacio_fk

        sess.commit()

        return True, None
