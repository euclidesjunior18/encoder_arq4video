"""Encoder QR Code Sequence - YouTube Ready"""

import numpy as np
import cv2
import math
import os
import json
import struct
import hashlib
import tempfile
from datetime import datetime
from typing import Callable, Tuple, List, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from encoders.base_encoder import BaseEncoder

# Tentar importar QR Code
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class QRSequenceEncoder(BaseEncoder):
    
    def __init__(self):
        self.qr_version = 40
        self.qr_box_size = 4
        self.chunk_size = 2500
        self.video_width = 1280
        self.video_height = 720
        self.fps = 30
    
    @property
    def signature(self) -> bytes:
        """Assinatura única do encoder (4 bytes)"""
        return b'QRC1'

    @property
    def name(self) -> str:
        return "qr_sequence"
    
    @property
    def display_name(self) -> str:
        return "📱 QR Code Sequence"
    
    @property
    def description(self) -> str:
        return "Resistente à compressão do YouTube. Correção de erro embutida."
    
    @property
    def icon(self) -> str:
        return "📱"
    
    @property
    def output_extension(self) -> str:
        return "avi"
    
    @property
    def mime_type(self) -> str:
        return "video/avi"
    
    @property
    def available(self) -> bool:
        return QRCODE_AVAILABLE
    
    def _create_qr_frame(self, data: bytes, frame_num: int, total_frames: int,
                         metadata: dict, is_header: bool = False) -> np.ndarray:
        """Cria um frame com QR code centralizado"""
        if not QRCODE_AVAILABLE:
            raise ImportError("QRCode não instalado")
        
        qr = qrcode.QRCode(
            version=self.qr_version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=self.qr_box_size,
            border=2,
        )
        
        if is_header:
            qr.add_data(json.dumps(metadata).encode())
        else:
            import zlib
            checksum = zlib.crc32(data) & 0xFFFFFFFF
            qr.add_data(struct.pack('>I', checksum) + data)
        
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_array = np.array(qr_img.convert('RGB'))
        
        frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
        
        qr_h, qr_w = qr_array.shape[:2]
        x_offset = (self.video_width - qr_w) // 2
        y_offset = (self.video_height - qr_h) // 2 - 50
        
        frame[y_offset:y_offset+qr_h, x_offset:x_offset+qr_w] = qr_array
        
        # Overlays
        cv2.putText(frame, "📱 QR CODE ENCODER - YOUTUBE READY 📱", 
                   (self.video_width//2 - 280, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        progress = (frame_num + 1) / total_frames
        bar_width = int((self.video_width - 200) * progress)
        cv2.rectangle(frame, (100, 70), (self.video_width - 100, 90), (50, 50, 50), -1)
        cv2.rectangle(frame, (100, 70), (100 + bar_width, 90), (0, 255, 0), -1)
        
        cv2.putText(frame, f"Frame {frame_num+1}/{total_frames}", 
                   (50, self.video_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        return frame
    
    def encode(self, data: bytes, file_path: str,
               progress_callback: Callable[[float, str], None]) -> Tuple[bytes, List[np.ndarray]]:
        
        if not QRCODE_AVAILABLE:
            raise ImportError("QRCode não instalado. Execute: pip install qrcode[pil]")
        
        progress_callback(0.05, "📱 Preparando QR Codes...")
        
        metadata = {
            'filename': os.path.basename(file_path),
            'size_bytes': len(data),
            'size_mb': len(data) / (1024*1024),
            'md5': hashlib.md5(data).hexdigest(),
            'timestamp': datetime.now().isoformat(),
            'total_chunks': math.ceil(len(data) / self.chunk_size),
            'method': 'QR Code Sequence',
        }
        
        chunks = [data[i:i+self.chunk_size] for i in range(0, len(data), self.chunk_size)]
        total_frames = len(chunks) + 1
        
        progress_callback(0.1, f"🎬 Criando {total_frames} QR codes...")
        
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False).name
        
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(temp_video, fourcc, self.fps, (self.video_width, self.video_height))
        
        frames_preview = []
        
        # Frame header
        header_frame = self._create_qr_frame(b'', 0, total_frames, metadata, is_header=True)
        for _ in range(self.fps * 2):
            out.write(header_frame)
        frame_rgb = cv2.cvtColor(header_frame, cv2.COLOR_BGR2RGB)
        frames_preview.append(cv2.resize(frame_rgb, (640, 360)))
        
        # Frames de dados
        for i, chunk in enumerate(chunks):
            frame = self._create_qr_frame(chunk, i+1, total_frames, metadata)
            out.write(frame)
            out.write(frame)
            
            if i % max(1, len(chunks) // 8) == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_preview.append(cv2.resize(frame_rgb, (640, 360)))
                progress_callback(0.2 + 0.7 * i / len(chunks), f"📝 QR Code {i+1}/{len(chunks)}")
        
        # Frame final
        final_frame = self._create_qr_frame(b'', total_frames, total_frames, metadata, is_header=True)
        for _ in range(self.fps * 3):
            out.write(final_frame)
        frame_rgb = cv2.cvtColor(final_frame, cv2.COLOR_BGR2RGB)
        frames_preview.append(cv2.resize(frame_rgb, (640, 360)))
        
        out.release()
        
        with open(temp_video, 'rb') as f:
            video_data = f.read()
        
        os.unlink(temp_video)
        
        progress_callback(1.0, "✅ QR Code concluído!")
        return video_data, frames_preview
    
    def decode(self, video_data: bytes) -> Optional[bytes]:
        """Decodifica vídeo QR Code Sequence"""
        try:
            import zlib
            from PIL import Image
            from pyzbar.pyzbar import decode as qr_decode
            
            temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
            temp_video.write(video_data)
            temp_video.close()
            
            cap = cv2.VideoCapture(temp_video.name)
            
            chunks_data = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Pega um frame a cada 2 (por causa da duplicação)
                if frame_count % 2 == 0 and frame_count > self.fps * 2:  # pula header
                    # Converte para PIL e decodifica QR
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    
                    decoded = qr_decode(pil_img)
                    if decoded:
                        chunk_data = decoded[0].data
                        # Remove checksum (4 bytes)
                        if len(chunk_data) > 4:
                            chunks_data.append(chunk_data[4:])
                
                frame_count += 1
            
            cap.release()
            os.unlink(temp_video.name)
            
            if chunks_data:
                return b''.join(chunks_data)
            
            return None
            
        except ImportError:
            # Fallback: tenta outros métodos
            from encoders.rgb_squares.encoder import RGBSquaresEncoder
            return RGBSquaresEncoder().decode(video_data)
        except Exception as e:
            print(f"Erro decode QR: {e}")
            return None