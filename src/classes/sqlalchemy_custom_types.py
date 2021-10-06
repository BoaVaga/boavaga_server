from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.sql.type_api import UserDefinedType

from src.classes.point import Point


class PointType(UserDefinedType):
    def get_col_spec(self):
        return 'POINT'

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)

    @staticmethod
    def result_processor(dialect, col_type):
        '''def process(value):
            return Point.from_string(value)

        return process'''

        return Point.from_string

    @staticmethod
    def bind_processor(dialect):
        '''def process(value):
            return str(value)

        return process'''

        return str
