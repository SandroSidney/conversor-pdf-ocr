"""
Converter_PDF_OCR.py
--------------------
Interface gráfica para converter PDFs digitalizados em PDFs pesquisáveis via OCR (Tesseract + Ghostscript).

Dependências:
    - ocrmypdf  (pip install ocrmypdf)
    - Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
    - Ghostscript:   https://www.ghostscript.com/releases/gsdnld.html
"""

import json
import logging
import os
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ocrmypdf

# ── Pastas de saída ────────────────────────────────────────────────────────────
# Path(__file__) aponta para a pasta temporária de extração quando empacotado
# com PyInstaller (--onefile), por isso usamos sys.executable nesse caso.
PASTA_RAIZ = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
PASTA_OUTPUT = PASTA_RAIZ / "output"
PASTA_RELATORIOS = PASTA_RAIZ / "output" / "relatorios"

PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
PASTA_OUTPUT.mkdir(exist_ok=True)

# ── Logging (console + arquivo diário) ────────────────────────────────────────
LOG_FILE = PASTA_RELATORIOS / \
    f"conversao_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Ambiente ───────────────────────────────────────────────────────────────────
def configurar_ambiente():
    """Detecta e adiciona Tesseract + Ghostscript ao PATH."""
    tesseract = Path(r"C:\Program Files\Tesseract-OCR")
    gs_base = Path(r"C:\Program Files\gs")
    ghostscript = None

    if gs_base.exists():
        for versao in sorted(gs_base.iterdir(), reverse=True):
            candidato = versao / "bin"
            if candidato.exists():
                ghostscript = candidato
                break

    extras = []
    if tesseract.exists():
        extras.append(str(tesseract))
    else:
        logger.warning("Tesseract não encontrado em: %s", tesseract)

    if ghostscript:
        extras.append(str(ghostscript))
        logger.info("Ghostscript detectado: %s", ghostscript)
    else:
        logger.warning("Ghostscript não encontrado em: %s", gs_base)

    if extras:
        os.environ["PATH"] = os.pathsep.join(
            extras) + os.pathsep + os.environ.get("PATH", "")


# ── Caminho de saída ───────────────────────────────────────────────────────────
def gerar_caminho_saida(entrada: Path) -> Path:
    """Gera o caminho de saída na mesma pasta do arquivo original. Adiciona timestamp se já existir."""
    candidato = entrada.parent / f"{entrada.stem}_ocr{entrada.suffix}"
    if candidato.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidato = entrada.parent / f"{entrada.stem}_ocr_{ts}{entrada.suffix}"
    return candidato


# ── Relatório ──────────────────────────────────────────────────────────────────
def _formatar_tamanho(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1_048_576:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / 1_048_576:.2f} MB"


