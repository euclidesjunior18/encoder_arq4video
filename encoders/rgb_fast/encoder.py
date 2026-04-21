"""Encoder RGB FAST - YouTube Proof + Ultra Rápido"""

import numpy as np
import cv2
import zlib
import os
import math
import hashlib
import tempfile
from typing import Callable, Tuple, List, Optional

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from encoders.base_encoder import BaseEncoder


class RGBFastEncoder(BaseEncoder):
    
    def __init__(self):
        self.CHUNK_SIZE = 4096
        self.REPEAT_FRAMES = 2
    
    @property
    def signature(self) -> bytes:
        """Assinatura única do encoder (4 bytes)"""
        return b'FST1'
    
    @property
    def name(self) -> str:
        return "rgb_fast"
    
    @property
    def display_name(self) -> str:
        return "⚡ RGB FAST"
    
    @property
    def description(self) -> str:
        return "YouTube Proof + Ultra Rápido. Compressão zlib e MP4 otimizado."
    
    @property
    def icon(self) -> str:
        return "⚡"
    
    @property
    def output_extension(self) -> str:
        return "mp4"
    
    @property
    def mime_type(self) -> str:
        return "video/mp4"
    
    def encode(self, data: bytes, file_path: str,
               progress_callback: Callable[[float, str], None],
               video_width: int = 640,
               video_height: int = 360) -> Tuple[bytes, List[np.ndarray]]:
        
        progress_callback(0.05, "🗜️ Comprimindo dados...")
        
        compressed = zlib.compress(data, level=6)
        
        header = (
            len(data).to_bytes(8, 'big') +
            len(compressed).to_bytes(8, 'big') +
            hashlib.md5(data).digest()
        )
        
        payload = header + compressed
        
        progress_callback(0.1, "📦 Dividindo em chunks...")
        
        chunks = [
            payload[i:i+self.CHUNK_SIZE]
            for i in range(0, len(payload), self.CHUNK_SIZE)
        ]
        
        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, 30, (video_width, video_height))
        
        frames_preview = []
        
        for idx, chunk in enumerate(chunks):
            pad = (-len(chunk)) % 3
            if pad:
                chunk += b'\x00' * pad
            
            pixels = np.frombuffer(chunk, dtype=np.uint8).reshape(-1, 3)
            
            side = math.ceil(math.sqrt(len(pixels)))
            total = side * side
            
            frame = np.zeros((total, 3), dtype=np.uint8)
            frame[:len(pixels)] = pixels
            frame = frame.reshape((side, side, 3))
            
            frame = cv2.resize(frame, (video_width, video_height))
            
            for _ in range(self.REPEAT_FRAMES):
                out.write(frame)
            
            if idx % 5 == 0:
                preview = cv2.resize(frame, (320, 180))
                preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                frames_preview.append(preview)
            
            if idx % 3 == 0:
                progress_callback(
                    0.1 + 0.85 * (idx / len(chunks)),
                    f"🎬 Chunk {idx+1}/{len(chunks)}"
                )
        
        out.release()
        
        with open(temp_video, "rb") as f:
            video_data = f.read()
        
        os.unlink(temp_video)
        
        progress_callback(1.0, "✅ FAST encoding concluído!")
        
        return video_data, frames_preview
    
    def decode(self, video_data: bytes) -> Optional[bytes]:
        try:
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_video.write(video_data)
            temp_video.close()
            
            cap = cv2.VideoCapture(temp_video.name)
            
            chunks_data = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % self.REPEAT_FRAMES == 0:
                    flat = frame.reshape(-1, 3)
                    chunk_bytes = flat.tobytes()
                    chunk_bytes = chunk_bytes.rstrip(b'\x00')
                    chunks_data.append(chunk_bytes)
                
                frame_count += 1
            
            cap.release()
            os.unlink(temp_video.name)
            
            if not chunks_data:
                return None
            
            payload = b''.join(chunks_data)
            
            original_size = int.from_bytes(payload[:8], 'big')
            compressed_size = int.from_bytes(payload[8:16], 'big')
            stored_md5 = payload[16:32]
            
            compressed = payload[32:32+compressed_size]
            
            data = zlib.decompress(compressed)
            
            if hashlib.md5(data).digest() == stored_md5:
                return data[:original_size]
            
            return data[:original_size]
            
        except Exception as e:
            print(f"Erro decode FAST: {e}")
            return None