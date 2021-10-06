from decimal import Decimal
from typing import Union


class Point:
    def __init__(self, x: Union[Decimal, float, str], y: Union[Decimal, float, str]):
        self.x = x if isinstance(x, Decimal) else Decimal(x)
        self.y = y if isinstance(y, Decimal) else Decimal(y)

    def __str__(self):
        return f'POINT({self.x} {self.y})'

    @staticmethod
    def from_string(s: str):
        if s is None or s == '':
            return None

        if not s.startswith('POINT(') or not s.endswith(')'):
            raise AttributeError(f'Invalid point string: {s}')

        v = s[6:-1]
        parts = v.split(' ')

        return Point(Decimal(parts[0]), Decimal(parts[1]))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Point):
            return NotImplemented

        return self.x == other.x and self.y == other.y
