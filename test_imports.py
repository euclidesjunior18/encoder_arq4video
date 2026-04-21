"""Teste de importação dos módulos"""

import sys
from pathlib import Path

# Adiciona o diretório atual ao path
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

print(f"ROOT_DIR: {ROOT_DIR}")
print(f"sys.path: {sys.path[:3]}")

# Testar importações
try:
    print("\n1. Testando import encoders...")
    import encoders
    print("   ✅ encoders importado")
    print(f"   Diretório: {encoders.__file__}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

try:
    print("\n2. Testando discover_encoders...")
    from encoders import discover_encoders
    print("   ✅ discover_encoders importado")
    
    plugins = discover_encoders()
    print(f"   Plugins encontrados: {list(plugins.keys())}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Testando utils...")
    from utils import video_utils
    print("   ✅ utils.video_utils importado")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n✅ Teste concluído!")