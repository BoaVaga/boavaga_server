from typing import Tuple, Union, Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.classes import Point
from src.models import Estacionamento, Endereco


class BuscarEstacioRepo:
    def __init__(self, distancia: int):
        self.distance = distancia

    def buscar(self, sess: Session, coordenadas: Point) -> Tuple[bool, Union[Iterable[Estacionamento], str]]:
        st = f'POINT({coordenadas.x} {coordenadas.y})'
        estacios = sess.query(Estacionamento).join(Endereco).filter(
            func.ST_Distance_Sphere(Endereco.coordenadas, func.st_geomfromtext(st)) <= (self.distance * 1000)
        ).all()

        return True, estacios
