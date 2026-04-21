"""
Classe base abstrata para todos os encoders
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Callable, Optional, Type
import numpy as np
import cv2
import tempfile
import os


class BaseEncoder(ABC):
    """Classe base que todos os plugins de encoder devem herdar"""
    
    # ============================================
    # PROPRIEDADES ABSTRATAS
    # ============================================
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do encoder"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nome para exibição na interface"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição do método"""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Ícone/emoji do método"""
        pass
    
    @property
    @abstractmethod
    def output_extension(self) -> str:
        """Extensão do arquivo de saída (ex: 'avi', 'mp4')"""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """MIME type do vídeo gerado"""
        pass
    
    @property
    @abstractmethod
    def signature(self) -> bytes:
        """
        Assinatura única do encoder (4 bytes)
        Exemplo: b'RGB1', b'YUV1', b'QRC1', b'FST1'
        """
        pass
    
    # ============================================
    # MÉTODOS ABSTRATOS
    # ============================================
    @abstractmethod
    def encode(self, 
               data: bytes, 
               file_path: str,
               progress_callback: Callable[[float, str], None]) -> Tuple[bytes, List[np.ndarray]]:
        """
        Codifica dados em vídeo
        
        Args:
            data: Dados binários do arquivo
            file_path: Caminho/nome do arquivo original
            progress_callback: Função(progresso: float, mensagem: str)
            
        Returns:
            Tuple[video_data: bytes, preview_frames: List[np.ndarray]]
        """
        pass
    
    @abstractmethod
    def decode(self, video_data: bytes) -> Optional[bytes]:
        """
        Decodifica vídeo de volta para dados originais
        
        Args:
            video_data: Bytes do vídeo
            
        Returns:
            Dados originais ou None se falhar
        """
        pass
    
    # ============================================
    # MÉTODOS DE IDENTIFICAÇÃO
    # ============================================
    def can_decode(self, video_data: bytes) -> bool:
        """
        Verifica se este decoder consegue decodificar o vídeo
        Baseado na assinatura embutida nos primeiros pixels
        """
        try:
            # Salva vídeo temporário
            temp_video = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
            temp_video.write(video_data)
            temp_video.close()
            
            cap = cv2.VideoCapture(temp_video.name)
            ret, frame = cap.read()
            cap.release()
            os.unlink(temp_video.name)
            
            if not ret:
                return False
            
            # Procura pela assinatura nos primeiros pixels (2x2 = 4 pixels = 12 bytes)
            signature_pixels = frame[:2, :2]  # 2x2 pixels
            signature_bytes = signature_pixels.tobytes()[:len(self.signature)]
            
            return signature_bytes == self.signature
            
        except Exception as e:
            print(f"Erro ao verificar assinatura: {e}")
            return False
    
    def embed_signature(self, frame: np.ndarray) -> np.ndarray:
        """
        Embute a assinatura nos primeiros pixels do frame
        (canto superior esquerdo)
        """
        # Garante que a assinatura tenha pelo menos 12 bytes (4 pixels RGB)
        sig_bytes = self.signature
        if len(sig_bytes) < 12:
            sig_bytes = sig_bytes + b'\x00' * (12 - len(sig_bytes))
        
        # Converte para pixels e embute no canto superior esquerdo
        sig_pixels = np.frombuffer(sig_bytes, dtype=np.uint8).reshape(2, 2, 3)
        frame[:2, :2] = sig_pixels
        
        return frame
    
    def extract_signature(self, frame: np.ndarray) -> bytes:
        """
        Extrai a assinatura de um frame
        """
        signature_pixels = frame[:2, :2]
        signature_bytes = signature_pixels.tobytes()
        
        # Remove padding (zeros)
        return signature_bytes.rstrip(b'\x00')
    
    def get_info(self, data: bytes) -> dict:
        """
        Retorna informações adicionais sobre a codificação
        (Opcional - pode ser sobrescrito)
        """
        return {}


class EncoderRegistry:
    """Registro central de encoders para identificação automática"""
    
    _encoders = {}
    
    @classmethod
    def register(cls, encoder_class: Type[BaseEncoder]):
        """
        Registra um encoder no sistema
        
        Args:
            encoder_class: Classe do encoder (não instanciada)
        """
        try:
            # Instancia temporariamente para pegar a assinatura
            encoder = encoder_class()
            cls._encoders[encoder.signature] = encoder_class
            print(f"📝 Encoder registrado: {encoder.name} -> Assinatura: {encoder.signature}")
        except Exception as e:
            print(f"❌ Erro ao registrar encoder {encoder_class.__name__}: {e}")
    
    @classmethod
    def identify(cls, video_data: bytes) -> Optional[BaseEncoder]:
        """
        Identifica qual encoder foi usado para criar o vídeo
        
        Args:
            video_data: Bytes do vídeo
            
        Returns:
            Instância do encoder identificado ou None
        """
        for signature, encoder_class in cls._encoders.items():
            try:
                encoder = encoder_class()
                if encoder.can_decode(video_data):
                    print(f"✅ Vídeo identificado como: {encoder.display_name}")
                    return encoder
            except Exception as e:
                print(f"⚠️ Erro ao testar encoder {encoder_class.__name__}: {e}")
                continue
        
        print("❌ Nenhum encoder reconheceu o formato do vídeo")
        return None
    
    @classmethod
    def get_all(cls) -> dict:
        """Retorna todos os encoders registrados"""
        return cls._encoders.copy()
    
    @classmethod
    def get_by_signature(cls, signature: bytes) -> Optional[Type[BaseEncoder]]:
        """Retorna um encoder pela sua assinatura"""
        return cls._encoders.get(signature)
    
    @classmethod
    def list_registered(cls) -> list:
        """Lista todos os encoders registrados"""
        encoders_info = []
        for signature, encoder_class in cls._encoders.items():
            try:
                encoder = encoder_class()
                encoders_info.append({
                    'name': encoder.name,
                    'display_name': encoder.display_name,
                    'signature': signature,
                    'icon': encoder.icon
                })
            except:
                pass
        return encoders_info
    
    @classmethod
    def clear(cls):
        """Limpa o registro (útil para testes)"""
        cls._encoders.clear()