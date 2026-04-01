# Özet Oluşturma v2.0 - Hızlı Başlangıç

## ✅ Ne Değişti?

### 1. **Yeni Uzunluk Hedefleri**
- **Kısa**: 30-60 kelime (makalenin konusu)
- **Orta**: %10 (orijinal metnin)
- **Uzun**: %25 (orijinal metnin)

### 2. **Akıllı Bağlam Sistemi**
- Önceki özetlerinizi analiz eder
- Benzer konulardaki dökümanları birleştirir
- Daha iyi ve tutarlı özetler üretir

### 3. **Yazar Bilgilerini Otomatik Kaldırma**
- PDF'deki yazar adları, e-postalar temizlenir
- Sadece makale içeriği özetlenir

### 4. **Sadece İngilizce**
- Çıktı %100 İngilizce
- Türkçe içerik otomatik filtrelenir

---

## ⚠️ ÇOK ÖNEMLİ: PDF İngilizce Olmalı!

### Neden?

BART modeli (`facebook/bart-large-cnn`) **sadece İngilizce** için eğitildi:
- ❌ Türkçe özetleme yapamaz
- ❌ Çeviri yapamaz
- ❌ Türkçe PDF yüklerseniz çıktı BOZUK olur

### Türkçe PDF Kullanmak İsterseniz:

**3 Seçenek:**

1. **İngilizce PDF Kullanın** ✅ (Önerilen)
   - En hızlı ve en kaliteli

2. **Çeviri Modeli Ekleyin** 🔧 (Teknik)
   ```bash
   pip install sentencepiece
   # Helsinki-NLP/opus-mt-tr-en modelini entegre edin
   ```
   - Yavaş (ekstra ~2GB GPU bellek)
   - %100 doğru çeviri garanti değil

3. **Google Translate API Kullanın** 🌐 (Kolay)
   - Hızlı ve kaliteli
   - Ücretli (limitten sonra)

---

## 🚀 Kullanım

### API Çağrısı

```python
import requests

files = {'file': open('article.pdf', 'rb')}
data = {
    'baslik': 'AI in Healthcare',
    'length_option': 'medium',  # short | medium | long
    'target_language': 'english'
}

response = requests.post(
    'http://localhost:8000/api/ozetler/pdf_yukle',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {token}'}
)

summary = response.json()
print(f"Özet ({len(summary['ozet_metin'].split())} kelime):")
print(summary['ozet_metin'])
```

### Frontend Kullanımı

```html
<form action="/api/ozetler/pdf_yukle" method="POST" enctype="multipart/form-data">
  <input type="text" name="baslik" placeholder="Article Title" required>
  <input type="file" name="file" accept=".pdf" required>
  
  <select name="length_option">
    <option value="short">Kısa (30-60 kelime)</option>
    <option value="medium" selected>Orta (10%)</option>
    <option value="long">Uzun (25%)</option>
  </select>
  
  <input type="hidden" name="target_language" value="english">
  <button type="submit">Özet Oluştur</button>
</form>
```

---

## 📊 Örnek Çıktılar

### Kısa Özet (45 kelime)
```
This article explores the transformative impact of artificial 
intelligence on modern healthcare systems. It examines how machine 
learning algorithms improve diagnostic accuracy, predict patient 
outcomes, and optimize treatment plans while addressing ethical 
considerations and implementation challenges.
```

### Orta Özet (~500 kelime / 10%)
```
This comprehensive study investigates the integration of artificial 
intelligence technologies within healthcare systems. The research 
focuses on three primary areas: diagnostic support, predictive 
analytics, and personalized treatment recommendations.

In the diagnostic domain, deep learning models have demonstrated 
remarkable accuracy in medical image analysis, particularly in 
radiology and pathology. Convolutional neural networks achieve 
performance comparable to expert clinicians in detecting various 
conditions...

[~500 kelime daha]
```

### Uzun Özet (~1250 kelime / 25%)
```
[Detaylı, kapsamlı özet - executive summary tarzı]
```

---

## 🧪 Test

```bash
# Test script'i çalıştırın
python test_summary_lengths.py

# Beklenen çıktı:
# ✅ Short: 30-60 words
# ✅ Medium: 10% of original
# ✅ Long: 25% of original
```

---

## 🐛 Sorun Giderme

### "Document must be in English" Hatası
**Neden**: PDF Türkçe veya başka dilde  
**Çözüm**: İngilizce PDF kullanın

### Özet Çok Kısa Çıkıyor
**Neden**: Orijinal metin çok kısa (<1000 kelime)  
**Çözüm**: Daha uzun döküman kullanın veya "medium" seçin

### Yazar Bilgileri Hala Var
**Neden**: PDF'de "Abstract" veya "Introduction" başlığı yok  
**Çözüm**: PDF'e başlık ekleyin veya manuel düzenleyin

### Çok Yavaş
**Neden**: CPU mode aktif  
**Çözüm**: GPU kullanın (`USE_GPU=true` .env'de)

---

## 📝 Kod Değişiklikleri Özeti

### `ai_service.py`
- ✅ `_get_user_context_from_db()` eklendi (veritabanı entegrasyonu)
- ✅ `_clean_text()` güncellendi (yazar temizleme + strict English)
- ✅ `summarize_with_embeddings()` yeni parametreler (`db` session)
- ✅ Yeni uzunluk hedefleri (30-60w, 10%, 25%)

### `ozet_service.py`
- ✅ `create_ozet()` güncellendi (`db` session geçişi)
- ✅ Default dil: `turkish` → `english`

### `ozet_router.py`
- ✅ Default `target_language`: `turkish` → `english`
- ✅ Docstring güncellendi
- ✅ Settings güncellendi (yeni targets)

---

## 📚 Detaylı Dokümantasyon

Daha fazla bilgi için: [SUMMARY_FEATURE_V2.md](SUMMARY_FEATURE_V2.md)

---

**Hazırlayan**: AI Assistant  
**Tarih**: 18 Şubat 2026  
**Versiyon**: 2.0.0
