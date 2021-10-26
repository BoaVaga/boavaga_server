import sys

from src.container import create_container
from src.models import AdminSistema, AdminEstacio


def main():
    if len(sys.argv) == 1:
        print('USAGE: python create_admin.py <CONFIG_PATH>')
        exit(0)

    config_path = sys.argv[1]

    container = create_container(config_path)
    session_maker = container.db_session_maker()
    crypto = container.crypto()

    with session_maker() as sess:
        tipo = input('Tipo de admin [(E)stacionamento/(S)istema]: ').strip().upper()
        if tipo not in ['E', 'S']:
            print('Tipo desconhecido')
            return -1

        email = input('Email: ').strip()
        senha = input('Senha: ').strip()
        hash_senha = crypto.hash_password(senha.encode('utf8'))

        if tipo == 'S':
            nome = input('Nome: ').strip()
            adm = AdminSistema(nome=nome, email=email, senha=hash_senha)
        else:
            adm = AdminEstacio(email=email, senha=hash_senha)

        sess.add(adm)
        sess.commit()

        print('Admin cadastrado')


if __name__ == '__main__':
    main()
