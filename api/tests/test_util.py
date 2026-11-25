import re

import pytest

from app.util import dentro_cobertura, generar_folio, ofuscar, parsear_bbox


def test_folio_tiene_formato_y_es_deterministico_con_bytes_dados():
    folio = generar_folio(2026, b"\x00\x01\x02\x03\x04")
    assert re.fullmatch(r"VIG-2026-[A-Z2-7]{8}", folio)
    assert folio == generar_folio(2026, b"\x00\x01\x02\x03\x04")


def test_folios_aleatorios_son_distintos():
    assert len({generar_folio() for _ in range(50)}) == 50


def test_ofuscar_reduce_precision():
    assert ofuscar(22.1512345, 3) == 22.151
    assert ofuscar(-100.97654, 2) == -100.98


def test_cobertura_slp():
    assert dentro_cobertura(22.15, -100.98)
    assert not dentro_cobertura(19.43, -99.13)  # Ciudad de México


def test_bbox_valido():
    assert parsear_bbox("-101.0,22.1,-100.9,22.2") == (-101.0, 22.1, -100.9, 22.2)


@pytest.mark.parametrize("texto", ["1,2,3", "a,b,c,d", "-100,22,-101,23", "-101,23,-100,22"])
def test_bbox_invalido(texto):
    with pytest.raises(ValueError):
        parsear_bbox(texto)
