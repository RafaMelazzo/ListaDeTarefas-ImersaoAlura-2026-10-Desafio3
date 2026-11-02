"""
app.py
------
Interface gráfica v2 da aplicação Lista de Tarefas.
Construída com CustomTkinter (tema escuro).

Novidades v2:
  • Checkbox clicável para alternar conclusão diretamente
  • Data/hora de criação exibida em cada tarefa pendente
  • Data/hora de conclusão exibida em cada tarefa concluída
  • Drag-and-drop via alça ⠿ para reordenar tarefas pendentes
  • Seção separada "Concluídas" abaixo das pendentes

Layout:
    ┌──────────────────────────────────────────────┐
    │  📝 Lista de Tarefas           2/5 concluídas│
    ├──────────────────────────────────────────────┤
    │  [___Nova tarefa___________] [＋ Adicionar]  │
    ├──────────────────────────────────────────────┤
    │  📋 Pendentes                                │
    │  ┌─────────────────────────────────────────┐ │
    │  │ ⠿ 🔲  Tarefa A          🕐 02/11 09:10 🗑│ │  ← clique em 🔲 conclui
    │  │ ⠿ 🔲  Tarefa B          🕐 02/11 08:30 🗑│ │  ← alça ⠿ arrasta
    │  └─────────────────────────────────────────┘ │
    │  ─────────────────────────────────────────── │
    │  ✅ Concluídas (1)                           │
    │  ┌─────────────────────────────────────────┐ │
    │  │ ✅  ~~Tarefa C~~  ✔ Conc. 02/11 10:00 🗑│ │  ← clique em ✅ reabre
    │  └─────────────────────────────────────────┘ │
    └──────────────────────────────────────────────┘
"""

from datetime import datetime

import customtkinter as ctk

from task_manager import GerenciadorDeTarefas

# ── Configuração global ────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta de cores ────────────────────────────────────────────────────────────
COR_FUNDO_LINHA_PEND  = "#2b2b2b"
COR_FUNDO_LINHA_DRAG  = "#383838"   # realce visual durante arraste
COR_FUNDO_LINHA_CONCL = "#1e1e1e"
COR_TEXTO             = "#e0e0e0"
COR_TEXTO_CONCLUIDO   = "#6e6e6e"
COR_DATA              = "#888888"
COR_ALCA              = "#555555"
COR_BOTAO_REMOVER     = "#8b2020"
COR_HOVER_REMOVER     = "#c0392b"
COR_SECAO_LABEL       = "#9e9e9e"
COR_SEPARADOR         = "#3a3a3a"

# Placeholder exibido quando a tarefa não possui data registrada (v1 legado)
PLACEHOLDER_DATA = "00/00/0000 00:00"


# ── Utilitário de formatação ───────────────────────────────────────────────────

def _formatar_data(iso_str: str | None) -> str:
    """Converte string ISO ("2026-11-02T09:30") para "02/11/2026 09:30".

    Retorna PLACEHOLDER_DATA para valores nulos ou inválidos (retrocompatibilidade).
    """
    if not iso_str:
        return PLACEHOLDER_DATA
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return PLACEHOLDER_DATA


# ── Janela principal ───────────────────────────────────────────────────────────

