from typing import Tuple

from src.enums import UserType
from src.classes import UserSession
from src.models import AdminEstacio, AdminSistema
from tests.factories import AdminSistemaFactory, set_session, AdminEstacioFactory

_nome = 'Test{}user'
_email_sis = 'test_{}-sis@untest.com'
_email_est = 'test_{}-est@untest.com'
_senha = 'senha123'


def get_adm_sistema_login(repo_container, crypto, session, n=5741):
    return _general_get_login(repo_container, crypto, session, UserType.SISTEMA, _email_sis, n=n)


def get_adm_estacio_login(repo_container, crypto, session, n=5741):
    return _general_get_login(repo_container, crypto, session, UserType.ESTACIONAMENTO, _email_est, n=n)


def get_adm_sistema(crypto, session, n=5741) -> Tuple[AdminSistema, UserSession]:
    return _general_get_adm(crypto, session, UserType.SISTEMA, _email_sis, n=n)


def get_adm_estacio(crypto, session, n=5741) -> Tuple[AdminEstacio, UserSession]:
    return _general_get_adm(crypto, session, UserType.ESTACIONAMENTO, _email_est, n=n)


def get_all_admins(crypto, session, n=5741):
    adm_sis, adm_sis_sess = get_adm_sistema(crypto, session, n=n)
    adm_est, adm_est_sess = get_adm_estacio(crypto, session, n=n)

    return (adm_sis, adm_est), (adm_sis_sess, adm_est_sess)


def _general_get_login(repo_container, crypto, session, tipo, email, n=5741):
    user, user_sess = _general_get_adm(crypto, session, tipo, email, n=n)

    repo = repo_container.auth_repo()
    success, token = repo.login(session, email.format(n), _senha, tipo)

    return user, user_sess, success, token


def _general_get_adm(crypto, session, tipo, email, n=5741):
    hashed = crypto.hash_password(_senha.encode('utf8'))

    set_session(session)
    if tipo == UserType.SISTEMA:
        user = AdminSistemaFactory.create(nome=_nome.format(n), email=email.format(n), senha=hashed)
    else:
        user = AdminEstacioFactory.create(email=email.format(n), senha=hashed)

    user_sess = UserSession(tipo, user.id)
    user_sess.set_db_session(session)
    return user, user_sess

