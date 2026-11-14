"""Pontuação de contas por sinais de compra e aderência ao ICP.

Nota final:
    A  -> sinal forte e recente + dentro do ICP: priorizar abordagem
    B  -> sinal moderado ou menos recente + dentro do ICP
    C  -> fora do ICP ou sem sinal relevante: descartar por enquanto
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PESO_SINAL = {
    "novo_executivo": 40,     # novo CIO/CTO/CISO
    "vagas_tecnologia": 30,   # vagas de cloud, dados, segurança
    "edital_publico": 35,     # licitação ou RFP pública
    "expansao": 25,           # nova unidade, fusão, aquisição
    "fim_contrato": 35,       # contrato de data center/fornecedor vencendo (informado publicamente)
    "incidente_publico": 20,  # indisponibilidade ou incidente divulgado
}


@dataclass
class ICP:
    setores: set[str]
    regioes: set[str]
    funcionarios_min: int = 500


@dataclass
class Conta:
    empresa: str
    setor: str
    regiao: str
    funcionarios: int
    tipo_sinal: str | None
    descricao_sinal: str = ""
    data_sinal: date | None = None
    fonte: str = ""
    motivos: list[str] = field(default_factory=list)


def aderencia_icp(conta: Conta, icp: ICP) -> tuple[bool, list[str]]:
    falhas = []
    if conta.setor.lower() not in {s.lower() for s in icp.setores}:
        falhas.append(f"setor fora do ICP ({conta.setor})")
    if conta.regiao.lower() not in {r.lower() for r in icp.regioes}:
        falhas.append(f"região fora do ICP ({conta.regiao})")
    if conta.funcionarios < icp.funcionarios_min:
        falhas.append(f"porte abaixo do ICP ({conta.funcionarios} funcionários)")
    return (not falhas, falhas)


def fator_recencia(data_sinal: date | None, hoje: date) -> float:
    if data_sinal is None:
        return 0.0
    dias = (hoje - data_sinal).days
    if dias < 0:
        return 0.0
    if dias <= 30:
        return 1.0
    if dias <= 90:
        return 0.6
    return 0.2


def pontuar(conta: Conta, icp: ICP, hoje: date | None = None) -> tuple[str, int, list[str]]:
    hoje = hoje or date.today()
    dentro, falhas = aderencia_icp(conta, icp)
    if not dentro:
        return "C", 0, falhas
    if not conta.tipo_sinal or conta.tipo_sinal not in PESO_SINAL:
        return "C", 0, ["nenhum sinal relevante"]
    if not conta.fonte:
        return "C", 0, ["sinal sem fonte pública verificável"]
    pontos = round(PESO_SINAL[conta.tipo_sinal] * fator_recencia(conta.data_sinal, hoje))
    motivos = [f"{conta.tipo_sinal}: {conta.descricao_sinal}", f"recência: {pontos} pts"]
    if pontos >= 30:
        return "A", pontos, motivos
    if pontos >= 15:
        return "B", pontos, motivos
    return "C", pontos, motivos + ["sinal antigo ou fraco"]
