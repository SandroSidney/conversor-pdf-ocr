# =============================================================================
# PDF OCR - Converter PDF não pesquisável em pesquisável
# Autor: Melhorado com seletor de arquivo, progresso e tratamento de erros
# Dependências: ocrmypdf, tkinter (nativo Python)
# =============================================================================

import ocrmypdf
import os
import sys
import time
import threading
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Configuração de ambiente (Tesseract + Ghostscript no Windows) ─────────────
def configurar_ambiente_windows():
    """Adiciona Tesseract e Ghostscript ao PATH se estiver no Windows."""
    if sys.platform != "win32":
        return

    # Detecta automaticamente a versão mais recente do Ghostscript instalada
    gs_base = Path(r"C:\Program Files\gs")
    caminho_tesseract = Path(r"C:\Program Files\Tesseract-OCR")
    caminho_ghostscript = None

    if gs_base.exists():
        versoes = sorted(gs_base.iterdir(), reverse=True)
        for v in versoes:
            candidato = v / "bin"
            if candidato.exists():
                caminho_ghostscript = candidato
                break

    extras = []
    if caminho_tesseract.exists():
        extras.append(str(caminho_tesseract))
    else:
        logger.warning("Tesseract não encontrado em: %s", caminho_tesseract)

    if caminho_ghostscript:
        extras.append(str(caminho_ghostscript))
        logger.info("Ghostscript detectado em: %s", caminho_ghostscript)
    else:
        logger.warning("Ghostscript não encontrado em: %s", gs_base)

    if extras:
        os.environ["PATH"] = os.pathsep.join(extras) + os.pathsep + os.environ.get("PATH", "")


# ── Seletor de arquivo ────────────────────────────────────────────────────────
def selecionar_arquivo_pdf() -> str | None:
    """Abre janela nativa para selecionar um arquivo PDF. Retorna o caminho ou None."""
    root = tk.Tk()
    root.withdraw()          # Oculta a janela principal
    root.attributes("-topmost", True)   # Garante que fique na frente

    caminho = filedialog.askopenfilename(
        title="Selecione o PDF não pesquisável",
        filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
    )
    root.destroy()
    return caminho if caminho else None


# ── Gerar nome do arquivo de saída ────────────────────────────────────────────
def gerar_caminho_saida(caminho_entrada: str) -> str:
    """
    Gera automaticamente o caminho de saída na mesma pasta do arquivo original,
    adicionando o sufixo '_pesquisavel' antes da extensão.
    Evita sobrescrever arquivos existentes adicionando timestamp se necessário.
    """
    p = Path(caminho_entrada)
    candidato = p.parent / f"{p.stem}_pesquisavel{p.suffix}"

    if candidato.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidato = p.parent / f"{p.stem}_pesquisavel_{ts}{p.suffix}"

    return str(candidato)


# ── Janela de progresso ───────────────────────────────────────────────────────
class JanelaProgresso:
    """Janela simples com barra de progresso indeterminada durante o OCR."""

    def __init__(self, nome_arquivo: str):
        self.root = tk.Tk()
        self.root.title("Processando OCR...")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # Bloqueia fechar

        # Centraliza na tela
        largura, altura = 420, 130
        sx = (self.root.winfo_screenwidth() - largura) // 2
        sy = (self.root.winfo_screenheight() - altura) // 2
        self.root.geometry(f"{largura}x{altura}+{sx}+{sy}")

        tk.Label(
            self.root,
            text=f"Aplicando OCR em:\n{Path(nome_arquivo).name}",
            wraplength=400,
            justify="center",
        ).pack(pady=(15, 8))

        self.barra = ttk.Progressbar(self.root, mode="indeterminate", length=380)
        self.barra.pack(padx=20)
        self.barra.start(12)

        self._encerrado = False

    def atualizar(self):
        if not self._encerrado:
            self.root.update()

    def fechar(self):
        self._encerrado = True
        try:
            self.barra.stop()
            self.root.destroy()
        except Exception:
            pass


