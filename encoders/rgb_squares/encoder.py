"""Encoder RGB Quadrados - Padrão Tabuleiro (Grid)"""

import numpy as np
import cv2
import math
import os
import hashlib
import json
import tempfile
import struct
from pathlib import Path
from datetime import datetime
from typing import Callable, Tuple, List, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from encoders.base_encoder import BaseEncoder


class RGBSquaresEncoder(BaseEncoder):
    
    def __init__(self):
        self.video_width = 1280
        self.video_height = 720
        self.grid_cols = 16  # Número de colunas no tabuleiro
        self.grid_rows = 9   # Número de linhas no tabuleiro
        self.cell_size = 60  # Tamanho de cada célula em pixels
        self.fps = 30
        self.bytes_per_cell = 3  # RGB
    
    @property
    def name(self) -> str:
        return "rgb_squares"
    
    @property
    def display_name(self) -> str:
        return "🎨 RGB Tabuleiro"
    
    @property
    def description(self) -> str:
        return "Padrão de tabuleiro colorido. Cada célula armazena 3 bytes (RGB)."
    
    @property
    def icon(self) -> str:
        return "🎨"
    
    @property
    def output_extension(self) -> str:
        return "avi"
    
    @property
    def mime_type(self) -> str:
        return "video/avi"
    
    @property
    def signature(self) -> bytes:
        return b'RGB1'
    
    def _create_checkerboard_frame(self, data_chunk: bytes, frame_num: int, 
                                   total_frames: int, metadata: dict) -> np.ndarray:
        """
        Cria um frame com padrão de tabuleiro (grid)
        Cada célula do grid armazena 3 bytes (R, G, B)
        """
        # Cria frame base preto
        frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
        
        # Calcula offset para centralizar o tabuleiro
        grid_width = self.grid_cols * self.cell_size
        grid_height = self.grid_rows * self.cell_size
        offset_x = (self.video_width - grid_width) // 2
        offset_y = (self.video_height - grid_height) // 2 - 30
        
        # Converte dados para pixels RGB
        pad = (-len(data_chunk)) % self.bytes_per_cell
        if pad:
            data_chunk += b'\x00' * pad
        
        pixels = np.frombuffer(data_chunk, dtype=np.uint8)
        num_pixels = len(pixels) // self.bytes_per_cell
        pixels = pixels.reshape((num_pixels, self.bytes_per_cell))
        
        # Preenche o tabuleiro
        cells_per_frame = self.grid_cols * self.grid_rows
        pixel_idx = 0
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                if pixel_idx < num_pixels:
                    color = pixels[pixel_idx].tolist()
                    color_bgr = [color[2], color[1], color[0]] if len(color) >= 3 else [0, 0, 0]
                    
                    x1 = offset_x + col * self.cell_size
                    y1 = offset_y + row * self.cell_size
                    x2 = x1 + self.cell_size - 2
                    y2 = y1 + self.cell_size - 2
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, -1)
                    
                    border_color = (255, 255, 255) if (row + col) % 2 == 0 else (100, 100, 100)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 1)
                    
                    pixel_idx += 1
                else:
                    # Célula vazia
                    x1 = offset_x + col * self.cell_size
                    y1 = offset_y + row * self.cell_size
                    x2 = x1 + self.cell_size - 2
                    y2 = y1 + self.cell_size - 2
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (30, 30, 30), -1)
                    cv2.line(frame, (x1, y1), (x2, y2), (60, 60, 60), 1)
                    cv2.line(frame, (x2, y1), (x1, y2), (60, 60, 60), 1)
        
        # EMBUTE A ASSINATURA
        frame = self.embed_signature(frame)
        
        # OVERLAYS
        title = "🎨 RGB TABULEIRO ENCODER"
        cv2.putText(frame, title, (self.video_width//2 - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.line(frame, (20, 50), (self.video_width - 20, 50), (100, 100, 100), 1)
        
        # Informações
        info_x = 20
        info_y = self.video_height - 100
        
        filename = metadata.get('original_filename', metadata.get('filename', 'unknown'))
        cv2.putText(frame, f"📁 {filename[:40]}",
                   (info_x, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, f"💾 {metadata.get('size_mb', 0):.2f} MB",
                   (info_x, info_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, f"🔐 {metadata.get('md5', '')[:16]}",
                   (info_x, info_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, f"🔑 Assinatura: {self.signature.decode('ascii')}",
                   (info_x, info_y + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 100), 1)
        
        # Progresso
        progress = (frame_num + 1) / total_frames
        bar_x = self.video_width - 400
        bar_y = self.video_height - 80
        
        cv2.putText(frame, f"🎬 Frame {frame_num+1}/{total_frames}",
                   (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        bar_width = 350
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + 15), (50, 50, 50), -1)
        fill_width = int(bar_width * progress)
        
        for i in range(fill_width):
            color_val = int(100 + 155 * (i / max(fill_width, 1)))
            cv2.line(frame, (bar_x + i, bar_y), (bar_x + i, bar_y + 15), (0, color_val, 0), 1)
        
        cv2.putText(frame, f"{progress*100:.1f}%",
                   (bar_x + bar_width//2 - 25, bar_y - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"🕐 {timestamp}",
                   (self.video_width - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        # Legenda
        legend_y = offset_y + grid_height + 20
        cv2.putText(frame, f"📊 Grid: {self.grid_cols}x{self.grid_rows} | Célula: {self.bytes_per_cell} bytes | Total: {cells_per_frame * self.bytes_per_cell} bytes/frame",
                   (offset_x, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 100), 1)
        
        return frame
    
    def _create_metadata_header(self, original_filename: str, original_data: bytes) -> bytes:
        """
        Cria um cabeçalho com metadados completos do arquivo
        Formato:
        - 4 bytes: Tamanho do cabeçalho JSON
        - N bytes: JSON com metadados (filename, size, md5, extension, etc.)
        - 8 bytes: Tamanho dos dados originais
        - N bytes: Dados originais
        """
        # Extrai extensão do arquivo
        file_extension = Path(original_filename).suffix
        filename_without_ext = Path(original_filename).stem
        
        metadata = {
            'filename': filename_without_ext,
            'extension': file_extension,
            'original_filename': original_filename,
            'size_bytes': len(original_data),
            'md5': hashlib.md5(original_data).hexdigest(),
            'sha256': hashlib.sha256(original_data).hexdigest()[:16],
            'encoder': self.name,
            'signature': self.signature.decode('ascii'),
            'timestamp': datetime.now().isoformat(),
            'grid_cols': self.grid_cols,
            'grid_rows': self.grid_rows,
            'bytes_per_cell': self.bytes_per_cell,
        }
        
        # Converte para JSON
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_len = len(metadata_json)
        
        # Cria cabeçalho
        header = struct.pack('>I', metadata_len)  # 4 bytes - tamanho do JSON
        header += metadata_json                    # N bytes - JSON
        header += struct.pack('>Q', len(original_data))  # 8 bytes - tamanho dos dados
        
        return header
    
    def encode(self, data: bytes, file_path: str,
               progress_callback: Callable[[float, str], None]) -> Tuple[bytes, List[np.ndarray]]:
        
        progress_callback(0.1, "🎨 Preparando dados para tabuleiro RGB...")
        
        # Cria cabeçalho com metadados
        header = self._create_metadata_header(file_path, data)
        data_with_header = header + data
        
        print(f"📊 Header size: {len(header)} bytes")
        print(f"📊 Data size: {len(data)} bytes")
        print(f"📊 Total size: {len(data_with_header)} bytes")
        
        # Calcula bytes por frame
        bytes_per_frame = self.grid_cols * self.grid_rows * self.bytes_per_cell
        num_frames = max(1, math.ceil(len(data_with_header) / bytes_per_frame))
        
        # Padding no último frame
        padded_data = data_with_header + b'\x00' * (num_frames * bytes_per_frame - len(data_with_header))
        
        progress_callback(0.2, f"🎬 Criando {num_frames} frames...")
        
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False).name
        
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter(temp_video, fourcc, self.fps, (self.video_width, self.video_height))
        
        metadata = {
            'filename': os.path.basename(file_path),
            'original_filename': file_path,
            'size_mb': len(data_with_header) / (1024*1024),
            'size_bytes': len(data),
            'md5': hashlib.md5(data).hexdigest()[:16],
            'method': 'RGB Tabuleiro',
            'signature': self.signature.decode('ascii')
        }
        
        frames_preview = []
        
        for i in range(num_frames):
            start = i * bytes_per_frame
            end = start + bytes_per_frame
            chunk = padded_data[start:end]
            
            frame = self._create_checkerboard_frame(chunk, i, num_frames, metadata)
            out.write(frame)
            
            if i % max(1, num_frames // 10) == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_preview.append(cv2.resize(frame_rgb, (640, 360)))
                progress_callback(0.2 + 0.7 * i / num_frames, f"📝 Frame {i+1}/{num_frames}")
        
        out.release()
        
        with open(temp_video, 'rb') as f:
            video_data = f.read()
        
        os.unlink(temp_video)
        
        progress_callback(1.0, "✅ RGB Tabuleiro concluído!")
        return video_data, frames_preview
    
    def decode(self, video_data: bytes) -> Optional[bytes]:
        """Decodifica vídeo RGB Tabuleiro"""
        try:
            temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
            temp_video.write(video_data)
            temp_video.close()
            
            cap = cv2.VideoCapture(temp_video.name)
            
            # Configurações
            grid_cols = self.grid_cols
            grid_rows = self.grid_rows
            cell_size = self.cell_size
            bytes_per_cell = self.bytes_per_cell
            fps = self.fps
            
            # Verifica assinatura
            ret, first_frame = cap.read()
            if not ret:
                cap.release()
                os.unlink(temp_video.name)
                return None
            
            signature_pixels = first_frame[:2, :2]
            signature_found = signature_pixels.tobytes()[:4]
            print(f"🔍 Assinatura encontrada: {signature_found}")
            
            # Volta ao início
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Extrai dados do tabuleiro
            all_data = bytearray()
            frame_count = 0
            processed_frames = 0
            
            grid_width = grid_cols * cell_size
            grid_height = grid_rows * cell_size
            offset_x = (self.video_width - grid_width) // 2
            offset_y = (self.video_height - grid_height) // 2 - 30
            
            bytes_per_frame = grid_cols * grid_rows * bytes_per_cell
            print(f"📊 Bytes por frame: {bytes_per_frame}")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Pega 1 frame por segundo (evita duplicatas)
                if frame_count % fps == 0:
                    frame_data = bytearray()
                    
                    for row in range(grid_rows):
                        for col in range(grid_cols):
                            x = offset_x + col * cell_size + cell_size // 2
                            y = offset_y + row * cell_size + cell_size // 2
                            
                            if 0 <= x < self.video_width and 0 <= y < self.video_height:
                                color_bgr = frame[y, x]
                                # Verifica se não é célula vazia (preta)
                                if not (color_bgr[0] < 50 and color_bgr[1] < 50 and color_bgr[2] < 50):
                                    frame_data.append(color_bgr[2])  # R
                                    frame_data.append(color_bgr[1])  # G
                                    frame_data.append(color_bgr[0])  # B
                                else:
                                    # Célula vazia - padding
                                    frame_data.extend([0, 0, 0])
                            else:
                                frame_data.extend([0, 0, 0])
                    
                    all_data.extend(frame_data)
                    processed_frames += 1
                    
                    if processed_frames == 1:
                        print(f"📝 Primeiro frame: {len(frame_data)} bytes extraídos")
                
                frame_count += 1
            
            cap.release()
            os.unlink(temp_video.name)
            
            print(f"📊 Total extraído: {len(all_data)} bytes")
            
            if len(all_data) < 12:
                print("❌ Dados insuficientes!")
                return None
            
            # ============================================
            # DECODIFICA O CABEÇALHO DE METADADOS
            # ============================================
            # Lê o tamanho do JSON de metadados (4 bytes)
            metadata_len = struct.unpack('>I', bytes(all_data[:4]))[0]
            print(f"📏 Tamanho do metadata JSON: {metadata_len} bytes")
            
            if len(all_data) < 4 + metadata_len + 8:
                print("❌ Dados insuficientes para metadados!")
                return None
            
            # Extrai o JSON
            metadata_json = bytes(all_data[4:4+metadata_len])
            metadata = json.loads(metadata_json.decode('utf-8'))
            print(f"📋 Metadados: {metadata}")
            
            # Lê o tamanho dos dados originais (8 bytes)
            data_start = 4 + metadata_len
            original_size = struct.unpack('>Q', bytes(all_data[data_start:data_start+8]))[0]
            print(f"📏 Tamanho original: {original_size} bytes")
            
            # Extrai os dados
            data_offset = data_start + 8
            file_data = bytes(all_data[data_offset:data_offset+original_size])
            
            print(f"✅ Dados extraídos: {len(file_data)} bytes")
            
            # Opcional: salvar com o nome original
            if 'original_filename' in metadata:
                print(f"📁 Nome original: {metadata['original_filename']}")
            
            return file_data
            
        except Exception as e:
            print(f"❌ Erro no decode: {e}")
            import traceback
            traceback.print_exc()
            return None