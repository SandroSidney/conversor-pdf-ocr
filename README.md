# Conversor PDF OCR

Converte PDFs digitalizados (imagens escaneadas) em PDFs pesquisáveis e editáveis, aplicando OCR (Optical Character Recognition) com suporte ao idioma português.

> Testado no Windows 11.

---

## O que faz

- Abre um **seletor gráfico de arquivo** para escolher o PDF desejado
- Aplica **OCR** no documento usando Tesseract + Ghostscript
- Salva o arquivo convertido na **mesma pasta do original**, com o sufixo `_Pesquisavel`
- Exibe uma **barra de progresso** durante a conversão
- Ao finalizar, exibe um **relatório** com tamanho original, tamanho gerado, variação percentual e tempo de processamento
- Salva o relatório em `output/relatorios/` no formato JSON e log diário

## Como funciona

```
PDF original (imagem escaneada)
        ↓
  Seletor de arquivo (GUI)
        ↓
  OCR via Tesseract (idioma: português)
  + Correção de inclinação (deskew)
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

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/SandroSidney/projeto_ocr_pdf_editavel.git
cd projeto_ocr_pdf_editavel

# 2. Crie e ative o ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## Como executar

```bash
python Converter_PDF_OCR.py
```

1. Uma janela de seleção de arquivos será aberta — escolha o PDF desejado
2. A barra de progresso aparecerá enquanto o OCR é processado
3. Ao concluir, o relatório será exibido na tela
4. O PDF pesquisável será salvo na mesma pasta do arquivo original com o sufixo `_Pesquisavel`

---

## Estrutura do projeto

```
projeto_ocr_pdf_editavel/
├── Converter_PDF_OCR.py       # Script principal
├── requirements.txt           # Dependências Python
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
  "arquivo_saida": "C:/Documentos/meu_arquivo_Pesquisavel.pdf",
  "tamanho_original_bytes": 1048576,
  "tamanho_saida_bytes": 1457300,
  "variacao_percentual": -39.1,
  "duracao_segundos": 38.5,
  "status": "sucesso"
}
```
