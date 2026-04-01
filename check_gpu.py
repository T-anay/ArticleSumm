#!/usr/bin/env python3
"""
GPU Kontrol Script
RTX 4060 ve diğer NVIDIA GPU'ların çalışıp çalışmadığını kontrol eder.
"""

import sys

def check_pytorch():
    """PyTorch kurulumunu ve GPU desteğini kontrol et"""
    try:
        import torch
        print("=" * 60)
        print("🔍 PyTorch Kontrol")
        print("=" * 60)
        print(f"✓ PyTorch Version: {torch.__version__}")
        print(f"✓ CUDA Available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA Version: {torch.version.cuda}")
            print(f"✓ GPU Count: {torch.cuda.device_count()}")
            print()
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  - Total Memory: {props.total_memory / 1e9:.2f} GB")
                print(f"  - Compute Capability: {props.major}.{props.minor}")
                print(f"  - Multi Processor Count: {props.multi_processor_count}")
            
            # GPU test
            print()
            print("🧪 GPU Test (Torch Tensor)...")
            x = torch.rand(1000, 1000).cuda()
            y = torch.rand(1000, 1000).cuda()
            z = torch.matmul(x, y)
            print(f"✓ GPU tensor operation successful!")
            print(f"  Result shape: {z.shape}")
            
        else:
            print("⚠️  GPU not detected, will use CPU")
            print("   Possible reasons:")
            print("   - NVIDIA driver not installed")
            print("   - CUDA toolkit not installed")
            print("   - PyTorch CPU-only version installed")
        
        return torch.cuda.is_available()
        
    except ImportError as e:
        print(f"❌ PyTorch not installed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_transformers():
    """Transformers kütüphanesini kontrol et"""
    try:
        import transformers
        print()
        print("=" * 60)
        print("🔍 Transformers Kontrol")
        print("=" * 60)
        print(f"✓ Transformers Version: {transformers.__version__}")
        return True
    except ImportError:
        print("❌ Transformers not installed")
        return False


def check_sentence_transformers():
    """Sentence Transformers kütüphanesini kontrol et"""
    try:
        import sentence_transformers
        print()
        print("=" * 60)
        print("🔍 Sentence Transformers Kontrol")
        print("=" * 60)
        print(f"✓ Sentence Transformers Version: {sentence_transformers.__version__}")
        return True
    except ImportError:
        print("❌ Sentence Transformers not installed")
        return False


def main():
    """Ana kontrol fonksiyonu"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "AI Model GPU Kontrolü" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = {
        'pytorch': check_pytorch(),
        'transformers': check_transformers(),
        'sentence_transformers': check_sentence_transformers(),
    }
    
    print()
    print("=" * 60)
    print("📊 Özet")
    print("=" * 60)
    
    all_ok = all(results.values())
    
    if results['pytorch']:
        import torch
        if torch.cuda.is_available():
            print("✓ GPU DESTEĞİ AKTİF - Özetleme hızlı çalışacak!")
            print("  .env dosyasında USE_GPU=true ayarlayın")
        else:
            print("⚠️  CPU MODU - Özetleme yavaş çalışacak")
            print("  GPU için NVIDIA driver ve CUDA toolkit kurun")
    else:
        print("❌ PyTorch kurulmamış, pip install torch yapın")
    
    if results['transformers']:
        print("✓ Transformers modeli kullanılabilir")
    else:
        print("❌ Transformers kurulmamış, pip install transformers yapın")
    
    if results['sentence_transformers']:
        print("✓ Sentence transformers kullanılabilir")
    else:
        print("❌ Sentence transformers kurulmamış")
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("🎉 Tüm kontroller başarılı! Uygulamayı başlatabilirsiniz.")
        print()
        print("Başlatmak için:")
        print("  uvicorn app.main:app --reload")
    else:
        print("⚠️  Bazı paketler eksik. Kurulum yapın:")
        print("  pip install -r requirements-gpu.txt")
    
    print("=" * 60)
    print()
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
