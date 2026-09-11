# Conversor PDF OCR

Converte PDFs digitalizados (imagens escaneadas) em PDFs pesquisáveis e editáveis, aplicando OCR (Optical Character Recognition) com suporte ao idioma português.

> Testado no Windows 11.

---

## O que faz

- Abre um **seletor gráfico de arquivo** para escolher o PDF desejado
- Aplica **OCR** no documento usando Tesseract + Ghostscript, pulando automaticamente páginas que já têm texto (não re-processa o que já está pesquisável)
- Salva o arquivo convertido na **mesma pasta do original**, com o sufixo `_ocr`
- Exibe uma **barra de progresso** durante a conversão
- Ao finalizar, exibe um **relatório** com tamanho original, tamanho gerado, variação percentual e tempo de processamento
- Salva o relatório em `output/relatorios/` no formato JSON e log diário

## Como funciona

```
PDF original (imagem escaneada, texto, ou uma mistura dos dois)
        ↓
  Seletor de arquivo (GUI)
        ↓
  OCR via Tesseract (idioma: português)
  + Correção de inclinação (deskew)
  + Páginas que já têm texto são preservadas sem novo OCR (skip_text)
        ↓
PDF pesquisável salvo na mesma pasta
        ↓
  Relatório de conversão exibido na tela
  + JSON salvo em output/relatorios/
```

---

## Pré-requisitos

### 1. Tesseract OCR
Baixe e instale: https://github.com/UB-Mannheim/tesseract/wiki

Durante a instalação, marque a opção **"Portuguese"** para instalar o pacote de idioma.

Caminho padrão esperado:
```
C:\Program Files\Tesseract-OCR
```

### 2. Ghostscript
Baixe e instale: https://www.ghostscript.com/releases/gsdnld.html

Caminho padrão esperado:
```
C:\Program Files\gs\gs<versão>\bin
```
> A versão é detectada automaticamente pelo script.

### 3. pngquant (opcional, recomendado)
Melhora a compressão das imagens coloridas/em escala de cinza durante a otimização do PDF (`optimize=2`). Sem ele, o ocrmypdf ainda funciona normalmente, apenas com arquivos um pouco maiores.

```bash
choco install pngquant
```

Ou baixe manualmente em https://pngquant.org/ e adicione ao PATH.

> **jbig2enc** também melhoraria a compressão de imagens em preto-e-branco (1 bit), mas não há pacote oficial para Windows via choco/winget — apenas builds de terceiros não verificados. Por segurança, não incluímos essa dependência automaticamente. Quem quiser o ganho extra pode compilar a partir de https://github.com/agl/jbig2enc e garantir que `jbig2` fique no PATH; o ocrmypdf detecta a ferramenta automaticamente quando disponível.

---

## Como executar (executável)

A forma mais simples de usar o conversor é pelo executável — não exige Python instalado.

1. Baixe/gere `dist/ConversorPDFOCR.exe` (veja [Gerando o executável](#gerando-o-executável))
2. Dê duplo clique no `.exe`
3. Na janela, clique em **Selecionar PDF...** e escolha o arquivo desejado
4. Clique em **Converter** e aguarde a barra de progresso
5. O relatório da conversão aparece na própria janela; o PDF pesquisável é salvo na mesma pasta do arquivo original, com o sufixo `_ocr`

> O executável ainda depende do **Tesseract OCR** e do **Ghostscript** instalados no Windows (ver [Pré-requisitos](#pré-requisitos)) — essas ferramentas não são embutidas no `.exe`.

---

## Instalação (a partir do código-fonte)

```bash
# 1. Clone o repositório
git clone https://github.com/SandroSidney/conversor-pdf-ocr.git
cd conversor-pdf-ocr

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## Como executar (código-fonte)

```bash
python Converter_PDF_OCR.py
```

1. A janela do conversor é aberta — clique em **Selecionar PDF...** para escolher o arquivo
2. Clique em **Converter**; a barra de progresso é exibida enquanto o OCR é processado
3. Ao concluir, o relatório aparece na própria janela
4. O PDF pesquisável será salvo na mesma pasta do arquivo original com o sufixo `_ocr`

---

## Gerando o executável

```bash
# 1. Instale a dependência de build (além das dependências de requirements.txt)
pip install -r requirements-build.txt

# 2. Gere o executável a partir do spec já configurado
python -m PyInstaller ConversorPDFOCR.spec
```

O arquivo `dist/ConversorPDFOCR.exe` é gerado como um único executável (`--onefile --windowed`), pronto para distribuir. As pastas `build/` e `dist/` são geradas localmente e não são versionadas.

> Use `python -m PyInstaller` em vez do comando `pyinstaller` direto — em alguns ambientes o executável `pyinstaller.exe` do venv falha silenciosamente (sai com código 1 e nenhuma saída, mesmo com `--version`), enquanto `python -m PyInstaller` funciona normalmente.

---

## Estrutura do projeto

```
conversor-pdf-ocr/
├── Converter_PDF_OCR.py       # Script principal (interface gráfica)
├── ConversorPDFOCR.spec       # Configuração do PyInstaller
├── requirements.txt           # Dependências Python (runtime)
├── requirements-build.txt     # Dependência para gerar o executável
├── dist/                      # Executável gerado (não versionado)
├── output/
│   └── relatorios/            # Relatórios JSON e logs de conversão
└── docs/                      # PDFs de exemplo (não versionados)
```

---

## Exemplo de relatório

```json
{
  "timestamp": "2026-04-29 15:54:31",
  "arquivo_original": "C:/Documentos/meu_arquivo.pdf",
  "arquivo_saida": "C:/Documentos/meu_arquivo_ocr.pdf",
  "tamanho_original_bytes": 1048576,
  "tamanho_saida_bytes": 1457300,
  "variacao_percentual": -39.1,
  "duracao_segundos": 38.5,
  "status": "sucesso"
}
```
