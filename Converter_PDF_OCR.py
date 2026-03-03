# Ler PDF não pesquisavel para pesquisavel.
# Ativar ambiente virtual
# python -m venv .venv
# Alterar para o diretório do ambiente virtual
# .venv\Scripts\activate (Windows)
# Instalar Biblioteca OCRmyPDF para converter PDF digitalizado em PDF pesquisável
# pip install ocrmypdf


import ocrmypdf
import os


def tornar_pdf_pesquisavel(caminho_entrada, caminho_saida):
    # --- CONFIGURAÇÃO PARA WINDOWS ---
    # Adicionando os caminhos do Tesseract e Ghostscript ao PATH apenas durante a execução
    caminho_tesseract = r'C:\Program Files\Tesseract-OCR'
    # Verifique se a sua versão do Ghostscript é a 10.06.0 ou mude o nome da pasta abaixo
    # C:\Program Files\gs\gs10.06.0
    caminho_ghostscript = r'C:\Program Files\gs\gs10.06.0\bin'

    os.environ['PATH'] += os.pathsep + \
        caminho_tesseract + os.pathsep + caminho_ghostscript
    # ---------------------------------

    try:
        # Executa o OCR
        ocrmypdf.ocr(caminho_entrada, caminho_saida,
                     language='por',
                     deskew=True,
                     force_ocr=True,
                     optimize=1,
                     output_type='pdf')

        print(f"Sucesso: {caminho_saida} agora permite busca de palavras.")
    except Exception as e:
        print(f"Erro ao processar {caminho_entrada}: {e}")


# Exemplo de uso:
# Use o prefixo 'r' antes do caminho para evitar erro de barras invertidas no Windows
arquivo_original = r"docs/04-Proposta-EGTecr 28-01-2026 14.15.pdf"
arquivo_final = "Proposta_Pesquisavel.pdf"

tornar_pdf_pesquisavel(arquivo_original, arquivo_final)
