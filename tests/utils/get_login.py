from src.enums import UserType
from src.classes import UserSession
from tests.factories import AdminSistemaFactory, set_session, AdminEstacioFactory

_nome = 'Test57410user'
_email_sis = 'test_5741-sis@untest.com'
_email_est = 'test_5741-est@untest.com'
_senha = 'senha123'


def get_adm_sistema_login(repo_container, crypto, session):
    return _general_get_login(repo_container, crypto, session, UserType.SISTEMA, _email_sis)


def get_adm_estacio_login(repo_container, crypto, session):
    return _general_get_login(repo_container, crypto, session, UserType.ESTACIONAMENTO, _email_est)


def get_adm_sistema(crypto, session):
    return _general_get_adm(crypto, session, UserType.SISTEMA, _email_sis)


def get_adm_estacio(crypto, session):
    return _general_get_adm(crypto, session, UserType.ESTACIONAMENTO, _email_est)


def get_all_admins(crypto, session):
    adm_sis, adm_sis_sess = get_adm_sistema(crypto, session)
    adm_est, adm_est_sess = get_adm_estacio(crypto, session)

    return (adm_sis, adm_est), (adm_sis_sess, adm_est_sess)


def _general_get_login(repo_container, crypto, session, tipo, email):
    user, user_sess = _general_get_adm(crypto, session, tipo, email)

    repo = repo_container.auth_repo()
    success, token = repo.login(session, email, _senha, tipo)

    return user, user_sess, success, token


def _general_get_adm(crypto, session, tipo, email):
    hashed = crypto.hash_password(_senha.encode('utf8'))

    set_session(session)
    if tipo == UserType.SISTEMA:
        user = AdminSistemaFactory.create(nome=_nome, email=email, senha=hashed)
    else:
        user = AdminEstacioFactory.create(email=email, senha=hashed)

    user_sess = UserSession(tipo, user.id)
    user_sess.set_db_session(session)
    return user, user_sess

