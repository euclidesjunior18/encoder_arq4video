"""Decoder para RGB Tabuleiro"""

import numpy as np
import cv2
import os
import tempfile
import json
import struct
from typing import Optional


def decode_rgb_squares(video_data: bytes) -> Optional[bytes]:
    """Decodifica vídeo RGB Tabuleiro"""
    from encoders.rgb_squares.encoder import RGBSquaresEncoder
    encoder = RGBSquaresEncoder()
    return encoder.decode(video_data)


def decode_rgb_squares_with_metadata(video_data: bytes) -> Optional[tuple]:
    """
    Decodifica e retorna (dados, metadados)
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
        temp_video.write(video_data)
        temp_video.close()
        
        cap = cv2.VideoCapture(temp_video.name)
        
        # Configurações
        video_width = 1280
        video_height = 720
        grid_cols = 16
        grid_rows = 9
        cell_size = 60
        bytes_per_cell = 3
        fps = 30
        
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            os.unlink(temp_video.name)
            return None
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        all_data = bytearray()
        frame_count = 0
        
        grid_width = grid_cols * cell_size
        grid_height = grid_rows * cell_size
        offset_x = (video_width - grid_width) // 2
        offset_y = (video_height - grid_height) // 2 - 30
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Processa TODOS os frames
                frame_data = bytearray()
                
                for row in range(grid_rows):
                    for col in range(grid_cols):
                        x = offset_x + col * cell_size + cell_size // 2
                        y = offset_y + row * cell_size + cell_size // 2
                        
                        if 0 <= x < video_width and 0 <= y < video_height:
                            color_bgr = frame[y, x]
                            if not (color_bgr[0] < 50 and color_bgr[1] < 50 and color_bgr[2] < 50):
                                frame_data.append(color_bgr[2])
                                frame_data.append(color_bgr[1])
                                frame_data.append(color_bgr[0])
                            else:
                                frame_data.extend([0, 0, 0])
                        else:
                            frame_data.extend([0, 0, 0])
                
                all_data.extend(frame_data)
            
            frame_count += 1
        
        cap.release()
        os.unlink(temp_video.name)
        
        if len(all_data) < 12:
            return None
        
        # Decodifica metadados
        metadata_len = struct.unpack('>I', bytes(all_data[:4]))[0]
        metadata_json = bytes(all_data[4:4+metadata_len])
        print("RAW METADATA:", metadata_json[:100])
        print("LEN:", metadata_len)
        metadata = json.loads(metadata_json.decode('utf-8'))
        
        data_start = 4 + metadata_len
        original_size = struct.unpack('>Q', bytes(all_data[data_start:data_start+8]))[0]
        
        data_offset = data_start + 8
        file_data = bytes(all_data[data_offset:data_offset+original_size])
        
        return file_data, metadata
        
    except Exception as e:
        print(f"Erro no decode: {e}")
        return None