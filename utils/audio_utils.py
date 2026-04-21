"""Utilitários para geração de áudio a partir de dados binários"""

import numpy as np
from typing import Optional


def generate_audio_from_data(data: bytes, sample_rate: int = 44100, 
                            max_duration: float = 10.0) -> np.ndarray:
    """
    Converte dados binários em áudio modulado (estéreo)
    
    Args:
        data: Dados binários
        sample_rate: Taxa de amostragem (Hz)
        max_duration: Duração máxima do áudio (segundos)
    
    Returns:
        Array numpy com áudio estéreo (shape: [n_samples, 2])
    """
    max_samples = int(sample_rate * max_duration)
    data = data[:min(len(data), max_samples)]
    
    if len(data) == 0:
        return np.zeros((1, 2), dtype=np.float32)
    
    samples = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
    samples = (samples / 128.0) - 1.0
    envelope = np.hanning(len(samples))
    samples = samples * envelope
    audio = np.column_stack([samples, samples])
    
    return audio


def save_audio_wav(audio_data: np.ndarray, output_path: str, sample_rate: int = 44100):
    """Salva áudio em formato WAV"""
    try:
        import scipy.io.wavfile as wav
        wav.write(output_path, sample_rate, audio_data)
        return True
    except ImportError:
        print("⚠️ scipy não instalado. Áudio não será salvo.")
        return False