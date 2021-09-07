from tests.factory import AdminSistemaFactory


def get_adm_sistema_login(container):
    crypto = container.crypto()
    cached = container.cached()

    nome = 'TestUser5741'
    email = 'test_5741@untest.com'
    senha = crypto.hash_password(b'senha123')

    user = AdminSistemaFactory.create(nome=nome, email=email, senha=senha)
    return user
