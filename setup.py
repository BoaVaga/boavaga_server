# AVISO: Código temporário, depois será alterado para usar injeção de dependência

import sqlalchemy
from sqlalchemy.ext.compiler import compiles
import sys

from src.models.base import Base
from src.models import *


@compiles(sqlalchemy.LargeBinary, 'mysql')
def compile_binary_mysql(element, compiler, **kw):
    if isinstance(element.length, int) and element.length > 0:
        return f'BINARY({element.length})'
    else:
        return compiler.visit_BLOB(element, **kw)


if len(sys.argv) == 1:
    print('USAGE: python setup.py DB_CONN_STRING')
    exit(0)

conn_string = sys.argv[1]

engine = sqlalchemy.create_engine(conn_string)
Base.metadata.create_all(engine)

print('Ok')
