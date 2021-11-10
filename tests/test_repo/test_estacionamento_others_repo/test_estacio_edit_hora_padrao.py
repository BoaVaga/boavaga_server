import datetime
from decimal import Decimal
import unittest
from src.models.estacionamento import Estacionamento
from src.models import ValorHora, HorarioPadrao
from tests.factories.factory import ValorHoraFactory
from tests.test_repo.test_estacionamento_others_repo.base import BaseTestEstacioOthers

_DIAS = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


class TestEstacioEditHoraPadrao(BaseTestEstacioOthers):
    def _test_general_edit_ok(self, user_sess, dia, h_abre='def', h_fec='def', estacio='def', estacio_id='def'):
        estacio_id = None if estacio_id == 'def' else estacio_id
        estacio = user_sess.user.estacionamento if estacio_id is None else self.session.query(Estacionamento).get(estacio_id)
        
        h_abre = datetime.time(10, 0, 0) if h_abre == 'def' else h_abre
        h_fec = datetime.time(20, 0, 0) if h_fec == 'def' else h_fec
        
        ori_hora_p = HorarioPadrao.from_dict(HorarioPadrao.to_dict(estacio.horario_padrao))
        success, hora_p = self.repo.edit_horario_padrao(user_sess, self.session, dia, h_abre, h_fec, estacio_id=estacio_id)

        self.assertEqual(True, success, f'Sucess should be True. Error: {hora_p}')

        for d in _DIAS:
            _abr, _fec = getattr(hora_p, f'{d}_abr'), getattr(hora_p, f'{d}_fec')

            if d == dia.strip().lower():
                self.assertEqual(h_abre, _abr, f'Hora abre should change ({d})')
                self.assertEqual(h_fec, _fec, f'Hora fecha should change ({d})')
            else:
                self.assertEqual(getattr(ori_hora_p, f'{d}_abr'), _abr, f'Hora abre should keep ({d})')
                self.assertEqual(getattr(ori_hora_p, f'{d}_fec'), _fec, f'Hora fecha should keep ({d})')

        self.assertEqual(hora_p.id, estacio.horap_fk, f'Hora padrao fk should match')

    def test_edit_horap_ok(self):
        self._test_general_edit_ok(self.adm_estacio_sess, 'segunda')

    def test_edit_horap_ok_adm_sis(self):
        self._test_general_edit_ok(self.adm_sis_sess, 'quarta', estacio_id=str(self.estacios[1].id))

    def test_edit_horap_all_days_ok(self):
        _MODOS = (
            lambda s: '   ' + s + '   ',
            lambda s: s.upper(),
            lambda s: s.capitalize(),
            lambda s: ''.join([s[i].upper() if i % 2 == 0 else s[i] for i in range(len(s))]),
            lambda s: s
        )

        for dia in _DIAS:
            for modo in _MODOS:
                fdia = modo(dia)
                self._test_general_edit_ok(self.adm_estacio_sess, fdia)

    def test_edit_horap_sem_permissao(self):
        success, error = self.repo.edit_horario_padrao(None, self.session, 'segunda', datetime.time(1), datetime.time(2))

        self.assertEqual('sem_permissao', error, 'Error should be "sem_permissao"')
        self.assertEqual(False, success, 'Success should be False')

    def test_edit_horap_dia_invalido(self):
        for d in ['segundaA', 'asddAaAAA', '11232', '0terca', 'terça', 'sábado']:
            success, error = self.repo.edit_horario_padrao(self.adm_estacio_sess, self.session, d, datetime.time(1),
                                                           datetime.time(2))

            self.assertEqual('dia_invalido', error, f'Error should be "dia_invalido" on "{d}"')
            self.assertEqual(False, success, f'Success should be False on "{d}"')

    def test_edit_horap_fecha_antes_de_abrir(self):
        _TESTS = (
            (datetime.time(10, 30, 0), datetime.time(10, 29, 0)),
            (datetime.time(10, 30, 0), datetime.time(10, 30, 0)),
            (datetime.time(10, 30, 0), datetime.time(9, 31, 0))
        )

        for i in range(len(_TESTS)):
            abr, fec = _TESTS[i]
            success, error = self.repo.edit_horario_padrao(self.adm_estacio_sess, self.session, 'terca', abr, fec)
            
            self.assertEqual('hora_padrao_fecha_antes_de_abrir', error, 
                             f'Error should be "hora_padrao_fecha_antes_de_abrir" on {i}')
            self.assertEqual(False, success, f'Success should be False on {i}')


if __name__ == '__main__':
    unittest.main()
