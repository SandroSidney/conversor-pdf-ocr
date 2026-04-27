"""
Converter_PDF_OCR.py
--------------------
Converte PDFs digitalizados (imagens) em PDFs pesquisáveis usando OCR.

Uso:
    python Converter_PDF_OCR.py

Ao executar, uma janela de seleção de arquivos é aberta. Selecione o PDF
desejado e o arquivo convertido será salvo na mesma pasta com o sufixo
'_Pesquisavel' no nome (ex: relatorio_Pesquisavel.pdf).

Dependências:
    - ocrmypdf  (pip install ocrmypdf)
    - Tesseract OCR instalado em: C:\\Program Files\\Tesseract-OCR
    - Ghostscript instalado em:   C:\\Program Files\\gs\\gs10.07.0\\bin
"""

import ocrmypdf
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog


# Caminhos das ferramentas externas necessárias para o OCR no Windows
CAMINHO_TESSERACT = r'C:\Program Files\Tesseract-OCR'
CAMINHO_GHOSTSCRIPT = r'C:\Program Files\gs\gs10.07.0\bin'


def configurar_path():
    """Adiciona Tesseract e Ghostscript ao PATH da sessão atual."""
    os.environ['PATH'] += os.pathsep + CAMINHO_TESSERACT + os.pathsep + CAMINHO_GHOSTSCRIPT


def gerar_nome_saida(caminho_entrada: str) -> str:
    """Retorna o caminho de saída com sufixo '_Pesquisavel' no mesmo diretório do original."""
    p = Path(caminho_entrada)
    return str(p.parent / f"{p.stem}_Pesquisavel{p.suffix}")


def selecionar_arquivo_via_gui() -> str:
    """Abre uma janela gráfica para o usuário selecionar um arquivo PDF."""
    root = tk.Tk()
    root.withdraw()
    arquivo = filedialog.askopenfilename(
        title="Selecione o PDF para converter",
        filetypes=[("Arquivos PDF", "*.pdf")],
    )
    root.destroy()
    return arquivo


def tornar_pdf_pesquisavel(caminho_entrada: str, caminho_saida: str):
    """
    Executa o OCR no PDF de entrada e grava o resultado em caminho_saida.

    Parâmetros:
        caminho_entrada: caminho do PDF original (digitalizado).
        caminho_saida:   caminho onde o PDF pesquisável será salvo.
    """
    configurar_path()
    try:
        ocrmypdf.ocr(
            caminho_entrada,
            caminho_saida,
            deskew=True,      # corrige inclinação de páginas escaneadas
            force_ocr=True,   # força OCR mesmo que o PDF já tenha texto
            optimize=1,       # compressão leve para reduzir o tamanho do arquivo
            output_type='pdf',
        )
        print(f"Sucesso: '{caminho_saida}' agora permite busca de palavras.")
    except Exception as e:
        print(f"Erro ao processar '{caminho_entrada}': {e}")
        sys.exit(1)


def main():
    arquivo_original = selecionar_arquivo_via_gui()

    if not arquivo_original:
        print("Nenhum arquivo selecionado. Encerrando.")
        sys.exit(0)

    arquivo_final = gerar_nome_saida(arquivo_original)
    print(f"Convertendo: '{arquivo_original}' -> '{arquivo_final}'")
    tornar_pdf_pesquisavel(arquivo_original, arquivo_final)


if __name__ == "__main__":
    main()
