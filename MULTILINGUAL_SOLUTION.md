# Çok Dilli Özet Sistemi - Çözüm Analizi

## 🎯 İhtiyaç

Farklı dillerde özet alabilmek:
- Türkçe PDF → İngilizce özet
- Türkçe PDF → Almanca özet  
- İngilizce PDF → Türkçe özet
- İngilizce PDF → İtalyanca özet
- vb.

---

## 🔍 Çözüm Seçenekleri

### **Seçenek 1: mBART-50 (Facebook)** ⭐ **ÖNERİLEN**

#### Özellikler
- **50 dil desteği**: tr, en, de, fr, es, it, ru, ar, ja, ko, zh, vb.
- **Tek model**: Hem çeviri hem özetleme
- **Hızlı**: Tek geçişte özet üretir
- **GPU gereksinimi**: ~8-10GB VRAM

#### Desteklenen Diller (örnekler)
```python
SUPPORTED_LANGUAGES = {
    'en': 'en_XX',  # İngilizce
    'tr': 'tr_TR',  # Türkçe
    'de': 'de_DE',  # Almanca
    'fr': 'fr_XX',  # Fransızca
    'es': 'es_XX',  # İspanyolca
    'it': 'it_IT',  # İtalyanca
    'ru': 'ru_RU',  # Rusça
    'ar': 'ar_AR',  # Arapça
    'ja': 'ja_XX',  # Japonca
    'ko': 'ko_KR',  # Korece
    'zh': 'zh_CN',  # Çince (Basitleştirilmiş)
    'nl': 'nl_XX',  # Hollandaca
    'pt': 'pt_XX',  # Portekizce
    'hi': 'hi_IN',  # Hintçe
    # ... 50+ dil
}
```

#### Avantajlar
✅ Tek model, kolay entegrasyon  
✅ Yüksek kalite  
✅ Cross-lingual: Türkçe'den İngilizce'ye direkt özet  
✅ Fine-tuned for summarization  

