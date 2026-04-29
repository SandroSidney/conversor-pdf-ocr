"""
Converter_PDF_OCR.py
--------------------
Converte PDFs digitalizados em PDFs pesquisáveis via OCR (Tesseract + Ghostscript).

Fluxo:
    1. Seleção do PDF via janela gráfica
    2. Conversão com barra de progresso
    3. Arquivo salvo em output/
    4. Relatório exibido na tela e salvo em output/relatorios/

Dependências:
    - ocrmypdf  (pip install ocrmypdf)
    - Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
    - Ghostscript:   https://www.ghostscript.com/releases/gsdnld.html
"""

import json
import logging
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ocrmypdf

# ── Pastas de saída ────────────────────────────────────────────────────────────
PASTA_RAIZ = Path(__file__).parent
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


# ── Seleção de arquivo ─────────────────────────────────────────────────────────
def selecionar_arquivo() -> Path | None:
    """Abre janela nativa para selecionar um PDF. Retorna o caminho ou None."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    caminho = filedialog.askopenfilename(
        title="Selecione o PDF para converter",
        filetypes=[("Arquivos PDF", "*.pdf")],
    )
    root.destroy()
    return Path(caminho) if caminho else None


# ── Caminho de saída ───────────────────────────────────────────────────────────
def gerar_caminho_saida(entrada: Path) -> Path:
    """Gera o caminho de saída na mesma pasta do arquivo original. Adiciona timestamp se já existir."""
    candidato = entrada.parent / f"{entrada.stem}_Pesquisavel{entrada.suffix}"
    if candidato.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidato = entrada.parent / f"{entrada.stem}_Pesquisavel_{ts}{entrada.suffix}"
    return candidato


# ── Janela de progresso ────────────────────────────────────────────────────────
class JanelaProgresso:
    """Barra de progresso indeterminada exibida durante a conversão OCR."""

    def __init__(self, nome_arquivo: str):
        self.root = tk.Tk()
        self.root.title("Convertendo PDF...")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        larg, alt = 440, 150
        sx = (self.root.winfo_screenwidth() - larg) // 2
        sy = (self.root.winfo_screenheight() - alt) // 2
        self.root.geometry(f"{larg}x{alt}+{sx}+{sy}")

        tk.Label(
            self.root,
            text="Aplicando OCR — aguarde...",
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(18, 4))

        tk.Label(
            self.root,
            text=nome_arquivo,
            wraplength=420,
            justify="center",
            font=("Segoe UI", 9),
            fg="#555555",
        ).pack()

        self.barra = ttk.Progressbar(
            self.root, mode="indeterminate", length=400)
        self.barra.pack(padx=20, pady=12)
        self.barra.start(12)

    def atualizar(self):
        try:
            self.root.update()
        except Exception:
            pass

    def fechar(self):
        try:
            self.barra.stop()
            self.root.destroy()
        except Exception:
            pass


# ── Conversão OCR ──────────────────────────────────────────────────────────────
def executar_ocr(entrada: Path, saida: Path) -> tuple[bool, str | None, float]:
    """
    Executa ocrmypdf em thread separada para não travar a interface.

    Retorna:
        (sucesso, mensagem_de_erro, duração_em_segundos)
    """
    sucesso = False
    erro = None

    def _ocr():
        nonlocal sucesso, erro
        try:
            ocrmypdf.ocr(
                str(entrada),
                str(saida),
                language="por",
                deskew=True,
                force_ocr=True,
                optimize=1,
                output_type="pdf",
                progress_bar=False,
            )
            sucesso = True
        except ocrmypdf.exceptions.PriorOcrFoundError:
            # PDF já possui camada de texto — reprocessa sem force_ocr
            logger.warning("OCR anterior detectado. Reprocessando com skip_text...")
            try:
                ocrmypdf.ocr(
                    str(entrada),
                    str(saida),
                    language="por",
                    deskew=True,
                    skip_text=True,
                    optimize=1,
                    output_type="pdf",
                    progress_bar=False,
                )
                sucesso = True
            except Exception as e2:
                erro = str(e2)
        except Exception as e:
            erro = str(e)

    thread = threading.Thread(target=_ocr, daemon=True)
    thread.start()

    janela = JanelaProgresso(entrada.name)
    inicio = time.time()
    while thread.is_alive():
        janela.atualizar()
        time.sleep(0.05)
    janela.fechar()

    return sucesso, erro, time.time() - inicio


# ── Relatório ──────────────────────────────────────────────────────────────────
def _formatar_tamanho(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1_048_576:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / 1_048_576:.2f} MB"


def gerar_relatorio(entrada: Path, saida: Path, duracao: float):
    """Salva relatório JSON e exibe resumo em messagebox."""
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

    sinal = "↓ redução" if variacao >= 0 else "↑ aumento"
    linha = "─" * 44

    texto = (
        f"PDF pesquisável gerado com sucesso!\n\n"
        f"{linha}\n"
        f"  Arquivo original : {entrada.name}\n"
        f"  Arquivo gerado   : {saida.name}\n"
        f"  Pasta de saída   : output/\n"
        f"{linha}\n"
        f"  Tamanho original : {_formatar_tamanho(tam_entrada)}\n"
        f"  Tamanho gerado   : {_formatar_tamanho(tam_saida)}\n"
        f"  Variação         : {sinal} de {abs(variacao):.1f}%\n"
        f"  Tempo de processo: {duracao:.1f}s\n"
        f"  Data / hora      : {timestamp}\n"
        f"{linha}\n"
        f"  Relatório salvo em: output/relatorios/"
    )

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("Relatório de Conversão", texto)
    root.destroy()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    configurar_ambiente()

    entrada = selecionar_arquivo()
    if not entrada:
        logger.info("Nenhum arquivo selecionado. Encerrando.")
        return

    saida = gerar_caminho_saida(entrada)

    # Confirmação antes de processar
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    confirmar = messagebox.askyesno(
        "Confirmar conversão",
        f"Arquivo selecionado:\n{entrada.name}\n\n"
        f"O PDF pesquisável será salvo em:\n{saida.parent}\n\n"
        "Deseja continuar?",
    )
    root.destroy()

    if not confirmar:
        logger.info("Processamento cancelado pelo usuário.")
        return

    logger.info("Iniciando conversão")
    logger.info("  Entrada : %s", entrada)
    logger.info("  Saida   : %s", saida)

    sucesso, erro, duracao = executar_ocr(entrada, saida)

    if sucesso:
        gerar_relatorio(entrada, saida, duracao)
    else:
        logger.error("Falha na conversao (%.1fs): %s", duracao, erro)
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(
            "Erro na conversão",
            f"Não foi possível processar o arquivo.\n\n"
            f"Erro: {erro}\n\n"
            "Verifique se Tesseract e Ghostscript estão instalados corretamente.",
        )
        root.destroy()


if __name__ == "__main__":
    main()
