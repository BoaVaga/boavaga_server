from src.enums import UserType
from src.models import UserSession
from tests.factory import AdminSistemaFactory, set_session


def get_adm_sistema_login(repo_container, crypto, session):
    nome = 'TestUser5741'
    email = 'test_5741@untest.com'
    senha = 'senha123'
    hashed = crypto.hash_password(senha.encode('utf8'))

    set_session(session)
    user = AdminSistemaFactory.create(nome=nome, email=email, senha=hashed)

    repo = repo_container.auth_repo()
    success, token = repo.login(session, email, senha, UserType.SISTEMA)

    user_sess = UserSession(UserType.SISTEMA, user.id)
    return user, user_sess, success, token
