"""
task_manager.py
---------------
Lógica de negócio para gerenciamento de tarefas (CRUD) — v2.

Modelo de tarefa:
    {
        "id":           str (UUID),
        "titulo":       str,
        "concluida":    bool,
        "criada_em":    str | None  — ISO datetime: "2026-11-02T09:30"
        "concluida_em": str | None  — ISO datetime: "2026-11-02T10:00"
        "ordem":        int         — posição na fila de pendentes (0-indexed)
    }

Compatibilidade retroativa: tarefas sem os campos novos recebem valores
padrão em tempo de execução (nunca alteramos o JSON de forma destrutiva).
"""

import uuid
from datetime import datetime
from storage import carregar, salvar


def _agora_iso() -> str:
    """Retorna o datetime atual em formato ISO sem segundos."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


class GerenciadorDeTarefas:
    """Gerencia a lista de tarefas em memória com persistência automática."""

    def __init__(self):
        self._tarefas: list[dict] = carregar()

    # ── Consultas ─────────────────────────────────────────────────────────────

    def listar_tarefas(self) -> list[dict]:
        """Retorna pendentes ordenadas por 'ordem', depois concluídas (mais recente primeiro)."""
        pendentes = sorted(
            [t for t in self._tarefas if not t["concluida"]],
            key=lambda t: t.get("ordem", 0),
        )
        concluidas = sorted(
            [t for t in self._tarefas if t["concluida"]],
            key=lambda t: t.get("concluida_em") or "",
            reverse=True,  # mais recente no topo
        )
        return pendentes + concluidas

    # ── Mutações ──────────────────────────────────────────────────────────────

    def adicionar_tarefa(self, titulo: str) -> dict | None:
        """Cria nova tarefa com data/hora de criação e posição no final da fila.

        Retorna a tarefa criada, ou None se o título estiver vazio.
        """
        titulo = titulo.strip()
        if not titulo:
            return None

        pendentes_atuais = [t for t in self._tarefas if not t["concluida"]]
        tarefa = {
            "id":           str(uuid.uuid4()),
            "titulo":       titulo,
            "concluida":    False,
            "criada_em":    _agora_iso(),
            "concluida_em": None,
            "ordem":        len(pendentes_atuais),  # vai para o final
        }
        self._tarefas.append(tarefa)
        self._persistir()
        return tarefa

    def alternar_conclusao(self, tarefa_id: str) -> dict | None:
        """Alterna o estado concluída ↔ pendente, registrando data/hora de conclusão.

        Ao concluir: registra 'concluida_em'.
        Ao reabrir:  limpa 'concluida_em' e insere a tarefa no final das pendentes.
        """
        tarefa = self._buscar_por_id(tarefa_id)
        if not tarefa:
            return None

        tarefa["concluida"] = not tarefa["concluida"]

        if tarefa["concluida"]:
            # Concluindo: registra horário
            tarefa["concluida_em"] = _agora_iso()
        else:
            # Reabrindo: limpa horário e coloca após o último pendente existente.
            # Usamos o maior valor de 'ordem' entre os outros pendentes + 1,
            # garantindo unicidade mesmo se houver empates preexistentes.
            tarefa["concluida_em"] = None
            outros_pendentes = [
                t for t in self._tarefas
                if not t["concluida"] and t["id"] != tarefa["id"]
            ]
            max_ordem = max((t.get("ordem", 0) for t in outros_pendentes), default=-1)
            tarefa["ordem"] = max_ordem + 1

        self._persistir()
        return tarefa

    def reordenar(self, ids_ordenados: list[str]) -> None:
        """Reordena as tarefas pendentes conforme a lista de IDs fornecida.

        As tarefas concluídas permanecem intocadas.
        """
        id_para_tarefa = {t["id"]: t for t in self._tarefas}
        pendentes_reord = [
            id_para_tarefa[tid] for tid in ids_ordenados if tid in id_para_tarefa
        ]
        concluidas = [t for t in self._tarefas if t["concluida"]]

        for i, t in enumerate(pendentes_reord):
            t["ordem"] = i

        self._tarefas = pendentes_reord + concluidas
        self._persistir()

    def remover_tarefa(self, tarefa_id: str) -> bool:
        """Remove a tarefa com o id informado.

        Retorna True se removida, False se não encontrada.
        """
        original = len(self._tarefas)
        self._tarefas = [t for t in self._tarefas if t["id"] != tarefa_id]
        removida = len(self._tarefas) < original
        if removida:
            self._persistir()
        return removida

    # ── Auxiliares ────────────────────────────────────────────────────────────

    def _buscar_por_id(self, tarefa_id: str) -> dict | None:
        return next((t for t in self._tarefas if t["id"] == tarefa_id), None)

    def _persistir(self) -> None:
        salvar(self._tarefas)
