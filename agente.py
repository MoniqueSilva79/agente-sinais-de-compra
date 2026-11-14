"""Agente de sinais de compra para TI.

Lê um CSV de sinais coletados de fontes públicas, aplica o ICP, pontua (A/B/C)
e gera rascunhos de mensagem para revisão humana.

Uso:
    python agente.py sinais_exemplo.csv --icp icp.json
    python agente.py sinais_exemplo.csv --icp icp.json --gemini   # refina o texto com Gemini
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from mensagem import rascunho_modelo, refinar_com_gemini
from pontuacao import ICP, Conta, pontuar

CAMPOS_SAIDA = ["empresa", "nota", "pontos", "motivos", "fonte", "mensagem", "status"]


def carregar_icp(caminho: Path) -> ICP:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return ICP(set(dados["setores"]), set(dados["regioes"]), int(dados.get("funcionarios_min", 500)))


def carregar_contas(caminho: Path) -> list[Conta]:
    with caminho.open(encoding="utf-8") as f:
        return [
            Conta(
                empresa=l["empresa"], setor=l["setor"], regiao=l["regiao"],
                funcionarios=int(l["funcionarios"]), tipo_sinal=l["tipo_sinal"] or None,
                descricao_sinal=l["descricao_sinal"], fonte=l["fonte"],
                data_sinal=date.fromisoformat(l["data_sinal"]) if l["data_sinal"] else None,
            )
            for l in csv.DictReader(f)
        ]


def processar(contas: list[Conta], icp: ICP, usar_gemini: bool = False, hoje: date | None = None) -> list[dict]:
    saida = []
    for c in contas:
        nota, pontos, motivos = pontuar(c, icp, hoje)
        msg = ""
        if nota in ("A", "B"):
            msg = rascunho_modelo(c)
            if usar_gemini:
                msg = refinar_com_gemini(msg)
        saida.append({
            "empresa": c.empresa, "nota": nota, "pontos": pontos, "motivos": "; ".join(motivos),
            "fonte": c.fonte, "mensagem": msg,
            "status": "PENDENTE_REVISAO" if msg else "DESCARTADA",
        })
    ordem = {"A": 0, "B": 1, "C": 2}
    return sorted(saida, key=lambda s: (ordem[s["nota"]], -s["pontos"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--icp", type=Path, default=Path("icp.json"))
    ap.add_argument("--gemini", action="store_true")
    ap.add_argument("--hoje", type=date.fromisoformat, help="data de referência (AAAA-MM-DD)")
    ap.add_argument("-o", "--saida", type=Path, default=Path("fila_de_abordagem.csv"))
    args = ap.parse_args()

    resultado = processar(carregar_contas(args.entrada), carregar_icp(args.icp), args.gemini, args.hoje)
    with args.saida.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_SAIDA)
        w.writeheader()
        w.writerows(resultado)
    for r in resultado:
        print(f"[{r['nota']}] {r['empresa']:<20} {r['status']:<17} {r['motivos']}")
    print(f"\nFila salva em {args.saida}. Revise cada mensagem antes de enviar.")


if __name__ == "__main__":
    main()