#### Dezavantajlar
❌ Büyük model boyutu (~2.4GB)  
❌ Yavaş (BART'tan ~2x yavaş)  
❌ Daha fazla GPU bellek gerektirir  

#### Kurulum
```bash
pip install transformers sentencepiece
```

#### Kullanım
```python
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")

# Türkçe'den İngilizce özet
tokenizer.src_lang = "tr_TR"
encoded = tokenizer(turkish_text, return_tensors="pt")
generated = model.generate(**encoded, forced_bos_token_id=tokenizer.lang_code_to_id["en_XX"])
summary = tokenizer.decode(generated[0], skip_special_tokens=True)
```

---

### **Seçenek 2: mT5 (Google)** 🔥 **EN İYİ KALİTE**

#### Özellikler
- **101 dil desteği**: mBART'tan daha fazla
- **State-of-the-art kalite**
- **GPU gereksinimi**: ~12-16GB VRAM (large model)

#### Modeller
```python
# Model seçenekleri (boyut/kalite dengesi)
"google/mt5-small"   # ~1.2GB, hızlı, orta kalite
"google/mt5-base"    # ~2.3GB, dengeli
"google/mt5-large"   # ~4.8GB, yüksek kalite ⭐
"google/mt5-xl"      # ~14GB, en iyi kalite (ağır)
```

#### Avantajlar
✅ En geniş dil desteği (101 dil)  
✅ En iyi özet kalitesi  
✅ Aktif geliştirme (Google)  

#### Dezavantajlar
❌ Daha büyük model  
❌ Daha yavaş  
❌ Daha fazla GPU bellek  
❌ Fine-tuning gerekebilir  

---

### **Seçenek 3: İki Aşamalı (Çeviri + BART)** 💰 **BUDGET-FRIENDLY**

#### Yaklaşım
1. **Adım 1**: Helsinki-NLP ile dil çevirisi (örn: tr→en)
2. **Adım 2**: BART ile özetleme (en→en)
3. **Adım 3** (opsiyonel): Hedef dile çeviri (en→de)

#### Örnek Akış
```
Türkçe PDF → [Helsinki tr→en] → İngilizce metin → [BART] → 
→ İngilizce özet → [Helsinki en→de] → Almanca özet
```

#### Avantajlar
✅ Mevcut BART modelini kullanır  
✅ Daha az GPU bellek  
✅ Modüler (her aşama ayrı optimizelenir)  

#### Dezavantajlar
❌ 2-3 aşama = çok yavaş  
❌ Çeviri hatası özete de yansır  
❌ Kalite kaybı (her aşamada)  
❌ Karmaşık pipeline  

#### Gerekli Modeller
```python
# Çeviri modelleri (Helsinki-NLP)
"Helsinki-NLP/opus-mt-tr-en"  # Türkçe → İngilizce
"Helsinki-NLP/opus-mt-en-tr"  # İngilizce → Türkçe
"Helsinki-NLP/opus-mt-en-de"  # İngilizce → Almanca
"Helsinki-NLP/opus-mt-de-en"  # Almanca → İngilizce
# ... (her dil çifti için ayrı model)
```

---

### **Seçenek 4: API Tabanlı (DeepL/Google)** 🌐 **EN KOLAY**

#### Yaklaşım
1. API ile dil çevirisi
2. BART ile özetleme
3. API ile hedef dile çeviri

#### Servisler

**DeepL API** (önerilen)
- Çok yüksek kalite çeviri
- 30+ dil
- Ücretsiz: 500,000 karakter/ay
- Ücretli: $5.49/milyon karakter

**Google Cloud Translation API**
- 100+ dil
- Ücretsiz: İlk 500,000 karakter/ay
- Ücretli: $20/milyon karakter

#### Avantajlar
✅ En kolay implementasyon  
✅ GPU gerekmez (çeviri için)  
✅ Yüksek kalite çeviri  
✅ Birçok dil desteği  

#### Dezavantajlar
❌ İnternet bağlantısı gerekli  
❌ Ücretli (belirli limitten sonra)  
❌ Dışa bağımlılık  
❌ Veri gizliliği (API'ye gönderiliyor)  

---

## 🏆 Karşılaştırma Tablosu

| Özellik | mBART-50 | mT5 | İki Aşama | API |
|---------|----------|-----|-----------|-----|
| **Dil Sayısı** | 50 | 101 | Değişken | 100+ |
| **Kalite** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Hız** | Orta | Yavaş | Çok Yavaş | Hızlı |
| **GPU Bellek** | 8-10GB | 12-16GB | 6-8GB | 6GB (sadece BART) |
| **Kolay Kurulum** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Maliyet** | Ücretsiz | Ücretsiz | Ücretsiz | Ücretli (limit sonrası) |
| **Offline** | ✅ | ✅ | ✅ | ❌ |

---

## 💡 ÖNERİ: Hibrit Yaklaşım

### Yapı
```
Gelen PDF
    ↓
Dil Algıla (langdetect)
    ↓
┌─────────────────────┐
│ PDF İngilizce mi?   │
└─────────────────────┘
    ↓           ↓
   Evet        Hayır
    ↓           ↓
    │      mBART/API Çeviri → İngilizce
    ↓           ↓
    └─────┬─────┘
          ↓
    BART Özetleme (İngilizce özet)
          ↓
┌─────────────────────────┐
│ Özet hedef dilde mi?    │
└─────────────────────────┘
    ↓           ↓
   Evet        Hayır
    ↓           ↓
   Bitir   mBART/API Çeviri → Hedef dil
    ↓           ↓
    └─────┬─────┘
          ↓
      Özet Döndür
```

### Avantajlar
✅ BART hızını korur (özet için)  
✅ Sadece gerekirse çeviri yapar  
✅ Yüksek kalite  
✅ Esnek (mBART veya API seçebilir)  

---

## 🎯 ÖNERİLEN ÇÖZÜM

### **1. ÖNCE: mBART-50 ile Başla** (Prototype)

**Artıları:**
- Hızlı başlangıç
- Tek model
- 50 dil yeterli

**Kodu:**
```python
# ai_service.py'ye ekle
def summarize_multilingual(
    text: str,
    source_lang: str,  # 'tr', 'en', 'de', ...
    target_lang: str,   # 'en', 'tr', 'it', ...
    length_mode: str
):
    from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
    
    model = MBartForConditionalGeneration.from_pretrained(
        "facebook/mbart-large-50-many-to-many-mmt"
    )
    tokenizer = MBart50TokenizerFast.from_pretrained(
        "facebook/mbart-large-50-many-to-many-mmt"
    )
    
    # Kaynak dil ayarla
    tokenizer.src_lang = LANG_CODES[source_lang]
    
    # Encode
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    
    # Özet üret (hedef dilde)
    generated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.lang_code_to_id[LANG_CODES[target_lang]],
        max_length=calculate_max_length(length_mode),
        min_length=calculate_min_length(length_mode),
        num_beams=4
    )
    
    summary = tokenizer.decode(generated[0], skip_special_tokens=True)
    return summary
```

### **2. DAHA SONRA: API Opsiyonu Ekle** (Production)

Kullanıcılara seçim hakkı tanı:
```python
TRANSLATION_METHOD = os.getenv("TRANSLATION_METHOD", "mbart")  # mbart | deepl | google
```

---

## 📋 Implementasyon Adımları

### Adım 1: Dil Algılama Ekle
```bash
pip install langdetect
```

### Adım 2: mBART Kur
```bash
pip install transformers sentencepiece sacremoses
```

### Adım 3: Kodu Güncelle
1. `ai_service.py` - multilingual_summarize() fonksiyonu
2. `ozet_service.py` - source_lang ve target_lang parametreleri
3. `ozet_router.py` - API endpoint güncellemesi
4. Frontend - dil seçici dropdown

### Adım 4: Test
```python
# Türkçe → İngilizce
summary = summarize_multilingual(
    text="Yapay zeka geleceğin teknolojisidir...",
    source_lang="tr",
    target_lang="en",
    length_mode="short"
)
```

---

## 💾 Disk ve Bellek Gereksinimleri

### Sadece BART (Mevcut)
- Model: ~1.6GB
- Runtime GPU: ~6GB VRAM
- Disk: ~3GB

### mBART-50 Eklenmesi
- Model: ~2.4GB
- Runtime GPU: ~10GB VRAM
- Disk: ~5.5GB (+2.5GB)

### Her İkisi Birden (Tavsiye)
- Toplam Disk: ~5.5GB
- Toplam GPU: 10GB VRAM (ikisi aynı anda yüklü değilse)

---

## 🚀 İlk Adım: Ne Yapalım?

Size **3 seçenek** sunuyorum:

### A) **HIZLI**: mBART-50 Entegrasyonu
- 2-3 saat implementasyon
- 50 dil desteği
- Hemen kullanıma hazır

### B) **KALİTELİ**: mT5 Entegrasyonu  
- 3-4 saat implementasyon
- 101 dil desteği
- En yüksek kalite
- Daha fazla GPU gerekir

### C) **KOLAY**: DeepL/Google API
- 1-2 saat implementasyon
- 100+ dil
- API key gerekli
- İnternet bağlantısı şart

**Hangi yaklaşımı tercih edersiniz?**
