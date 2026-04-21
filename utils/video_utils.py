"""Utilitários para processamento de vídeo"""

import cv2
import numpy as np
import math


def create_bordered_frame(frame: np.ndarray, 
                         video_width: int, 
                         video_height: int,
                         square_size: int,
                         metadata: dict,
                         frame_num: int,
                         total_frames: int) -> np.ndarray:
    """Cria um frame com borda decorativa e informações"""
    
    h, w = video_height, video_width
    bordered = np.zeros((h, w, 3), dtype=np.uint8)
    
    square_x = (w - square_size) // 2
    square_y = (h - square_size) // 2
    
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    frame_resized = cv2.resize(frame, (square_size, square_size))
    bordered[square_y:square_y+square_size, square_x:square_x+square_size] = frame_resized
    
    border_thickness = 2 + int(math.sin(frame_num * 0.1) * 1)
    cv2.rectangle(bordered, (square_x-border_thickness, square_y-border_thickness),
                 (square_x+square_size+border_thickness, square_y+square_size+border_thickness),
                 (0, 255, 0), border_thickness)
    
    for i in range(h):
        alpha = i / h
        color = tuple(int(c * alpha) for c in (20, 20, 40))
        cv2.line(bordered, (0, i), (w, i), color, 1)
    
    title = "🎥 FILE-TO-VIDEO ENCODER 🎥"
    cv2.putText(bordered, title, (w//2 - 200, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    info_y = 70
    cv2.putText(bordered, f"📁 {metadata.get('filename', 'unknown')[:45]}", 
               (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    info_y += 25
    cv2.putText(bordered, f"💾 {metadata.get('size_mb', 0):.2f} MB", 
               (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    info_y += 25
    cv2.putText(bordered, f"⚙️ {metadata.get('method', 'Unknown')} | 🎬 {frame_num+1}/{total_frames}", 
               (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    progress = (frame_num + 1) / total_frames
    bar_width = int((w - 200) * progress)
    cv2.rectangle(bordered, (100, h - 50), (w - 100, h - 30), (30, 30, 30), -1)
    
    for i in range(bar_width):
        color_val = int(100 + 155 * (i / max(bar_width, 1)))
        cv2.line(bordered, (100 + i, h - 50), (100 + i, h - 30), 
                (0, color_val, 0), 1)
    
    cv2.putText(bordered, f"{progress*100:.1f}%", (w//2 - 30, h - 55),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    for i in range(8):
        level = int((math.sin(frame_num * 0.1 + i * 0.5) + 1) * 25)
        color = (0, 255 - i*20, 0)
        cv2.rectangle(bordered, 
                     (w - 180 + i*20, h - 90 - level), 
                     (w - 180 + i*20 + 15, h - 90), 
                     color, -1)
    
    return bordered


def extract_frames_for_preview(video_data: bytes, max_frames: int = 10) -> list:
    """Extrai frames do vídeo para preview"""
    import tempfile
    import os
    
    frames = []
    temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
    temp_video.write(video_data)
    temp_video.close()
    
    cap = cv2.VideoCapture(temp_video.name)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, frame_count // max_frames)
    
    for i in range(0, min(frame_count, max_frames * step), step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 360))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
    
    cap.release()
    os.unlink(temp_video.name)
    
    return frames