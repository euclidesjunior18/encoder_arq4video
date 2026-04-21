# encoder_arq4video
Encoder de arquivos em video

# 🎥 Encoder Arquivos para Vídeo

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-4.0.0-purple.svg)](https://github.com/KamenRider/encoder_arq4video)

Transforme **qualquer arquivo** em um vídeo visual e recupere-o depois! Uma ferramenta inovadora que codifica dados binários em padrões visuais de vídeo.

<p align="center">
  <img src="docs/demo.gif" alt="Demo" width="800"/>
</p>

## ✨ Características

- 🔌 **Arquitetura de Plugins Dinâmica** - Adicione novos encoders sem modificar o código principal
- 🔐 **Sistema de Assinatura Digital** - Identificação automática do formato de codificação
- 📊 **Métricas em Tempo Real** - Tamanho, taxa de compressão e tempo de processamento
- 📜 **Histórico de Ações** - Registro completo de todas as operações
- 🎨 **Múltiplos Métodos** - RGB Tabuleiro, YUV Barras, QR Code, RGB FAST
- 🌐 **Interface Web** - Construída com Streamlit, acessível via navegador
- 📥 **Decodificação Automática** - Recupere o arquivo original com um clique

## 🚀 Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/KamenRider/encoder_arq4video.git
cd encoder_arq4video

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
streamlit run app_streamlit.py