def salvar_relatorio_json(entrada: Path, saida: Path, duracao: float) -> dict:
    """Calcula métricas da conversão e salva relatório JSON. Retorna os dados calculados."""
    tam_entrada = entrada.stat().st_size
    tam_saida = saida.stat().st_size
    variacao = (1 - tam_saida / tam_entrada) * 100 if tam_entrada else 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dados = {
        "timestamp": timestamp,
        "arquivo_original": str(entrada),
        "arquivo_saida": str(saida),
        "tamanho_original_bytes": tam_entrada,
        "tamanho_saida_bytes": tam_saida,
        "variacao_percentual": round(variacao, 2),
        "duracao_segundos": round(duracao, 2),
        "status": "sucesso",
    }

    json_path = PASTA_RELATORIOS / \
        f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_path.write_text(json.dumps(
        dados, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Relatorio JSON salvo: %s", json_path)
    return dados


# ── Interface gráfica ──────────────────────────────────────────────────────────
class ConversorApp(tk.Tk):
    """Janela única: selecionar PDF, converter e acompanhar o relatório."""

    def __init__(self):
        super().__init__()
        self.title("Conversor PDF OCR")
        self.resizable(False, False)

        self.entrada: Path | None = None
        self.saida: Path | None = None
        self._thread_resultado: dict = {}
        self._inicio: float = 0.0

        self._montar_layout()
        self._centralizar()

    # -- layout -------------------------------------------------------------
    def _montar_layout(self):
        pad = {"padx": 16, "pady": 8}

        tk.Label(self, text="Conversor PDF OCR", font=("Segoe UI", 14, "bold")).pack(pady=(16, 0))
        tk.Label(
            self,
            text="Converte PDFs escaneados em PDFs pesquisáveis (idioma: português)",
            font=("Segoe UI", 9), fg="#555555",
        ).pack(pady=(0, 12))

        # Seleção de arquivo
        frame_arquivo = tk.LabelFrame(self, text="Arquivo", font=("Segoe UI", 9, "bold"))
        frame_arquivo.pack(fill="x", **pad)

        self.var_entrada = tk.StringVar(value="Nenhum arquivo selecionado")
        tk.Entry(frame_arquivo, textvariable=self.var_entrada, state="readonly", width=58).grid(
            row=0, column=0, padx=(10, 6), pady=10, sticky="w"
        )
        tk.Button(frame_arquivo, text="Selecionar PDF...", command=self._selecionar_arquivo).grid(
            row=0, column=1, padx=(0, 10), pady=10
        )

        tk.Label(frame_arquivo, text="Será salvo como:", font=("Segoe UI", 8), fg="#555555").grid(
            row=1, column=0, sticky="w", padx=10
        )
        self.var_saida = tk.StringVar(value="—")
        tk.Label(frame_arquivo, textvariable=self.var_saida, font=("Segoe UI", 8), fg="#333333").grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )

        # Ação de conversão
        frame_acao = tk.Frame(self)
        frame_acao.pack(fill="x", **pad)

        self.btn_converter = tk.Button(
            frame_acao, text="Converter", state="disabled", width=16,
            command=self._iniciar_conversao,
        )
        self.btn_converter.pack(side="left")

        self.var_status = tk.StringVar(value="Selecione um PDF para começar.")
        self.lbl_status = tk.Label(frame_acao, textvariable=self.var_status, font=("Segoe UI", 9), fg="#555555")
        self.lbl_status.pack(side="left", padx=12)

        self.barra = ttk.Progressbar(self, mode="indeterminate", length=460)
        self.barra.pack(padx=16, pady=(0, 8))

        # Relatório
        frame_relatorio = tk.LabelFrame(self, text="Relatório da última conversão", font=("Segoe UI", 9, "bold"))
        frame_relatorio.pack(fill="x", **pad)

        self.var_relatorio = tk.StringVar(value="Nenhuma conversão realizada ainda.")
        self.lbl_relatorio = tk.Label(
            frame_relatorio, textvariable=self.var_relatorio, justify="left",
            font=("Segoe UI", 9), fg="#333333", anchor="w",
        )
        self.lbl_relatorio.pack(fill="x", padx=10, pady=10)

    def _centralizar(self):
        self.update_idletasks()
        larg, alt = self.winfo_width(), self.winfo_height()
        sx = (self.winfo_screenwidth() - larg) // 2
        sy = (self.winfo_screenheight() - alt) // 2
        self.geometry(f"+{sx}+{sy}")

    # -- seleção de arquivo ---------------------------------------------------
    def _selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o PDF para converter",
            filetypes=[("Arquivos PDF", "*.pdf")],
        )
        if not caminho:
            return

        self.entrada = Path(caminho)
        self.saida = gerar_caminho_saida(self.entrada)

        self.var_entrada.set(self.entrada.name)
        self.var_saida.set(str(self.saida))
        self.lbl_status.config(fg="#555555")
        self.var_status.set("Pronto para converter.")
        self.btn_converter.config(state="normal")

    # -- conversão --------------------------------------------------------------
    def _iniciar_conversao(self):
        if not self.entrada:
            return

        self.btn_converter.config(state="disabled")
        self.lbl_status.config(fg="#555555")
        self.var_status.set("Aplicando OCR — aguarde...")
        self.barra.start(12)

        self._thread_resultado = {}
        self._inicio = time.time()
        thread = threading.Thread(target=self._executar_ocr, daemon=True)
        thread.start()
        self.after(100, self._verificar_thread, thread)

    def _executar_ocr(self):
        resultado = self._thread_resultado
        try:
            # skip_text preserva páginas que já têm texto (sem re-rasterizar) e
            # aplica OCR apenas nas páginas que ainda são imagem pura.
            ocrmypdf.ocr(
                str(self.entrada), str(self.saida),
                language="por", deskew=True, skip_text=True,
                optimize=2, output_type="pdf", progress_bar=False,
            )
            resultado["sucesso"] = True
        except Exception as e:
            resultado["sucesso"] = False
            resultado["erro"] = str(e)

    def _verificar_thread(self, thread: threading.Thread):
        if thread.is_alive():
            self.after(100, self._verificar_thread, thread)
            return

        self.barra.stop()
        duracao = time.time() - self._inicio

        if self._thread_resultado.get("sucesso"):
            self._exibir_sucesso(duracao)
        else:
            self._exibir_erro(self._thread_resultado.get("erro", "Erro desconhecido"), duracao)

        self.btn_converter.config(state="normal")

    def _exibir_sucesso(self, duracao: float):
        dados = salvar_relatorio_json(self.entrada, self.saida, duracao)
        sinal = "↓ redução" if dados["variacao_percentual"] >= 0 else "↑ aumento"

        texto = (
            f"Arquivo gerado  : {self.saida.name}\n"
            f"Tamanho original: {_formatar_tamanho(dados['tamanho_original_bytes'])}    "
            f"Tamanho gerado: {_formatar_tamanho(dados['tamanho_saida_bytes'])}\n"
            f"Variação: {sinal} de {abs(dados['variacao_percentual']):.1f}%    "
            f"Tempo: {duracao:.1f}s\n"
            f"Data/hora: {dados['timestamp']}"
        )
        self.lbl_relatorio.config(fg="#1a7a1a")
        self.var_relatorio.set(texto)

        self.lbl_status.config(fg="#1a7a1a")
        self.var_status.set("Conversão concluída com sucesso!")
        logger.info("Conversao concluida (%.1fs): %s", duracao, self.saida)

    def _exibir_erro(self, erro: str, duracao: float):
        self.lbl_status.config(fg="#c0392b")
        self.var_status.set("Falha na conversão.")

        self.lbl_relatorio.config(fg="#c0392b")
        self.var_relatorio.set(f"Erro: {erro}")

        logger.error("Falha na conversao (%.1fs): %s", duracao, erro)
        messagebox.showerror(
            "Erro na conversão",
            f"Não foi possível processar o arquivo.\n\nErro: {erro}\n\n"
            "Verifique se Tesseract e Ghostscript estão instalados corretamente.",
        )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    configurar_ambiente()
    app = ConversorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
