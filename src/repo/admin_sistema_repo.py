from typing import Tuple, Union

from dependency_injector.wiring import inject, Provide
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.container import Container
from src.models import AdminSistema
from src.services import Crypto, Cached


class AdminSistemaRepo:
    EMAIL_JA_CADASTRADO = 'email_ja_cadastrado'

    @inject
    def __init__(self, crypto: Crypto = Provide[Container.crypto], cached: Cached = Provide[Container.cached]):
        self.crypto = crypto
        self.cached = cached

    def create_admin(self, sess: Session, nome: str, email: str, senha: str) -> Tuple[bool, Union[str, AdminSistema]]:
        try:
            hash_senha = self.crypto.hash_password(senha.encode('utf8'))
            admin = AdminSistema(nome=nome, email=email, senha=hash_senha)
            sess.add(admin)
            sess.commit()

            return True, admin
        except IntegrityError:
            sess.rollback()

            return False, self.EMAIL_JA_CADASTRADO
        except Exception as ex:
            sess.rollback()

            return False, str(ex)
