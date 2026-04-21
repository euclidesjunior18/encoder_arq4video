"""Plugin RGB FAST"""

from .encoder import RGBFastEncoder
from .decoder import decode_rgb_fast, decode_fast_with_signature_check

__all__ = [
    'RGBFastEncoder',
    'decode_rgb_fast',
    'decode_fast_with_signature_check'
]