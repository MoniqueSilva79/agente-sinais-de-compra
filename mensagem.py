"""Rascunho de mensagem de abordagem que cita o sinal real.

Toda mensagem sai com status PENDENTE_REVISAO: o agente nunca envia nada.
"""
from __future__ import annotations

import os

from pontuacao import Conta

GANCHOS = {
    "novo_executivo": "Vi a chegada da nova liderança de tecnologia na {empresa}. Nos primeiros meses costuma haver revisão de prioridades de cloud e dados.",
    "vagas_tecnologia": "Vi que a {empresa} abriu vagas na área de tecnologia ({descricao}). Em geral isso vem antes de uma modernização de plataforma.",
    "edital_publico": "Vi o edital publicado pela {empresa} ({descricao}).",
    "expansao": "Vi a notícia sobre {descricao} da {empresa}. Expansões assim costumam pressionar infraestrutura e integração de dados.",
    "fim_contrato": "Vi que a {empresa} comentou publicamente sobre {descricao}.",
    "incidente_publico": "Acompanhei o que a {empresa} divulgou sobre {descricao}.",
}

FECHO = "Faz sentido trocarmos 20 minutos sobre como outras empresas do setor estão tratando isso?"

PROMPT = """Reescreva a mensagem abaixo para LinkedIn em português do Brasil, tom profissional e direto,
máximo de 450 caracteres. Mantenha o fato citado exatamente como está. Não invente dados,
resultados ou nomes de clientes. Não use emojis.

Mensagem:
{mensagem}
"""


def rascunho_modelo(conta: Conta) -> str:
    gancho = GANCHOS.get(conta.tipo_sinal or "", "Acompanho o momento da {empresa}.")
    return f"Olá, [nome]. {gancho.format(empresa=conta.empresa, descricao=conta.descricao_sinal)} {FECHO}"


def refinar_com_gemini(texto: str, modelo: str | None = None) -> str:
    from google import genai

    cliente = genai.Client()
    resp = cliente.models.generate_content(
        model=modelo or os.environ.get("MODELO_GEMINI", "gemini-2.5-flash"),
        contents=PROMPT.format(mensagem=texto),
        config={"temperature": 0.3},
    )
    return (resp.text or texto).strip()
