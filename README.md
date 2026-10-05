# ArticleSumm

> AI-powered article summarization platform — Graduation thesis project
> Yapay zeka destekli makale özetleme platformu — Bitirme ödevi projesi

---

## 🇬🇧 English

ArticleSumm is a 3-tier web application that uses transformer-based language models to automatically summarize long-form articles. Users can paste or upload article text and receive concise, high-quality summaries in seconds. The system supports multiple summarization models and can be configured to run on both CPU and GPU.

### Features

- **Automatic Summarization** — Extracts key information from long articles using NLP models (BART, DistilBART, mBART)
- **Multilingual Support** — Supports Turkish and other languages via multilingual models
- **GPU Acceleration** — Optional NVIDIA GPU support for significantly faster inference
- **Configurable Models** — Switch between lightweight (769MB) and high-quality (2.4GB) models via environment variables
- **External API Mode** — Offload inference to an external AI provider instead of running models locally
- **Dockerized** — Fully containerized with Docker and Docker Compose for easy deployment
- **Nginx Reverse Proxy** — Production-ready setup with Nginx

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, Flask |
| **Frontend** | HTML / CSS / JavaScript |
| **AI Models** | HuggingFace Transformers (BART, DistilBART, mBART) |
| **Database** | PostgreSQL |
| **Containerization** | Docker, Docker Compose |
| **Proxy** | Nginx |
| **Embeddings** | sentence-transformers (ChromaDB optional) |

### Project Structure

```
ArticleSumm/
├── app/                    # Python backend application
├── Frontend/               # Web UI
├── nginx/                  # Nginx configuration
├── Dockerfile
├── docker-compose.yml
├── requirements.txt        # CPU dependencies
├── requirements-gpu.txt    # GPU dependencies
└── .env.example            # Environment variable template
```

### Getting Started

**Prerequisites:** Python 3.10+, Docker & Docker Compose, (Optional) NVIDIA GPU

**1. Clone the repository**
```bash
git clone https://github.com/T-anay/ArticleSumm.git
cd ArticleSumm
```

**2. Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env`:
```env
USE_GPU=false                            # true for NVIDIA GPU acceleration
SUMMARY_MODEL=facebook/bart-large-cnn   # AI model to use
AI_PROVIDER=local                        # 'local' or 'ext' for external API
```

**3. Run with Docker Compose**
```bash
docker-compose up --build
```
The application will be available at `http://localhost`.

**4. Run locally (without Docker)**
```bash
# CPU
pip install -r requirements.txt

# GPU (NVIDIA)
pip install -r requirements-gpu.txt

python app/main.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_GPU` | `false` | Enable NVIDIA GPU acceleration |
| `SUMMARY_MODEL` | `facebook/bart-large-cnn` | HuggingFace model for summarization |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `USE_CHROMA` | `false` | Enable ChromaDB for chunk selection |
| `AI_PROVIDER` | `local` | `local` = Docker, `ext` = external API |

### Available Models

| Model | Size | Language |
|-------|------|----------|
| `sshleifer/distilbart-cnn-12-6` | 769 MB | English (fast) |
| `facebook/bart-large-cnn` | 1.6 GB | English (default) |
| `facebook/mbart-large-50` | 2.4 GB | Multilingual + Turkish |

### How It Works

1. User submits an article through the web interface
2. The backend pre-processes and chunks the text
3. The selected transformer model generates a summary for each chunk
4. (Optional) ChromaDB selects the most relevant chunks before summarization
5. The consolidated summary is returned to the user

---

## 🇹🇷 Türkçe

ArticleSumm, transformer tabanlı dil modellerini kullanarak uzun makaleleri otomatik olarak özetleyen 3 katmanlı bir web uygulamasıdır. Kullanıcılar makale metnini yapıştırarak veya yükleyerek saniyeler içinde kısa ve kaliteli özetler alabilir. Sistem birden fazla özetleme modelini destekler ve hem CPU hem de GPU ile çalışacak şekilde yapılandırılabilir.

### Özellikler

- **Otomatik Özetleme** — NLP modelleri (BART, DistilBART, mBART) kullanarak uzun makalelerden kilit bilgileri çıkarır
- **Çok Dilli Destek** — Çok dilli modeller sayesinde Türkçe ve diğer dilleri destekler
- **GPU Hızlandırması** — Çok daha hızlı çıkarım için isteğe bağlı NVIDIA GPU desteği
- **Yapılandırılabilir Modeller** — Ortam değişkenleri ile hafif (769MB) ve yüksek kaliteli (2.4GB) modeller arasında geçiş
- **Harici API Modu** — Modelleri yerel olarak çalıştırmak yerine harici bir AI sağlayıcısına yük aktarımı
- **Docker Desteği** — Docker ve Docker Compose ile tam konteynerleştirilmiş kolay kurulum
- **Nginx Ters Proxy** — Nginx ile production'a hazır yapı

### Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | Python, Flask |
| **Frontend** | HTML / CSS / JavaScript |
| **Yapay Zeka Modelleri** | HuggingFace Transformers (BART, DistilBART, mBART) |
| **Veritabanı** | PostgreSQL |
| **Konteynerleştirme** | Docker, Docker Compose |
| **Proxy** | Nginx |
| **Gömülemeler** | sentence-transformers (ChromaDB opsiyonel) |

### Başlarken

**Gereksinimler:** Python 3.10+, Docker & Docker Compose, (İsteğe bağlı) NVIDIA GPU

**1. Repoyu klonlayın**
```bash
git clone https://github.com/T-anay/ArticleSumm.git
cd ArticleSumm
```

**2. Ortam değişkenlerini yapılandırın**
```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:
```env
USE_GPU=false                            # NVIDIA GPU için true yapın
SUMMARY_MODEL=facebook/bart-large-cnn   # Kullanılacak AI modeli
AI_PROVIDER=local                        # 'local' veya harici API için 'ext'
```

**3. Docker Compose ile çalıştırın**
```bash
docker-compose up --build
```
Uygulama `http://localhost` adresinde çalışır.

**4. Docker olmadan yerel çalıştırma**
```bash
# CPU
pip install -r requirements.txt

# GPU (NVIDIA)
pip install -r requirements-gpu.txt

python app/main.py
```

### Nasıl Çalışır?

1. Kullanıcı web arayüzü üzerinden makale gönderir
2. Backend metni önceden işler ve parçalara ayırır
3. Seçilen transformer modeli her parça için özet oluşturur
4. (İsteğe bağlı) ChromaDB, özetlemeden önce en ilgili parçaları seçer
5. Birleştirilmiş özet kullanıcıya döndürülür
