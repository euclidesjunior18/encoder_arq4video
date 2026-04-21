"""Encoder YUV Barras de Luminância"""

import numpy as np
import cv2
import math
import os
import hashlib
import tempfile
from typing import Callable, Tuple, List, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from encoders.base_encoder import BaseEncoder
from utils.video_utils import create_bordered_frame


class YUVBarsEncoder(BaseEncoder):

    @property
    def signature(self) -> bytes:
        """Assinatura única do encoder (4 bytes)"""
        return b'YUV1'
    
    @property
    def name(self) -> str:
        return "yuv_bars"
    
    @property
    def display_name(self) -> str:
        return "📊 YUV Barras"
    
    @property
    def description(self) -> str:
        return "Mais rápido e compacto. 1 byte por pixel em escala de cinza."
    
    @property
    def icon(self) -> str:
        return "📊"
    
    @property
    def output_extension(self) -> str:
        return "avi"
    
    @property
    def mime_type(self) -> str:
        return "video/avi"
    
    def encode(self, data: bytes, file_path: str,
               progress_callback: Callable[[float, str], None],
               video_width: int = 1280,
               video_height: int = 720,
               square_size: int = 600) -> Tuple[bytes, List[np.ndarray]]:
        
        progress_callback(0.1, "📊 Preparando dados YUV...")
        
        header = len(data).to_bytes(8, 'big')
        data_with_header = header + data
        
        bytes_per_frame = square_size * square_size
        num_frames = max(1, math.ceil(len(data_with_header) / bytes_per_frame))
        
        padded_data = data_with_header + b'\x00' * (num_frames * bytes_per_frame - len(data_with_header))
        frames_data = np.frombuffer(padded_data, dtype=np.uint8)
        frames_data = frames_data.reshape((num_frames, square_size, square_size))
        
        progress_callback(0.2, f"🎬 Criando {num_frames} frames YUV...")
        
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False).name
        
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter(temp_video, fourcc, 30, (video_width, video_height))
        
        metadata = {
            'filename': os.path.basename(file_path),
            'size_mb': len(data_with_header) / (1024*1024),
            'size_bytes': len(data),
            'md5': hashlib.md5(data).hexdigest()[:16],
            'method': 'YUV Luminance Bars',
        }
        
        frames_preview = []
        step = max(1, num_frames // 10)
        
        for i, frame_data in enumerate(frames_data):
            bordered = create_bordered_frame(frame_data, video_width, video_height,
                                            square_size, metadata, i, num_frames)
            out.write(bordered)
            
            if i % step == 0:
                frame_rgb = cv2.cvtColor(bordered, cv2.COLOR_BGR2RGB)
                frames_preview.append(cv2.resize(frame_rgb, (640, 360)))
                progress_callback(0.2 + 0.7 * i / num_frames, f"📝 Frame {i+1}/{num_frames}")
        
        out.release()
        
        with open(temp_video, 'rb') as f:
            video_data = f.read()
        
        os.unlink(temp_video)
        
        progress_callback(1.0, "✅ YUV concluído!")
        return video_data, frames_preview
    
    def decode(self, video_data: bytes) -> Optional[bytes]:
        # Reutiliza o mesmo método do RGB Squares
        from encoders.rgb_squares.encoder import RGBSquaresEncoder
        return RGBSquaresEncoder().decode(video_data)