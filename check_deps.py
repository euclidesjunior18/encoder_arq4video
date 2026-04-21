import sys

deps = {
    'flet': 'Interface gráfica',
    'cv2': 'OpenCV (processamento de vídeo)',
    'numpy': 'NumPy (arrays)',
    'scipy': 'SciPy (áudio)',
    'qrcode': 'QR Code',
    'PIL': 'Pillow (imagens)'
}

print("🔍 Verificando dependências...\n")

missing = []
for module, desc in deps.items():
    try:
        __import__(module)
        print(f"✅ {module:10} - {desc}")
    except ImportError:
        print(f"❌ {module:10} - {desc} (NÃO INSTALADO)")
        missing.append(module)

if missing:
    print(f"\n📦 Execute: pip install {' '.join(missing)}")
else:
    print("\n✨ Todas as dependências instaladas! Pode executar o app.")