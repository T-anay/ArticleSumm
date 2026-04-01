# ArticleSumm
Yapay zeka destekli akıllı makale özetleme platformu. Python, PostgreSQL ve Docker kullanılarak geliştirilen 3 katmanlı bir web uygulamasıdır.

## 🚀 AI Model Özellikleri

### GPU Desteği (ÖNERİLEN)
RTX 4060, 3060, 4070 gibi NVIDIA GPU'lar desteklenir.

#### GPU Kurulumu (Daha Hızlı):
```bash
# 1. GPU sürümü PyTorch ile kurun
pip install -r requirements-gpu.txt

# 2. .env dosyası oluşturun
cp .env.example .env

# 3. .env dosyasında GPU'yu aktif edin
USE_GPU=true
```

#### CPU Kurulumu (Daha Yavaş):
```bash
# 1. Normal requirements
pip install -r requirements.txt

# 2. .env dosyasında CPU kullanımı
USE_GPU=false
```

### Model Seçenekleri

`.env` dosyasında model değiştirebilirsiniz:

```bash
# Hızlı model (769MB, İngilizce)
SUMMARY_MODEL=sshleifer/distilbart-cnn-12-6

# Varsayılan (1.6GB, İngilizce)
SUMMARY_MODEL=facebook/bart-large-cnn

# Türkçe desteği (2.4GB, çok dilli)
SUMMARY_MODEL=facebook/mbart-large-50
```

### Harici Model API ile Çalıştırma

Projeyi yerel transformer yerine harici bir model API ile çalıştırabilirsiniz.

`.env` örneği:

```bash
AI_PROVIDER=external
EXTERNAL_LLM_BASE_URL=https://api.openai.com/v1
EXTERNAL_LLM_ENDPOINT=/chat/completions
EXTERNAL_LLM_MODEL=gpt-4o-mini
EXTERNAL_LLM_API_KEY=your_api_key
```

Notlar:

- `AI_PROVIDER=external` iken özetleme OpenAI-compatible endpoint'e gönderilir.
- Harici API hata verirse sistem otomatik olarak yerel modele fallback yapar.
- `AI_PROVIDER=local` varsayılandır ve mevcut lokal model akışı ile çalışır.

### Performans Beklentileri

| Metin Uzunluğu | CPU (32GB RAM) | GPU (RTX 4060) |
|----------------|----------------|----------------|
| 1000 kelime    | ~30 saniye     | ~5 saniye      |
| 5000 kelime    | ~2 dakika      | ~15 saniye     |
| 10000 kelime   | ~5 dakika      | ~30 saniye     |

### ChromaDB (Opsiyonel)

Embedding-based chunk selection için ChromaDB kullanabilirsiniz:

```bash
# .env dosyasında
USE_CHROMA=true
CHROMA_TENANT=your-tenant
CHROMA_DATABASE=your-database
```

**Not:** ChromaDB olmadan da çalışır (direkt özetleme).
