"""
File to Video Encoder - Interface Streamlit Genérica
Detecta automaticamente os plugins disponíveis
"""

import streamlit as st
import hashlib
import base64
from pathlib import Path
import sys
import os
import tempfile
import time
from datetime import datetime

# ============================================
# CONFIGURAÇÃO DO PATH
# ============================================
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

from encoders import discover_encoders, list_available_encoders, identify_video_format, decode_video_auto
from utils.video_utils import extract_frames_for_preview

# ============================================
# Configuração da Página
# ============================================
st.set_page_config(
    page_title="File to Video Encoder",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS Personalizado
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    
    .main-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .video-container {
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    .video-container video {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 15px;
        object-fit: contain;
        background: #000;
    }
    
    .history-item {
        padding: 10px;
        border-left: 3px solid #667eea;
        margin-bottom: 8px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
    }
    
    .history-item.encode {
        border-left-color: #4CAF50;
    }
    
    .history-item.decode {
        border-left-color: #FF9800;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Inicialização do Session State
# ============================================
if 'encoded_video_data' not in st.session_state:
    st.session_state.encoded_video_data = None
if 'video_frames' not in st.session_state:
    st.session_state.video_frames = []
if 'original_filename' not in st.session_state:
    st.session_state.original_filename = None
if 'encoding_method' not in st.session_state:
    st.session_state.encoding_method = None
if 'current_encoder' not in st.session_state:
    st.session_state.current_encoder = None
if 'temp_videos' not in st.session_state:
    st.session_state.temp_videos = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'encode_stats' not in st.session_state:
    st.session_state.encode_stats = {}
if 'decode_stats' not in st.session_state:
    st.session_state.decode_stats = {}

# Descobrir plugins disponíveis
try:
    AVAILABLE_ENCODERS = discover_encoders()
    ENCODER_INFO = list_available_encoders()
    print(f"🔍 Plugins encontrados: {list(AVAILABLE_ENCODERS.keys())}")
except Exception as e:
    st.error(f"Erro ao carregar plugins: {e}")
    AVAILABLE_ENCODERS = {}
    ENCODER_INFO = []

# ============================================
# Funções de Histórico e Métricas
# ============================================
def add_history(action: str, method: str, filename: str, size_before: int, size_after: int, duration: float):
    """Adiciona uma ação ao histórico"""
    history_item = {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'action': action,
        'method': method,
        'filename': filename[:30] + "..." if len(filename) > 30 else filename,
        'size_before': size_before,
        'size_after': size_after,
        'ratio': size_after / size_before if size_before > 0 else 0,
        'duration': duration
    }
    st.session_state.history.insert(0, history_item)
    
    # Mantém apenas os últimos 20 itens
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]

def format_size(size_bytes: int) -> str:
    """Formata tamanho em bytes para formato legível"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def format_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível"""
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"

# ============================================
# Função para player de vídeo
# ============================================
def render_video_player(video_data: bytes, mime_type: str = "video/mp4") -> str:
    """Renderiza um player de vídeo HTML5 funcional"""
    video_base64 = base64.b64encode(video_data).decode('utf-8')
    
    if mime_type == "video/avi" or not mime_type:
        mime_type = "video/mp4"
    
    return f"""
    <div class="video-container">
        <video width="100%" controls autoplay loop muted playsinline>
            <source src="data:{mime_type};base64,{video_base64}" type="{mime_type}">
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
            <source src="data:video/webm;base64,{video_base64}" type="video/webm">
            Seu navegador não suporta o elemento de vídeo.
            <br>
            <a href="data:application/octet-stream;base64,{video_base64}" 
               download="video.avi" 
               style="color: #667eea; text-decoration: none;">
                📥 Clique aqui para baixar o vídeo
            </a>
        </video>
    </div>
    """

def display_video_fallback(video_data: bytes, filename: str = "video.avi"):
    """Fallback: exibe frames e botão de download quando o player não funciona"""
    st.warning("⚠️ Player de vídeo não disponível para este formato.")
    
    frames = extract_frames_for_preview(video_data, max_frames=5)
    if frames:
        st.markdown("### 🎥 Frames do vídeo:")
        cols = st.columns(len(frames))
        for i, (col, frame) in enumerate(zip(cols, frames)):
            with col:
                st.image(frame, caption=f"Frame {i+1}", width="stretch")
    
    st.download_button(
        label="📥 Baixar vídeo para assistir",
        data=video_data,
        file_name=filename,
        mime="video/avi",
        width="stretch"
    )

# ============================================
# Interface Principal
# ============================================

st.markdown('<h1 class="main-header">🎥 FILE TO VIDEO ENCODER</h1>', unsafe_allow_html=True)

# ============================================
# SIDEBAR - Histórico e Informações
# ============================================
with st.sidebar:
    st.header("⚙️ Configurações")
    
    if AVAILABLE_ENCODERS:
        method_options = list(AVAILABLE_ENCODERS.keys())
        method_names = {
            name: f"{AVAILABLE_ENCODERS[name]().icon} {AVAILABLE_ENCODERS[name]().display_name}"
            for name in method_options
        }
        
        encoding_method = st.selectbox(
            "Método de Codificação",
            method_options,
            format_func=lambda x: method_names[x],
            key="encoder_method"
        )
        
        if encoding_method:
            encoder_class = AVAILABLE_ENCODERS[encoding_method]
            encoder = encoder_class()
            with st.expander("ℹ️ Sobre este método"):
                st.markdown(f"**{encoder.display_name}**")
                st.markdown(encoder.description)
                st.markdown(f"**Formato:** {encoder.output_extension.upper()}")
                st.markdown(f"**Assinatura:** `{encoder.signature.decode('ascii')}`")
    else:
        encoding_method = None

    st.divider()
    
    # ============================================
    # PLUGINS CARREGADOS
    # ============================================
    st.markdown("### 📋 Plugins Carregados")
    if AVAILABLE_ENCODERS:
        for name, encoder_class in AVAILABLE_ENCODERS.items():
            encoder = encoder_class()
            st.caption(f"{encoder.icon} {encoder.display_name}")
    else:
        st.warning("Nenhum plugin encontrado")
    
    st.divider()
    
    # ============================================
    # HISTÓRICO DE AÇÕES
    # ============================================
    st.markdown("### 📜 Histórico de Ações")
    
    if st.button("🗑️ Limpar Histórico", width="stretch", key="clear_history"):
        st.session_state.history = []
        st.rerun()
    
    if st.session_state.history:
        for item in st.session_state.history[:10]:
            action_icon = "🎬" if item['action'] == 'encode' else "📥"
            ratio_color = "green" if item['ratio'] < 1.5 else "orange" if item['ratio'] < 3 else "red"
            
            st.markdown(f"""
            <div class="history-item {item['action']}">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>{action_icon} {item['action'].upper()}</strong> - {item['method']}</span>
                    <span style="color: #888;">{item['timestamp']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span>📁 {item['filename']}</span>
                    <span>⏱️ {format_duration(item['duration'])}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                    <span>📦 {format_size(item['size_before'])} → {format_size(item['size_after'])}</span>
                    <span style="color: {ratio_color};">({(item['ratio'] - 1) * 100:+.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Nenhuma ação registrada ainda")

# Tabs principais
tab1, tab2 = st.tabs(["📤 Encoder", "📥 Decoder"])

# ============================================
# TAB 1: ENCODER
# ============================================
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📁 Selecione um arquivo para codificar",
            type=None,
            key="encoder_upload"
        )
    
    with col2:
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            file_size_mb = file_size / (1024 * 1024)
            
            st.markdown("### 📊 Informações do Arquivo")
            st.metric("📦 Tamanho Original", format_size(file_size))
            st.metric("📄 Nome", uploaded_file.name[:25] + "..." if len(uploaded_file.name) > 25 else uploaded_file.name)
            
            # Hash MD5
            md5_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            st.metric("🔐 MD5", md5_hash[:12] + "...")
    
    if uploaded_file and encoding_method and AVAILABLE_ENCODERS:
        if st.button("🎬 Iniciar Codificação", type="primary", width="stretch", key="encode_btn"):
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(progress: float, message: str):
                progress_bar.progress(progress)
                status_text.info(f"⏳ {message}")
            
            try:
                data = uploaded_file.getvalue()
                original_size = len(data)
                
                encoder = AVAILABLE_ENCODERS[encoding_method]()
                st.session_state.current_encoder = encoder
                
                # Marca o tempo de início
                start_time = time.time()
                
                # Codifica
                video_data, frames = encoder.encode(data, uploaded_file.name, update_progress)
                
                # Calcula duração
                duration = time.time() - start_time
                video_size = len(video_data)
                
                # Salva estatísticas
                st.session_state.encode_stats = {
                    'original_size': original_size,
                    'video_size': video_size,
                    'duration': duration,
                    'ratio': video_size / original_size,
                    'method': encoding_method,
                    'encoder_name': encoder.display_name
                }
                
                st.session_state.encoded_video_data = video_data
                st.session_state.video_frames = frames
                st.session_state.original_filename = uploaded_file.name
                st.session_state.encoding_method = encoding_method
                
                # Adiciona ao histórico
                add_history(
                    'encode',
                    encoder.display_name,
                    uploaded_file.name,
                    original_size,
                    video_size,
                    duration
                )
                
                progress_bar.progress(1.0)
                status_text.success(f"✅ Codificação concluída em {format_duration(duration)}!")
                st.balloons()
                
                output_name = Path(uploaded_file.name).stem + f"_{encoding_method}.{encoder.output_extension}"
                
                # ============================================
                # MÉTRICAS DE ENCODING
                # ============================================
                st.markdown("### 📊 Resultado da Codificação")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_size(original_size)}</div>
                        <div class="metric-label">Tamanho Original</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_size(video_size)}</div>
                        <div class="metric-label">Tamanho do Vídeo</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col3:
                    ratio_percent = (video_size / original_size - 1) * 100
                    ratio_color = "green" if ratio_percent < 50 else "orange" if ratio_percent < 200 else "red"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: {ratio_color};">{ratio_percent:+.1f}%</div>
                        <div class="metric-label">Taxa de Expansão</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_duration(duration)}</div>
                        <div class="metric-label">Tempo de Processamento</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Download
                st.download_button(
                    label=f"📥 Baixar Vídeo ({format_size(video_size)})",
                    data=video_data,
                    file_name=output_name,
                    mime=encoder.mime_type,
                    width="stretch",
                    key="download_encoded"
                )
                
                # Preview
                with st.expander("🎬 Preview do Vídeo Gerado", expanded=True):
                    st.markdown("### 🎥 Frames do Vídeo")
                    
                    if frames:
                        frame_index = st.slider("Frame", 0, len(frames)-1, 0, key="preview_slider")
                        st.image(frames[frame_index], width="stretch")
                    
                    st.markdown("### ▶️ Player de Vídeo")
                    
                    try:
                        html_player = render_video_player(video_data, encoder.mime_type)
                        st.html(html_player)
                    except Exception as e:
                        display_video_fallback(video_data, output_name)
                
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# ============================================
# TAB 2: DECODER
# ============================================
with tab2:
    st.markdown("### 📥 Decodificar Vídeo")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # ============================================
        # OPÇÃO 1: Decodificar último vídeo gerado
        # ============================================
        if st.session_state.encoded_video_data and st.session_state.current_encoder:
            st.success(f"✅ Vídeo disponível: {st.session_state.original_filename}")
            st.caption(f"Encoder: {st.session_state.current_encoder.display_name}")
            
            # Mostrar métricas do encode
            if st.session_state.encode_stats:
                stats = st.session_state.encode_stats
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Original", format_size(stats['original_size']))
                with cols[1]:
                    st.metric("Vídeo", format_size(stats['video_size']))
                with cols[2]:
                    st.metric("Tempo", format_duration(stats['duration']))
            
            if st.button("🔄 Decodificar Último Vídeo", type="primary", width="stretch", key="decode_last_btn"):
                with st.spinner("Decodificando..."):
                    encoder = st.session_state.current_encoder
                    video_size = len(st.session_state.encoded_video_data)
                    
                    # Marca tempo
                    start_time = time.time()
                    decoded_data = encoder.decode(st.session_state.encoded_video_data)
                    duration = time.time() - start_time
                    
                    if decoded_data:
                        decoded_size = len(decoded_data)
                        
                        # Salva estatísticas
                        st.session_state.decode_stats = {
                            'video_size': video_size,
                            'decoded_size': decoded_size,
                            'duration': duration,
                            'method': st.session_state.encoding_method
                        }
                        
                        # Adiciona ao histórico
                        add_history(
                            'decode',
                            encoder.display_name,
                            st.session_state.original_filename,
                            video_size,
                            decoded_size,
                            duration
                        )
                        
                        st.success(f"✅ Decodificação concluída em {format_duration(duration)}!")
                        
                        # Métricas de decodificação
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        
                        with metric_col1:
                            st.metric("📦 Vídeo", format_size(video_size))
                        with metric_col2:
                            st.metric("📄 Recuperado", format_size(decoded_size))
                        with metric_col3:
                            st.metric("⏱️ Tempo", format_duration(duration))
                        
                        st.download_button(
                            label=f"📥 Baixar Arquivo ({format_size(decoded_size)})",
                            data=decoded_data,
                            file_name=st.session_state.original_filename,
                            mime="application/octet-stream",
                            width="stretch",
                            key="download_decoded_last"
                        )
                        st.balloons()
                    else:
                        st.error("❌ Falha na decodificação")
        
        st.divider()
        
        # ============================================
        # OPÇÃO 2: Upload de vídeo externo
        # ============================================
        st.markdown("#### 📤 Ou faça upload de um vídeo codificado")
        
        uploaded_video_external = st.file_uploader(
            "Selecione um vídeo codificado",
            type=['avi', 'mp4'],
            key="decoder_upload_external"
        )
        
        if uploaded_video_external:
            video_data = uploaded_video_external.getvalue()
            video_size = len(video_data)
            
            st.info(f"📦 Vídeo carregado: {format_size(video_size)}")
            
            # Preview
            with st.expander("🎬 Preview do Vídeo Enviado", expanded=True):
                frames = extract_frames_for_preview(video_data)
                if frames:
                    frame_idx = st.slider(
                        "Frame", 0, len(frames)-1, 0, 
                        key="upload_preview_slider"
                    )
                    st.image(frames[frame_idx], width="stretch")
                
                try:
                    mime = "video/mp4" if uploaded_video_external.name.endswith('.mp4') else "video/avi"
                    html_player = render_video_player(video_data, mime)
                    st.html(html_player)
                except:
                    st.info("👆 Use o slider acima para navegar pelos frames")
            
            if st.button("🎬 Decodificar Upload", type="primary", width="stretch", key="decode_upload_btn"):
                
                with st.spinner("🔍 Identificando formato do vídeo..."):
                    try:
                        encoder = identify_video_format(video_data)
                        st.success(f"✅ Formato identificado: {encoder.display_name}")
                    except ValueError as e:
                        st.warning(f"⚠️ {e}")
                        st.info("Tentando fallback com todos os decoders...")
                        
                        encoder = None
                        for name, encoder_class in AVAILABLE_ENCODERS.items():
                            try:
                                temp_encoder = encoder_class()
                                if temp_encoder.can_decode(video_data):
                                    encoder = temp_encoder
                                    st.success(f"✅ Identificado via fallback: {encoder.display_name}")
                                    break
                            except:
                                continue
                
                if encoder:
                    with st.spinner(f"Decodificando com {encoder.display_name}..."):
                        # Marca tempo
                        start_time = time.time()
                        decoded_data = encoder.decode(video_data)
                        duration = time.time() - start_time
                        
                        if decoded_data:
                            decoded_size = len(decoded_data)
                            
                            # Adiciona ao histórico
                            add_history(
                                'decode',
                                encoder.display_name,
                                uploaded_video_external.name,
                                video_size,
                                decoded_size,
                                duration
                            )
                            
                            st.success(f"✅ Decodificação concluída em {format_duration(duration)}!")
                            
                            # Métricas
                            metric_col1, metric_col2, metric_col3 = st.columns(3)
                            
                            with metric_col1:
                                st.metric("📦 Vídeo", format_size(video_size))
                            with metric_col2:
                                st.metric("📄 Recuperado", format_size(decoded_size))
                            with metric_col3:
                                st.metric("⏱️ Tempo", format_duration(duration))
                            
                            st.download_button(
                                label=f"📥 Baixar Arquivo Recuperado ({format_size(decoded_size)})",
                                data=decoded_data,
                                file_name="arquivo_restaurado",
                                mime="application/octet-stream",
                                width="stretch",
                                key="download_decoded_external"
                            )
                            
                            # Preview de texto
                            try:
                                text_preview = decoded_data[:500].decode('utf-8')
                                with st.expander("📝 Preview do texto"):
                                    st.text(text_preview)
                            except:
                                pass
                            
                            st.balloons()
                        else:
                            st.error("❌ Falha na decodificação")
                else:
                    st.error("❌ Não foi possível identificar o formato do vídeo")
    
    with col2:
        st.info("""
        ### ℹ️ Identificação Automática
        
        O sistema identifica automaticamente qual encoder foi usado através de uma **assinatura digital** embutida nos primeiros pixels do vídeo.
        
        **Assinaturas suportadas:**
        - `RGB1` → RGB Tabuleiro
        - `YUV1` → YUV Barras
        - `QRC1` → QR Code Sequence
        - `FST1` → RGB FAST
        """)

# ============================================
# Limpeza de arquivos temporários
# ============================================
def cleanup_temp_files():
    if 'temp_videos' in st.session_state:
        for tmp_path in st.session_state.temp_videos:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except:
                pass

import atexit
atexit.register(cleanup_temp_files)

st.divider()
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>🎥 File to Video Encoder v3.0 - Arquitetura de Plugins</p>
    <p style='font-size: 0.8rem;'>{len(AVAILABLE_ENCODERS)} plugins disponíveis | {len(st.session_state.history)} ações no histórico</p>
</div>
""", unsafe_allow_html=True)