# ── Processamento OCR ─────────────────────────────────────────────────────────
def processar_ocr(caminho_entrada: str, caminho_saida: str, idioma: str = "por") -> bool:
    """
    Executa o OCR com ocrmypdf.
    Retorna True em caso de sucesso, False em caso de erro.
    """
    sucesso = False
    erro_msg = None

    def _executar():
        nonlocal sucesso, erro_msg
        try:
            ocrmypdf.ocr(
                caminho_entrada,
                caminho_saida,
                language=idioma,
                deskew=True,
                force_ocr=True,
                optimize=1,
                output_type="pdf",
                progress_bar=False,   # Desativa barra interna (usamos a própria)
            )
            sucesso = True
        except ocrmypdf.exceptions.PriorOcrFoundError:
            # PDF já tem texto — tenta sem force_ocr
            logger.warning("OCR anterior detectado. Tentando com skip_text...")
            try:
                ocrmypdf.ocr(
                    caminho_entrada,
                    caminho_saida,
                    language=idioma,
                    deskew=True,
                    skip_text=True,
                    optimize=1,
                    output_type="pdf",
                    progress_bar=False,
                )
                sucesso = True
            except Exception as e2:
                erro_msg = str(e2)
        except Exception as e:
            erro_msg = str(e)

    # Roda OCR em thread separada para não travar a janela de progresso
    thread = threading.Thread(target=_executar, daemon=True)
    thread.start()

    janela = JanelaProgresso(caminho_entrada)
    inicio = time.time()

    while thread.is_alive():
        janela.atualizar()
        time.sleep(0.05)

    janela.fechar()
    duracao = time.time() - inicio

    if sucesso:
        tamanho_mb = Path(caminho_saida).stat().st_size / 1_048_576
        logger.info("✅ Concluído em %.1fs — Saída: %s (%.2f MB)", duracao, caminho_saida, tamanho_mb)
    else:
        logger.error("❌ Falha após %.1fs — %s", duracao, erro_msg)

    return sucesso, erro_msg, duracao


# ── Interface principal ───────────────────────────────────────────────────────
def main():
    configurar_ambiente_windows()

    # 1. Seleciona o arquivo de entrada
    caminho_entrada = selecionar_arquivo_pdf()
    if not caminho_entrada:
        logger.info("Nenhum arquivo selecionado. Encerrando.")
        return

    if not Path(caminho_entrada).exists():
        messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho_entrada}")
        return

    # 2. Define arquivo de saída automaticamente
    caminho_saida = gerar_caminho_saida(caminho_entrada)
    logger.info("Entrada : %s", caminho_entrada)
    logger.info("Saída   : %s", caminho_saida)

    # 3. Confirmação antes de processar
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    confirmar = messagebox.askyesno(
        "Confirmar processamento",
        f"Arquivo selecionado:\n{Path(caminho_entrada).name}\n\n"
        f"O PDF pesquisável será salvo em:\n{caminho_saida}\n\n"
        "Deseja continuar?",
    )
    root.destroy()

    if not confirmar:
        logger.info("Processamento cancelado pelo usuário.")
        return

    # 4. Executa OCR
    sucesso, erro_msg, duracao = processar_ocr(caminho_entrada, caminho_saida)

    # 5. Feedback final
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if sucesso:
        tamanho_mb = Path(caminho_saida).stat().st_size / 1_048_576
        messagebox.showinfo(
            "✅ Concluído",
            f"PDF pesquisável gerado com sucesso!\n\n"
            f"⏱ Tempo: {duracao:.1f}s\n"
            f"📄 Arquivo: {Path(caminho_saida).name}\n"
            f"📦 Tamanho: {tamanho_mb:.2f} MB\n\n"
            f"Localização:\n{caminho_saida}",
        )
    else:
        messagebox.showerror(
            "❌ Erro no processamento",
            f"Não foi possível processar o arquivo.\n\n"
            f"Detalhe do erro:\n{erro_msg}\n\n"
            "Verifique se Tesseract e Ghostscript estão instalados corretamente.",
        )
    root.destroy()


if __name__ == "__main__":
    main()
