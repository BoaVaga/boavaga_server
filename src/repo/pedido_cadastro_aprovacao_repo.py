from typing import Tuple, Union, Optional

from sqlalchemy.orm import Session

from src.classes import UserSession, Point
from src.enums import UserType
from src.models import Estacionamento, PedidoCadastro, HorarioPadrao


class PedidoCadastroAprovacaoRepo:
    ERRO_SEM_PERMISSAO = 'sem_permissao'
    ERRO_PEDIDO_NAO_ENCONTRADO = 'pedido_nao_encontrado'

    def accept(self, user_sess: UserSession, sess: Session, pedido_id: str, coordenadas: Point) \
            -> Tuple[bool, Union[Estacionamento, str]]:
        if user_sess is None or user_sess.tipo != UserType.SISTEMA:
            return False, self.ERRO_SEM_PERMISSAO

        pedido: PedidoCadastro = sess.query(PedidoCadastro).get(pedido_id)
        if pedido is None:
            return False, self.ERRO_PEDIDO_NAO_ENCONTRADO

        pedido.endereco.coordenadas = coordenadas

        estacio = Estacionamento(nome=pedido.nome, telefone=pedido.telefone, endereco=pedido.endereco, foto=pedido.foto,
                                 esta_suspenso=False, esta_aberto=False, cadastro_terminado=False, qtd_vaga_livre=0,
                                 horario_padrao=HorarioPadrao())

        sess.add(estacio)
        sess.commit()

        return True, estacio

    def reject(self, user_sess: UserSession, sess: Session, pedido_id: str, motivo: str) -> Tuple[bool, Optional[str]]:
        pass
