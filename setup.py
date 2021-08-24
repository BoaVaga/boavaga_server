import sqlalchemy
from sqlalchemy.ext.compiler import compiles
import sys

from src.container import create_container
from src.models.base import Base
from src.models import *


@compiles(sqlalchemy.LargeBinary, 'mysql')
def compile_binary_mysql(element, compiler, **kw):
    if isinstance(element.length, int) and element.length > 0:
        return f'BINARY({element.length})'
    else:
        return compiler.visit_BLOB(element, **kw)


def main():
    if len(sys.argv) == 1:
        print('USAGE: python setup.py <CONFIG_PATH>')
        exit(0)

    config_path = sys.argv[1]

    container = create_container(config_path)
    db_engine = container.db_engine()

    Base.metadata.create_all(db_engine.engine)

    print('Ok')


if __name__ == '__main__':
    main()
