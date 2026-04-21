"""Decoder para YUV Barras com verificação de assinatura"""

import numpy as np
import cv2
import os
import tempfile
from typing import Optional


def decode_yuv_bars(video_data: bytes) -> Optional[bytes]:
    """
    Decodifica vídeo YUV Barras de volta para arquivo
    Com verificação de assinatura para maior segurança
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
        temp_video.write(video_data)
        temp_video.close()
        
        cap = cv2.VideoCapture(temp_video.name)
        
        # ============================================
        # CONFIGURAÇÕES
        # ============================================
        video_width = 1280
        video_height = 720
        square_size = 600
        signature_expected = b'YUV1'
        
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
            print(f"✅ Assinatura YUV confirmada: {signature_found.decode('ascii')}")
        else:
            print(f"⚠️ Assinatura YUV não confere. Esperado: {signature_expected}, Encontrado: {signature_found}")
        
        # Volta para o início
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        
        # ============================================
        # MÉTODO 1: DETECÇÃO POR BORDA VERDE
        # ============================================
        green_lower = np.array([0, 200, 0])
        green_upper = np.array([100, 255, 100])
        mask = cv2.inRange(frame, green_lower, green_upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            print("📐 YUV: Usando método de detecção por borda verde")
            
            largest = max(contours, key=cv2.contourArea)
            x, y, w_box, h_box = cv2.boundingRect(largest)
            
            # Extrai região interna
            inner = frame[y+2:y+h_box-2, x+2:x+w_box-2]
            
            # Converte para bytes (escala de cinza = 1 byte por pixel)
            if len(inner.shape) == 3:
                # Converte para grayscale
                gray = cv2.cvtColor(inner, cv2.COLOR_BGR2GRAY)
                data_bytes = gray.tobytes()
            else:
                data_bytes = inner.tobytes()
            
            # Lê cabeçalho (8 bytes = tamanho original)
            if len(data_bytes) >= 8:
                original_size = int.from_bytes(data_bytes[:8], 'big')
                file_data = data_bytes[8:8+original_size]
                
                cap.release()
                os.unlink(temp_video.name)
                return file_data
        
        # ============================================
        # MÉTODO 2: EXTRAÇÃO DIRETA DO QUADRADO CENTRAL
        # ============================================
        print("📐 YUV: Usando método de extração direta")
        
        square_x = (video_width - square_size) // 2
        square_y = (video_height - square_size) // 2
        
        # Extrai o quadrado central
        inner = frame[square_y:square_y+square_size, square_x:square_x+square_size]
        
        # Converte para grayscale e bytes
        if len(inner.shape) == 3:
            gray = cv2.cvtColor(inner, cv2.COLOR_BGR2GRAY)
            data_bytes = gray.tobytes()
        else:
            data_bytes = inner.tobytes()
        
        cap.release()
        os.unlink(temp_video.name)
        
        # Remove padding (zeros no final)
        data_bytes = data_bytes.rstrip(b'\x00')
        
        # Lê cabeçalho
        if len(data_bytes) >= 8:
            original_size = int.from_bytes(data_bytes[:8], 'big')
            
            if original_size > 0 and original_size <= len(data_bytes):
                return data_bytes[8:8+original_size]
        
        return data_bytes
        
    except Exception as e:
        print(f"❌ Erro no decode YUV Barras: {e}")
        import traceback
        traceback.print_exc()
        return None


def decode_yuv_with_signature_check(video_data: bytes, expected_signature: bytes = b'YUV1') -> Optional[bytes]:
    """
    Decodifica YUV com verificação estrita de assinatura
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
            print(f"❌ Assinatura YUV incorreta. Esperado: {expected_signature}, Encontrado: {signature_found}")
            return None
        
        print(f"✅ Assinatura YUV verificada: {signature_found.decode('ascii')}")
        return decode_yuv_bars(video_data)
        
    except Exception as e:
        print(f"❌ Erro na verificação de assinatura YUV: {e}")
        return None