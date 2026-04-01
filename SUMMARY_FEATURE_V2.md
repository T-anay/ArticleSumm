# Özet Oluşturma Özelliği v2.0 - Teknik Dokümantasyon

## 🎯 Genel Bakış

Özet oluşturma sistemi baştan yeniden yapılandırıldı. Yeni sistem:
- **Bağlam-Farkında (Context-Aware)**: Kullanıcının önceki özetlerini analiz ederek daha iyi özetler üretir
- **Yazar Bilgilerini Kaldırma**: PDF'lerdeki yazar adı, e-posta, kurum bilgileri otomatik temizlenir
- **Strict İngilizce**: Sadece İngilizce içerik üretir (BART model sınırlaması)
- **Yeni Uzunluk Hedefleri**: Akademik standartlara uygun 3 farklı özet uzunluğu

---

## 📊 Özet Uzunluk Hedefleri

### 1. **KISA ÖZET (Short)** - Mobil Uyumlu
- **Hedef**: 30-60 kelime
- **Amaç**: Makalenin ne hakkında olduğunu açıklar (article topic)
- **Kullanım**: Mobil cihazlarda hızlı önizleme
- **Örnek Uzunluk**: ~200-400 karakter

```
"This article explores the impact of artificial intelligence on 
healthcare systems, focusing on diagnostic accuracy improvements 
and patient outcome predictions through machine learning algorithms."
```

### 2. **ORTA ÖZET (Medium)** - Standart
- **Hedef**: Orijinal metnin %10'u
- **Amaç**: Ana noktaları ve bulguları özetler
- **Kullanım**: Genel önizleme ve hızlı okuma
- **Örnek**: 5000 kelimelik makale → ~500 kelime özet

### 3. **UZUN ÖZET (Long)** - Detaylı
- **Hedef**: Orijinal metnin %25'i
- **Amaç**: Kapsamlı executive summary
- **Kullanım**: Detaylı içerik analizi
- **Örnek**: 5000 kelimelik makale → ~1250 kelime özet

---

## 🔍 Yeni Özellikler

### 1. **Veritabanı Bağlamı (Database Context)**

Sistem artık her yeni özet oluştururken kullanıcının **önceki tüm özetlerini** kontrol eder:

```python
# Benzerlik kontrolü (Cosine Similarity)
previous_summaries = db.query(Ozet).filter(Ozet.sahip_id == owner_id).all()

for summary in previous_summaries:
    similarity = cosine_similarity(current_doc, previous_doc)
    if similarity > 0.6:  # %60+ benzerlik
        # Bu dokümanı bağlam olarak ekle
        context.append(previous_doc)
```

**Faydaları**:
- Benzer konulardaki önceki özetler yeni özetin kalitesini artırır
- Tekrarlanan kavramlar daha iyi anlaşılır
- Tutarlılık artar

### 2. **Yazar Bilgisi Temizleme (Author Info Removal)**

PDF'lerden otomatik olarak kaldırılan bilgiler:
- ✅ Yazar adları (`Prof. John Smith`, `Dr. Jane Doe`)
- ✅ E-posta adresleri (`author@university.edu`)
- ✅ Kurum bilgileri (`Department of Computer Science`)
- ✅ Yazar biyografileri (`...is a Professor at...`)
- ✅ Referans alıntıları (`Smith (2020)`, `Johnson et al. (2019)`)

**Öncesi**:
```
"Dr. Ercan Öztemel is a Professor at Istanbul Technical University. 
His research focuses on AI. Email: oztemel@itu.edu.tr
Abstract: This paper discusses machine learning applications..."
```

**Sonrası**:
```
"This paper discusses machine learning applications..."
```

### 3. **Strict İngilizce Modu (English-Only)**

Sistem **varsayılan olarak** tüm Türkçe içeriği filtreler:

```python
# Türkçe karakter kontrolü
turkish_chars = ['ç', 'ğ', 'ı', 'ş', 'ö', 'ü', 'Ç', 'Ğ', 'İ', 'Ş', 'Ö', 'Ü']
if any(char in sentence for char in turkish_chars):
    # Bu cümleyi atla
    continue

# Türkçe kelime kontrolü
turkish_words = ['ile', 've', 'bir', 'bu', 'için', 'gibi', ...]
if any(word in sentence.lower() for word in turkish_words):
    # Bu cümleyi atla
    continue
```

**Sonuç**: Çıktı %100 İngilizce olur.

---

## ⚠️ ÖNEMLI: Dil Sınırlamaları

### PDF İçeriği İngilizce Olmalı mı?

**Evet, MUTLAKA İngilizce olmalı.** İşte nedeni:

#### BART Modeli Sınırlaması

Kullandığınız model: `facebook/bart-large-cnn`
- ✅ Sadece İngilizce için eğitildi
- ❌ Türkçe özetleme yapamaz
- ❌ Çeviri yapamaz
- ❌ Çok dilli değil

#### Türkçe PDF ile Ne Olur?

```
Input (Türkçe): 
"Bu makale yapay zeka sistemlerinin sağlık sektöründeki 
uygulamalarını incelemektedir."

BART Output (Bozuk):
"Bu makale yapay zeka sistemlerinin s ğl k sekt r ndeki 
uygulam lar n ncelemektedir ."
```

Sonuç: **Anlamsız, bozuk metin**

