# 🎥 CS2 Highlight Generator 🚀

Este projeto é um gerador de melhores momentos (highlights) para partidas de Counter-Strike 2, desenvolvido para a disciplina de Sistemas Multimídia. Ele permite que usuários enviem um vídeo de uma partida e recebam um vídeo com os momentos de eliminação de um jogador específico, entregue via **streaming DASH (Dynamic Adaptive Streaming over HTTP)**.

---

## 💻 Tecnologias Utilizadas

### Backend (Python)

* **Flask**: Micro-framework web para a criação do servidor.

* **OpenCV (`cv2`)**: Biblioteca para processamento de imagens e vídeo.

* **PyTesseract**: Wrapper Python para a ferramenta Tesseract OCR.

* **FFmpeg**: Ferramenta de linha de comando essencial para manipulação, corte, concatenação e conversão de vídeo para formatos de streaming (HLS/DASH).

* **`threading`**: Para processar vídeos em segundo plano, sem travar a interface.

### Frontend (Web)

* **HTML5**: Estrutura da página web.

* **CSS3**: Estilização e design responsivo (com imagem de fundo e efeitos modernos).

* **JavaScript**: Lógica de interação, upload assíncrono e comunicação com o backend.

* **`dash.js`**: Biblioteca JavaScript robusta para reprodução de conteúdo via streaming DASH em navegadores compatíveis.

---

## 🚀 Pré-requisitos

Para rodar este projeto, você precisará ter o seguinte instalado em sua máquina:

1.  **Python 3.x**:
    * Baixe e instale a versão mais recente em [python.org](https://www.python.org/downloads/).
    * Certifique-se de adicionar o Python ao seu PATH durante a instalação.

2.  **pip (Gerenciador de Pacotes Python)**:
    * Geralmente vem junto com o Python. Verifique com `pip --version`.

3.  **FFmpeg**:
    * **Windows**: Baixe uma `full build` em [gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z). Descompacte e **adicione o caminho da pasta `bin` (ex: `C:\ffmpeg\bin`) ao PATH do sistema**.
    * **macOS**: `brew install ffmpeg`
    * **Linux**: `sudo apt update && sudo apt install ffmpeg`

4.  **Tesseract OCR**:
    * **Windows**: Baixe o instalador em [github.com/tesseract-ocr/tessdoc/blob/main/Home.md](https://github.com/tesseract-ocr/tessdoc/blob/main/Home.md). **Marque a opção para adicionar ao PATH durante a instalação**. Se não houver a opção, adicione manualmente o caminho da instalação (ex: `C:\Program Files\Tesseract-OCR`) ao PATH do sistema.
    * **macOS**: `brew install tesseract`
    * **Linux**: `sudo apt update && sudo apt install tesseract-ocr`

---

## 🛠️ Como Rodar o Projeto

Siga estas etapas para configurar e executar o projeto:

1.  **Clone o Repositório (ou crie a estrutura de pastas)**:
    ```bash
    # Se você está usando Git
    git clone <URL_DO_SEU_REPOSITORIO>
    cd projeto_highlights
    ```
    Ou crie manualmente as pastas `uploads/`, `dash_output/`, `static/` e `templates/`.

2.  **Configure o Tesseract OCR no seu Código (Windows)**:
    Abra o arquivo `highlight_generator.py` e **certifique-se de que o caminho para o executável `tesseract.exe` está correto** na linha:
    ```python
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```
    Ajuste `C:\Program Files\Tesseract-OCR\tesseract.exe` para o caminho exato onde o Tesseract está instalado no seu computador.

3.  **Instale as Dependências Python**:
    No diretório raiz do projeto (`projeto_highlights/`), execute:
    ```bash
    pip install Flask opencv-python pytesseract
    ```

4.  **Execute o Servidor Flask**:
    No diretório raiz do projeto, execute:
    ```bash
    python app.py
    ```
    O servidor estará rodando em `http://127.0.0.1:5000`.