class App(ctk.CTk):
    """Janela principal da aplicação Lista de Tarefas."""

    LARGURA = 660
    ALTURA  = 640

    def __init__(self):
        super().__init__()

        self._gerenciador = GerenciadorDeTarefas()

        # ── Estado do drag-and-drop ─────────────────────────────────────
        # ID da tarefa sendo arrastada (None quando não há arraste ativo)
        self._drag_tarefa_id: str | None = None
        # Lista ordenada (tarefa_id, CTkFrame) das linhas visíveis de pendentes
        self._linhas_pendentes: list[tuple[str, ctk.CTkFrame]] = []
        # Referência ao container de pendentes (criado na renderização)
        self._container_pendentes: ctk.CTkFrame | None = None

        self._configurar_janela()
        self._construir_cabecalho()
        self._construir_barra_adicao()
        self._construir_area_lista()
        self._renderizar_lista()

    # ── Configuração da janela ─────────────────────────────────────────────────

    def _configurar_janela(self):
        self.title("📝 Lista de Tarefas")
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.minsize(480, 400)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

    # ── Widgets estáticos (cabeçalho e barra de adição) ───────────────────────

    def _construir_cabecalho(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="📝  Lista de Tarefas",
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._label_contador = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO_CONCLUIDO,
            anchor="e",
        )
        self._label_contador.grid(row=0, column=1, sticky="e", padx=(10, 0))

    def _construir_barra_adicao(self):
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.grid(row=1, column=0, sticky="ew", padx=20, pady=15)
        frame.grid_columnconfigure(0, weight=1)

        self._entrada = ctk.CTkEntry(
            frame,
            placeholder_text="Nova tarefa…",
            height=44,
            font=ctk.CTkFont(size=15),
            border_width=0,
            corner_radius=8,
        )
        self._entrada.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=10)
        self._entrada.bind("<Return>", lambda _: self._adicionar_tarefa())

        ctk.CTkButton(
            frame,
            text="＋ Adicionar",
            width=130,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=self._adicionar_tarefa,
        ).grid(row=0, column=1, padx=(0, 12), pady=10)

    def _construir_area_lista(self):
        """Cria o frame scrollável principal que conterá ambas as seções."""
        self._frame_lista = ctk.CTkScrollableFrame(self, corner_radius=12)
        self._frame_lista.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self._frame_lista.grid_columnconfigure(0, weight=1)

    # ── Renderização completa ──────────────────────────────────────────────────

    def _renderizar_lista(self):
        """Limpa e reconstrói toda a área de lista (pendentes + concluídas)."""
        for widget in self._frame_lista.winfo_children():
            widget.destroy()
        self._linhas_pendentes = []
        self._container_pendentes = None

        todas      = self._gerenciador.listar_tarefas()
        pendentes  = [t for t in todas if not t["concluida"]]
        concluidas = [t for t in todas if t["concluida"]]

        row = 0

        # ── Rótulo: Pendentes ────────────────────────────────────────────
        ctk.CTkLabel(
            self._frame_lista,
            text="📋  Pendentes",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COR_SECAO_LABEL,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(10, 2))
        row += 1

        if pendentes:
            # Container dedicado — permite rearranjo de linhas sem recriar tudo
            self._container_pendentes = ctk.CTkFrame(
                self._frame_lista, fg_color="transparent"
            )
            self._container_pendentes.grid(row=row, column=0, sticky="ew")
            self._container_pendentes.grid_columnconfigure(0, weight=1)
            row += 1

            for idx, tarefa in enumerate(pendentes):
                linha = self._criar_linha_pendente(tarefa, idx)
                self._linhas_pendentes.append((tarefa["id"], linha))
        else:
            ctk.CTkLabel(
                self._frame_lista,
                text="Nenhuma tarefa pendente  🎉",
                font=ctk.CTkFont(size=13),
                text_color=COR_TEXTO_CONCLUIDO,
            ).grid(row=row, column=0, pady=(4, 6))
            row += 1

        # ── Linha separadora ─────────────────────────────────────────────
        ctk.CTkFrame(
            self._frame_lista, height=1, fg_color=COR_SEPARADOR
        ).grid(row=row, column=0, sticky="ew", padx=10, pady=10)
        row += 1

        # ── Rótulo: Concluídas ───────────────────────────────────────────
        ctk.CTkLabel(
            self._frame_lista,
            text=f"✅  Concluídas ({len(concluidas)})",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COR_SECAO_LABEL,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(2, 2))
        row += 1

        if concluidas:
            for tarefa in concluidas:
                linha = self._criar_linha_concluida(tarefa)
                linha.grid(row=row, column=0, sticky="ew", pady=3, padx=4)
                row += 1
        else:
            ctk.CTkLabel(
                self._frame_lista,
                text="Nenhuma tarefa concluída ainda.",
                font=ctk.CTkFont(size=13),
                text_color=COR_TEXTO_CONCLUIDO,
            ).grid(row=row, column=0, pady=(4, 8))
            row += 1

        self._atualizar_contador(todas)

    # ── Criação de linhas ──────────────────────────────────────────────────────

    def _criar_linha_pendente(self, tarefa: dict, idx: int) -> ctk.CTkFrame:
        """Cria o frame de uma tarefa pendente com alça de drag e checkbox clicável."""
        frame = ctk.CTkFrame(
            self._container_pendentes,
            corner_radius=10,
            fg_color=COR_FUNDO_LINHA_PEND,
        )
        frame.grid(row=idx, column=0, sticky="ew", pady=3, padx=4)
        # Col 2 (título) expande; cols 0,1,3 fixas
        frame.grid_columnconfigure(2, weight=1)

        tid = tarefa["id"]

        # ── Col 0: alça de drag ──────────────────────────────────────────
        alca = ctk.CTkLabel(
            frame,
            text="⠿",
            font=ctk.CTkFont(size=20),
            text_color=COR_ALCA,
            cursor="fleur",
            width=28,
        )
        alca.grid(row=0, column=0, rowspan=2, padx=(8, 2), pady=12)
        alca.bind("<Button-1>",        lambda e, f=frame, t=tid: self._drag_inicio(e, f, t))
        alca.bind("<B1-Motion>",       lambda e, f=frame, t=tid: self._drag_mover(e, f, t))
        alca.bind("<ButtonRelease-1>", lambda e, t=tid:          self._drag_soltar(e, t))

        # ── Col 1: checkbox clicável ─────────────────────────────────────
        checkbox = ctk.CTkLabel(
            frame,
            text="🔲",
            font=ctk.CTkFont(size=20),
            cursor="hand2",
            width=32,
        )
        checkbox.grid(row=0, column=1, rowspan=2, padx=(2, 8), pady=12)
        checkbox.bind("<Button-1>", lambda e, t=tid: self._alternar_conclusao(t))

        # ── Col 2: título ────────────────────────────────────────────────
        ctk.CTkLabel(
            frame,
            text=tarefa["titulo"],
            font=ctk.CTkFont(size=15),
            text_color=COR_TEXTO,
            anchor="w",
            wraplength=320,
        ).grid(row=0, column=2, sticky="w", padx=(0, 8), pady=(10, 2))

        # ── Col 2: data de criação ───────────────────────────────────────
        criada_em = _formatar_data(tarefa.get("criada_em"))
        ctk.CTkLabel(
            frame,
            text=f"🕐  Criada em {criada_em}",
            font=ctk.CTkFont(size=11),
            text_color=COR_DATA,
            anchor="w",
        ).grid(row=1, column=2, sticky="w", padx=(0, 8), pady=(0, 10))

        # ── Col 3: botão remover ─────────────────────────────────────────
        ctk.CTkButton(
            frame,
            text="🗑",
            width=38,
            height=38,
            font=ctk.CTkFont(size=14),
            fg_color=COR_BOTAO_REMOVER,
            hover_color=COR_HOVER_REMOVER,
            corner_radius=8,
            command=lambda t=tid: self._remover_tarefa(t),
        ).grid(row=0, column=3, rowspan=2, padx=(4, 10), pady=10)

        return frame

    def _criar_linha_concluida(self, tarefa: dict) -> ctk.CTkFrame:
        """Cria o frame de uma tarefa concluída (sem drag, com data de conclusão)."""
        frame = ctk.CTkFrame(
            self._frame_lista,
            corner_radius=10,
            fg_color=COR_FUNDO_LINHA_CONCL,
        )
        frame.grid_columnconfigure(1, weight=1)

        tid = tarefa["id"]

        # ── Col 0: checkbox ✅ clicável (reabre a tarefa) ────────────────
        checkbox = ctk.CTkLabel(
            frame,
            text="✅",
            font=ctk.CTkFont(size=20),
            cursor="hand2",
            width=44,
        )
        checkbox.grid(row=0, column=0, rowspan=2, padx=(12, 6), pady=12)
        checkbox.bind("<Button-1>", lambda e, t=tid: self._alternar_conclusao(t))

        # ── Col 1: título (tachado) ──────────────────────────────────────
        ctk.CTkLabel(
            frame,
            text=tarefa["titulo"],
            font=ctk.CTkFont(size=15, overstrike=True),
            text_color=COR_TEXTO_CONCLUIDO,
            anchor="w",
            wraplength=330,
        ).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(10, 2))

        # ── Col 1: data de conclusão ─────────────────────────────────────
        concluida_em = _formatar_data(tarefa.get("concluida_em"))
        ctk.CTkLabel(
            frame,
            text=f"✔  Concluída em {concluida_em}",
            font=ctk.CTkFont(size=11),
            text_color=COR_DATA,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(0, 10))

        # ── Col 2: botão remover ─────────────────────────────────────────
        ctk.CTkButton(
            frame,
            text="🗑",
            width=38,
            height=38,
            font=ctk.CTkFont(size=14),
            fg_color=COR_BOTAO_REMOVER,
            hover_color=COR_HOVER_REMOVER,
            corner_radius=8,
            command=lambda t=tid: self._remover_tarefa(t),
        ).grid(row=0, column=2, rowspan=2, padx=(4, 10), pady=10)

        return frame

    def _atualizar_contador(self, tarefas: list[dict]):
        total      = len(tarefas)
        concluidas = sum(1 for t in tarefas if t["concluida"])
        texto = f"{concluidas}/{total} concluídas" if total else ""
        self._label_contador.configure(text=texto)

    # ── Drag-and-drop ──────────────────────────────────────────────────────────

    def _drag_inicio(self, event, frame: ctk.CTkFrame, tarefa_id: str):
        """Registra início do arraste e realça a linha visualmente."""
        self._drag_tarefa_id = tarefa_id
        frame.configure(fg_color=COR_FUNDO_LINHA_DRAG)

    def _drag_mover(self, event, frame: ctk.CTkFrame, tarefa_id: str):
        """Troca a posição da linha arrastada com seu vizinho quando cruza o ponto médio."""
        if self._drag_tarefa_id != tarefa_id:
            return

        # Y absoluto do mouse na tela
        mouse_y_abs = event.widget.winfo_rooty() + event.y

        # Índice atual da linha sendo arrastada
        idx = next(
            (i for i, (tid, _) in enumerate(self._linhas_pendentes) if tid == tarefa_id),
            None,
        )
        if idx is None:
            return

        # ── Troca com o item acima ───────────────────────────────────────
        if idx > 0:
            _, frame_acima = self._linhas_pendentes[idx - 1]
            centro_acima = frame_acima.winfo_rooty() + frame_acima.winfo_height() / 2
            if mouse_y_abs < centro_acima:
                (self._linhas_pendentes[idx],
                 self._linhas_pendentes[idx - 1]) = (
                    self._linhas_pendentes[idx - 1],
                    self._linhas_pendentes[idx],
                )
                self._reempacotar_pendentes()
                return

        # ── Troca com o item abaixo ──────────────────────────────────────
        if idx < len(self._linhas_pendentes) - 1:
            _, frame_abaixo = self._linhas_pendentes[idx + 1]
            centro_abaixo = frame_abaixo.winfo_rooty() + frame_abaixo.winfo_height() / 2
            if mouse_y_abs > centro_abaixo:
                (self._linhas_pendentes[idx],
                 self._linhas_pendentes[idx + 1]) = (
                    self._linhas_pendentes[idx + 1],
                    self._linhas_pendentes[idx],
                )
                self._reempacotar_pendentes()

    def _drag_soltar(self, event, tarefa_id: str):
        """Finaliza o arraste: restaura cor, persiste a nova ordem e re-renderiza."""
        if self._drag_tarefa_id != tarefa_id:
            return
        self._drag_tarefa_id = None

        # Restaura cor da linha que foi arrastada
        for tid, f in self._linhas_pendentes:
            if tid == tarefa_id:
                f.configure(fg_color=COR_FUNDO_LINHA_PEND)
                break

        # Persiste a nova ordem e re-renderiza com estado limpo
        ids_em_ordem = [tid for tid, _ in self._linhas_pendentes]
        self._gerenciador.reordenar(ids_em_ordem)
        self._renderizar_lista()

    def _reempacotar_pendentes(self):
        """Atualiza as posições de grid das linhas pendentes conforme a ordem atual."""
        for idx, (_, f) in enumerate(self._linhas_pendentes):
            f.grid(row=idx, column=0, sticky="ew", pady=3, padx=4)

    # ── Ações do usuário ───────────────────────────────────────────────────────

    def _adicionar_tarefa(self):
        titulo = self._entrada.get()
        if not titulo.strip():
            self._entrada.configure(border_color="red", border_width=2)
            self.after(800, lambda: self._entrada.configure(border_width=0))
            return
        self._gerenciador.adicionar_tarefa(titulo)
        self._entrada.delete(0, "end")
        self._renderizar_lista()

    def _alternar_conclusao(self, tarefa_id: str):
        self._gerenciador.alternar_conclusao(tarefa_id)
        self._renderizar_lista()

    def _remover_tarefa(self, tarefa_id: str):
        self._gerenciador.remover_tarefa(tarefa_id)
        self._renderizar_lista()

    # ── Execução ───────────────────────────────────────────────────────────────

    def run(self):
        self.mainloop()