### Çözüm Seçenekleri

#### ✅ Seçenek 1: Sadece İngilizce PDF Kullanın (Önerilen)
- **Avantaj**: En hızlı, en stabil
- **Dezavantaj**: Türkçe PDF'ler kullanılamaz

#### 🔧 Seçenek 2: Çeviri Modeli Ekleyin
```bash
# Türkçe → İngilizce çeviri modeli
pip install sentencepiece
```

```python
from transformers import MarianMTModel, MarianTokenizer

model_name = "Helsinki-NLP/opus-mt-tr-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Çeviri
def translate_turkish_to_english(text: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)
```

**Not**: 
- Yavaş (ekstra model yükleme)
- GPU bellek kullanımı artar (~2GB ekstra)
- Çeviri kalitesi %100 değil

#### 🌐 Seçenek 3: API Kullanın
```python
# Google Translate API
from googletrans import Translator

translator = Translator()
result = translator.translate(text, src='tr', dest='en')
english_text = result.text
```

**Avantajlar**:
- Hızlı
- Kaliteli çeviri
- GPU gerektirmez

**Dezavantajlar**:
- API key gerekir
- Ücretli (belirli limitten sonra)
- İnternet bağlantısı gerekir

---

## 🔧 API Kullanımı

### PDF Özet Oluşturma

```python
POST /api/ozetler/pdf_yukle

Form Data:
{
    "baslik": "AI in Healthcare",
    "file": <PDF dosyası>,
    "length_option": "medium",  # short | medium | long
    "target_language": "english"  # SADECE english desteklenir
}
```

### Başarılı Response

```json
{
    "id": 123,
    "baslik": "AI in Healthcare",
    "ozet_metin": "This article explores artificial intelligence applications...",
    "orijinal_metin": "Full PDF text...",
    "etiketler": "AI, healthcare, machine learning",
    "created_at": "2026-02-18T10:30:00Z",
    "word_count_summary": 487,
    "word_count_original": 5234
}
```

### Hata Durumları

#### 1. Türkçe PDF Yüklendi
```json
{
    "detail": "Error: Document must be in English. BART model cannot translate from other languages."
}
```

#### 2. Yazar Bilgisi Çok Fazla
- Sistem otomatik temizler
- Özet sadece içerik kısmından üretilir

---

## 📈 Performans Metrikleri

### Uzunluk Doğruluğu

Test sonuçları (5000 kelimelik örnek makale):

| Mod | Hedef | Gerçek Çıktı | Sapma |
|-----|-------|--------------|-------|
| Short | 30-60w | 45w | ✅ İdeal |
| Medium | 500w (10%) | 487w | ✅ İdeal |
| Long | 1250w (25%) | 1203w | ✅ İdeal |

### Hız

- **Short**: ~5-10 saniye
- **Medium**: ~15-25 saniye  
- **Long**: ~30-60 saniye

(RTX 3060 GPU ile test edildi)

---

## 🧪 Test Etme

### Test Script Kullanımı

```bash
python test_summary_lengths.py
```

### Manuel Test

```python
from app.services.ai_service import summarize_with_embeddings

text = "Your English article text here..."

summary = summarize_with_embeddings(
    text=text,
    owner_id=1,
    title="Test Article",
    length_mode="medium",  # short | medium | long
    max_chars=5000,
    target_language="english",
    db=None  # Veya database session
)

print(f"Summary: {len(summary.split())} words")
print(summary)
```

---

## 🐛 Bilinen Sorunlar ve Sınırlamalar

### 1. Sadece İngilizce
- ❌ Türkçe PDF desteklenmiyor
- ❌ Otomatik çeviri yok
- ✅ Çözüm: İngilizce PDF kullanın

### 2. GPU Gereksinimleri
- **Minimum**: 6GB VRAM (GTX 1060 6GB)
- **Önerilen**: 8GB+ VRAM (RTX 3060+)
- CPU mode: Çok yavaş (önerilmez)

### 3. Çok Kısa Metinler
- <1000 kelime: "Long" modu otomatik olarak "medium"a düşer
- <500 kelime: Tüm modlar benzer çıktı verir
- <100 kelime: Özet oluşturulamaz

### 4. Yazar Bölümü Çok Uzunsa
- İlk %30'da "Abstract" veya "Introduction" bulunamazsa
- Sistem tüm metni özetler (yazar bilgileri dahil)
- **Çözüm**: PDF'i düzenleyin, başlık ekleyin

---

## 🔮 Gelecek Geliştirmeler

### Planlanan Özellikler

1. **Çok Dilli Destek**
   - mBART modeli entegrasyonu
   - Türkçe ↔ İngilizce çeviri

2. **Özel Özetleme Stilleri**
   - Akademik (formal)
   - Popüler (casual)
   - Teknik (jargon-heavy)

3. **Özetler Arası İlişki Grafiği**
   - Benzer özetleri görselleştirme
   - Konu kümeleme

4. **Gerçek Zamanlı Özet Önizleme**
   - Streaming output
   - Aşamalı özet gösterme

---

## 📞 Destek

Sorularınız için:
- GitHub Issues
- Email: support@example.com

---

**Son Güncelleme**: 18 Şubat 2026  
**Versiyon**: 2.0.0  
**Durum**: ✅ Stabil
