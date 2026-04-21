"""
Detector automático de plugins de encoder
Sistema genérico - descobre dinamicamente todos os encoders disponíveis
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, Optional, List

# Importa a classe base
try:
    from .base_encoder import BaseEncoder, EncoderRegistry
except ImportError:
    # Fallback para importação absoluta
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from encoders.base_encoder import BaseEncoder, EncoderRegistry


def discover_encoders() -> Dict[str, Type[BaseEncoder]]:
    """
    Descobre automaticamente todos os encoders na pasta encoders/
    Escaneia todas as subpastas que contêm encoder.py
    
    Returns:
        Dicionário {plugin_name: EncoderClass}
    """
    encoders = {}
    
    current_dir = Path(__file__).parent
    
    # Itera sobre todas as subpastas
    for item in current_dir.iterdir():
        # Ignora arquivos, pastas especiais e a base
        if not item.is_dir():
            continue
        if item.name.startswith('_') or item.name.startswith('.'):
            continue
        if item.name == '__pycache__':
            continue
        
        encoder_file = item / "encoder.py"
        if encoder_file.exists():
            try:
                # Importa dinamicamente o módulo
                module_name = f"encoders.{item.name}.encoder"
                module = importlib.import_module(module_name)
                
                # Procura por classes que herdam de BaseEncoder
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseEncoder) and 
                        obj != BaseEncoder):
                        
                        # Instancia temporariamente para verificar disponibilidade
                        try:
                            encoder_instance = obj()
                            
                            # Verifica se o encoder está disponível (ex: dependências)
                            if hasattr(encoder_instance, 'available') and not encoder_instance.available:
                                print(f"⚠️ Plugin '{item.name}' não disponível (dependências faltando)")
                                continue
                            
                            encoders[item.name] = obj
                            EncoderRegistry.register(obj)
                            print(f"✅ Plugin carregado: {item.name} -> {encoder_instance.display_name}")
                            
                        except Exception as e:
                            print(f"⚠️ Erro ao instanciar {item.name}: {e}")
                            
            except Exception as e:
                print(f"❌ Erro ao carregar plugin '{item.name}': {e}")
                import traceback
                traceback.print_exc()
    
    return encoders


def get_encoder_instance(encoder_name: str) -> BaseEncoder:
    """
    Retorna uma instância do encoder solicitado
    
    Args:
        encoder_name: Nome do encoder (nome da pasta)
        
    Returns:
        Instância do encoder
    """
    encoders = discover_encoders()
    if encoder_name in encoders:
        return encoders[encoder_name]()
    raise ValueError(f"Encoder '{encoder_name}' não encontrado. Disponíveis: {list(encoders.keys())}")


def list_available_encoders() -> List[Dict[str, str]]:
    """
    Lista todos os encoders disponíveis com suas informações
    
    Returns:
        Lista de dicionários com informações de cada encoder
    """
    encoders = discover_encoders()
    result = []
    
    for name, encoder_class in encoders.items():
        try:
            encoder = encoder_class()
            result.append({
                'id': name,
                'name': encoder.name,
                'display_name': encoder.display_name,
                'description': encoder.description,
                'icon': encoder.icon,
                'extension': encoder.output_extension,
                'mime_type': encoder.mime_type,
                'signature': encoder.signature.decode('ascii', errors='ignore') if encoder.signature else None,
            })
        except Exception as e:
            print(f"⚠️ Erro ao obter info de {name}: {e}")
    
    return result


def identify_video_format(video_data: bytes) -> Optional[BaseEncoder]:
    """
    Identifica o formato de um vídeo e retorna o encoder apropriado
    
    Args:
        video_data: Bytes do vídeo
        
    Returns:
        Instância do encoder identificado ou None
    """
    # Garante que os encoders estão descobertos
    discover_encoders()
    
    # Tenta identificar pelo registro
    encoder = EncoderRegistry.identify(video_data)
    return encoder


def get_decoder_for_video(video_data: bytes) -> Optional[callable]:
    """
    Retorna a função de decode apropriada para um vídeo
    
    Args:
        video_data: Bytes do vídeo
        
    Returns:
        Função de decode ou None
    """
    encoder = identify_video_format(video_data)
    if encoder:
        return encoder.decode
    return None


def decode_video_auto(video_data: bytes) -> Optional[bytes]:
    """
    Decodifica um vídeo automaticamente, identificando o formato
    
    Args:
        video_data: Bytes do vídeo
        
    Returns:
        Dados decodificados ou None
    """
    encoder = identify_video_format(video_data)
    if encoder:
        return encoder.decode(video_data)
    
    # Fallback: tenta todos os encoders
    encoders = discover_encoders()
    for name, encoder_class in encoders.items():
        try:
            encoder = encoder_class()
            if encoder.can_decode(video_data):
                print(f"🔄 Fallback: usando {encoder.display_name}")
                return encoder.decode(video_data)
        except:
            continue
    
    return None


# ============================================
# DECODERS DINÂMICOS
# Obtidos automaticamente dos encoders
# ============================================

def get_all_decoders() -> Dict[str, callable]:
    """
    Retorna um dicionário com todas as funções de decode disponíveis
    
    Returns:
        {encoder_name: decode_function}
    """
    decoders = {}
    encoders = discover_encoders()
    
    for name, encoder_class in encoders.items():
        try:
            encoder = encoder_class()
            decoders[name] = encoder.decode
        except:
            pass
    
    return decoders


# Para compatibilidade - importa decoders específicos se existirem
# Mas de forma genérica, sem hardcoding
_encoder_modules = {}

def _load_decoder_module(encoder_name: str):
    """Carrega dinamicamente o módulo decoder de um encoder"""
    if encoder_name in _encoder_modules:
        return _encoder_modules[encoder_name]
    
    try:
        module = importlib.import_module(f"encoders.{encoder_name}.decoder")
        _encoder_modules[encoder_name] = module
        return module
    except ImportError:
        return None


def __getattr__(name: str):
    """
    Permite acesso dinâmico a decoders específicos
    Ex: encoders.decode_rgb_squares
    """
    if name.startswith('decode_'):
        # Extrai o nome do encoder do nome da função
        # Ex: decode_rgb_squares -> rgb_squares
        encoder_name = name[7:]  # Remove 'decode_'
        
        module = _load_decoder_module(encoder_name)
        if module and hasattr(module, name):
            return getattr(module, name)
    
    raise AttributeError(f"module 'encoders' has no attribute '{name}'")


__all__ = [
    'discover_encoders',
    'get_encoder_instance',
    'list_available_encoders',
    'identify_video_format',
    'get_decoder_for_video',
    'decode_video_auto',
    'get_all_decoders',
    'BaseEncoder',
    'EncoderRegistry',
]