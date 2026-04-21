"""Decoder para QR Code Sequence com verificação de assinatura"""

import numpy as np
import cv2
import zlib
import json
import struct
import os
import tempfile
from typing import Optional, List

# Tentar importar dependências do QR Code
try:
    from PIL import Image
    from pyzbar.pyzbar import decode as qr_decode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("⚠️ pyzbar não instalado. Decodificação QR limitada.")


def decode_qr_sequence(video_data: bytes) -> Optional[bytes]:
    """
    Decodifica vídeo QR Code Sequence de volta para arquivo
    Com verificação de assinatura
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
        temp_video.write(video_data)
        temp_video.close()
        
        cap = cv2.VideoCapture(temp_video.name)
        
        # ============================================
        # CONFIGURAÇÕES
        # ============================================
        fps = 30
        signature_expected = b'QRC1'
        
        # ============================================
        # VERIFICA ASSINATURA
        # ============================================
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            os.unlink(temp_video.name)
            return None
        
        # Extrai assinatura dos primeiros pixels (2x2)
        signature_pixels = first_frame[:2, :2]
        signature_found = signature_pixels.tobytes()[:4]
        
        if signature_found == signature_expected:
            print(f"✅ Assinatura QR confirmada: {signature_found.decode('ascii')}")
        else:
            print(f"⚠️ Assinatura QR não confere. Esperado: {signature_expected}, Encontrado: {signature_found}")
        
        # Volta para o início
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # ============================================
        # DECODIFICAÇÃO DOS QR CODES
        # ============================================
        if QRCODE_AVAILABLE:
            return _decode_with_pyzbar(cap, fps, temp_video.name)
        else:
            return _decode_fallback(cap, temp_video.name)
        
    except Exception as e:
        print(f"❌ Erro no decode QR Sequence: {e}")
        import traceback
        traceback.print_exc()
        return None


def _decode_with_pyzbar(cap: cv2.VideoCapture, fps: int, temp_path: str) -> Optional[bytes]:
    """Decodifica usando pyzbar (método principal)"""
    
    chunks_data = []
    frame_count = 0
    metadata = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Pega frames não duplicados (cada QR aparece 2 vezes)
        if frame_count % 2 == 0:
            # Converte para PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            # Decodifica QR code
            decoded_objects = qr_decode(pil_img)
            
            if decoded_objects:
                qr_data = decoded_objects[0].data
                
                # Tenta interpretar como JSON (header)
                try:
                    json_data = json.loads(qr_data)
                    if not metadata:
                        metadata = json_data
                        print(f"📋 Metadata QR: {metadata.get('filename', 'unknown')}")
                except:
                    # Dados binários normais
                    if len(qr_data) > 4:
                        # Remove checksum (4 bytes)
                        chunks_data.append(qr_data[4:])
        
        frame_count += 1
    
    cap.release()
    os.unlink(temp_path)
    
    if chunks_data:
        return b''.join(chunks_data)
    
    return None


def _decode_fallback(cap: cv2.VideoCapture, temp_path: str) -> Optional[bytes]:
    """Fallback: tenta extrair dados da região central"""
    
    # Tenta detectar borda verde
    ret, frame = cap.read()
    if not ret:
        cap.release()
        os.unlink(temp_path)
        return None
    
    green_lower = np.array([0, 200, 0])
    green_upper = np.array([100, 255, 100])
    mask = cv2.inRange(frame, green_lower, green_upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w_box, h_box = cv2.boundingRect(largest)
        
        inner = frame[y+2:y+h_box-2, x+2:x+w_box-2]
        
        if len(inner.shape) == 3:
            flat = inner.reshape(-1, 3)
            data_bytes = flat.tobytes()
        else:
            data_bytes = inner.tobytes()
        
        cap.release()
        os.unlink(temp_path)
        
        # Remove padding
        data_bytes = data_bytes.rstrip(b'\x00')
        
        if len(data_bytes) >= 8:
            original_size = int.from_bytes(data_bytes[:8], 'big')
            return data_bytes[8:8+original_size]
    
    cap.release()
    os.unlink(temp_path)
    return None


def decode_qr_with_signature_check(video_data: bytes, expected_signature: bytes = b'QRC1') -> Optional[bytes]:
    """
    Decodifica QR com verificação estrita de assinatura
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
        temp_video.write(video_data)
        temp_video.close()
        
        cap = cv2.VideoCapture(temp_video.name)
        ret, first_frame = cap.read()
        cap.release()
        os.unlink(temp_video.name)
        
        if not ret:
            return None
        
        signature_pixels = first_frame[:2, :2]
        signature_found = signature_pixels.tobytes()[:4]
        
        if signature_found != expected_signature:
            print(f"❌ Assinatura QR incorreta. Esperado: {expected_signature}, Encontrado: {signature_found}")
            return None
        
        print(f"✅ Assinatura QR verificada: {signature_found.decode('ascii')}")
        return decode_qr_sequence(video_data)
        
    except Exception as e:
        print(f"❌ Erro na verificação de assinatura QR: {e}")
        return None


# Alias para compatibilidade
decode_qr_code = decode_qr_sequence