
No Windows para utilizar o conversor é preciso instalar as seguintes ferramentas : 

### Dependências Externas ( Obrigatórias )

 - Tesseract OCR
	Download: https://github.com/UB-Mannheim/tesseract/wiki
	 - Instale e marque "Add Tesseract to the PATH"
	 - Caminho padrão: C:\Program Files\Tesseract-OCR

 - Ghostscript
	Download: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases
	 - Instale e adicione ao PATH (ou use o caminho padrão no código)
	 - Caminho padrão: C:\Program Files\gs\gs10.06.0\bin

O script já adiciona esses caminhos ao PATH do processo Python automaticamente.

### Dependências Externas ( Opcionais )

 - pngquant (melhora a compressão de imagens coloridas/em escala de cinza)
	Instale via `choco install pngquant` ou https://pngquant.org/
	Sem ele o OCR funciona normalmente, apenas com arquivos um pouco maiores.
