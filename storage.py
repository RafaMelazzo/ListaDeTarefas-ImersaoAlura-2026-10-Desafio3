"""
storage.py
----------
Responsável por carregar e salvar as tarefas em um arquivo JSON local.
"""

import json
import os

# Arquivo de persistência no mesmo diretório do projeto
ARQUIVO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarefas.json")


def carregar() -> list[dict]:
    """Carrega a lista de tarefas do arquivo JSON.
    Retorna uma lista vazia se o arquivo não existir ou estiver corrompido.
    """
    if not os.path.exists(ARQUIVO_JSON):
        return []
    try:
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def salvar(tarefas: list[dict]) -> None:
    """Salva a lista de tarefas no arquivo JSON."""
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(tarefas, f, ensure_ascii=False, indent=2)
