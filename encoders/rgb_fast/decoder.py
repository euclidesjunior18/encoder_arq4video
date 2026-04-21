"""Decoder para RGB FAST com verificação de assinatura"""

import numpy as np
import cv2
import zlib
import hashlib
import os
import tempfile
from typing import Optional


def decode_rgb_fast(video_data: bytes, repeat_frames: int = 2) -> Optional[bytes]:
    """
    Decodifica vídeo RGB FAST de volta para arquivo
    Com verificação de assinatura e integridade MD5
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video.write(video_data)
        temp_video.close()
        
        cap = cv2.VideoCapture(temp_video.name)
        
        # ============================================
        # CONFIGURAÇÕES
        # ============================================
        signature_expected = b'FST1'
        
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
            print(f"✅ Assinatura FAST confirmada: {signature_found.decode('ascii')}")
        else:
            print(f"⚠️ Assinatura FAST não confere. Esperado: {signature_expected}, Encontrado: {signature_found}")
        
        # Volta para o início
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # ============================================
        # EXTRAÇÃO DOS DADOS
        # ============================================
        chunks_data = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Pega frames não duplicados
            if frame_count % repeat_frames == 0:
                # Achata o frame e converte para bytes
                flat = frame.reshape(-1, 3)
                chunk_bytes = flat.tobytes()
                
                # Remove padding (zeros no final)
                chunk_bytes = chunk_bytes.rstrip(b'\x00')
                chunks_data.append(chunk_bytes)
            
            frame_count += 1
        
        cap.release()
        os.unlink(temp_video.name)
        
        if not chunks_data:
            print("❌ Nenhum dado extraído do vídeo FAST")
            return None
        
        # ============================================
        # RECONSTRUÇÃO DO PAYLOAD
        # ============================================
        payload = b''.join(chunks_data)
        
        if len(payload) < 32:
            print(f"❌ Payload muito pequeno: {len(payload)} bytes")
            return None
        
        # Lê cabeçalho FAST
        original_size = int.from_bytes(payload[:8], 'big')
        compressed_size = int.from_bytes(payload[8:16], 'big')
        stored_md5 = payload[16:32]
        
        print(f"📊 FAST: original={original_size}, comprimido={compressed_size}")
        
        # Extrai dados comprimidos
        compressed = payload[32:32+compressed_size]
        
        # ============================================
        # DESCOMPRESSÃO E VERIFICAÇÃO
        # ============================================
        try:
            data = zlib.decompress(compressed)
        except zlib.error as e:
            print(f"❌ Erro na descompressão zlib: {e}")
            return None
        
        # Verifica tamanho
        if len(data) < original_size:
            data = data[:original_size]
        
        # Verifica integridade MD5
        calculated_md5 = hashlib.md5(data).digest()
        if calculated_md5 == stored_md5:
            print(f"✅ MD5 verificado com sucesso!")
        else:
            print(f"⚠️ MD5 não confere. Dados podem estar corrompidos.")
        
        return data[:original_size]
        
    except Exception as e:
        print(f"❌ Erro no decode RGB FAST: {e}")
        import traceback
        traceback.print_exc()
        return None


def decode_fast_with_signature_check(video_data: bytes, expected_signature: bytes = b'FST1') -> Optional[bytes]:
    """
    Decodifica FAST com verificação estrita de assinatura
    """
    try:
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
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
            print(f"❌ Assinatura FAST incorreta. Esperado: {expected_signature}, Encontrado: {signature_found}")
            return None
        
        print(f"✅ Assinatura FAST verificada: {signature_found.decode('ascii')}")
        return decode_rgb_fast(video_data)
        
    except Exception as e:
        print(f"❌ Erro na verificação de assinatura FAST: {e}")
        return None