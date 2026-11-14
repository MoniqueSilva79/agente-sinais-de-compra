import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from agente import carregar_contas, carregar_icp, processar  # noqa: E402
from pontuacao import ICP, Conta, fator_recencia, pontuar  # noqa: E402

AQUI = Path(__file__).parent
HOJE = date(2026, 11, 14)
ICP_T = ICP({"Varejo"}, {"Sudeste"}, 500)


def _conta(**kw):
    base = dict(empresa="X", setor="Varejo", regiao="Sudeste", funcionarios=1000,
                tipo_sinal="novo_executivo", descricao_sinal="novo CIO",
                data_sinal=date(2026, 11, 1), fonte="https://exemplo.com")
    base.update(kw)
    return Conta(**base)


def test_sinal_forte_recente_e_A():
    assert pontuar(_conta(), ICP_T, HOJE)[0] == "A"


def test_fora_do_icp_e_C():
    nota, _, motivos = pontuar(_conta(setor="Mineração"), ICP_T, HOJE)
    assert nota == "C" and "setor" in motivos[0]


def test_sem_fonte_e_descartado():
    assert pontuar(_conta(fonte=""), ICP_T, HOJE)[0] == "C"


def test_recencia():
    assert fator_recencia(date(2026, 11, 1), HOJE) == 1.0
    assert fator_recencia(date(2026, 9, 1), HOJE) == 0.6
    assert fator_recencia(date(2025, 1, 1), HOJE) == 0.2
    assert fator_recencia(None, HOJE) == 0.0


def test_pipeline_exemplo():
    res = processar(carregar_contas(AQUI / "sinais_exemplo.csv"), carregar_icp(AQUI / "icp.json"), hoje=HOJE)
    notas = {r["empresa"]: r["nota"] for r in res}
    assert notas == {"Alfa Seguros": "A", "Beta Varejo": "A", "Gama Logística": "B",
                     "Delta Saúde": "B", "Ômega Têxtil": "C"}
    assert res[0]["nota"] == "A"
    for r in res:
        if r["mensagem"]:
            assert r["status"] == "PENDENTE_REVISAO"
            assert "[nome]" in r["mensagem"]
        else:
            assert r["status"] == "DESCARTADA"
