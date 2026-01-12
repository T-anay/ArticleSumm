# app/services/ai_service.py
from typing import List
import yake

# Not: Gerçek bir LLM (Gemini/GPT) kullanıldığında buradaki 'logic' 
# Prompt içine gömülmelidir. Şimdilik simülasyon yapıyoruz.

def summarize_text_simple(text: str, max_chars: int = 800, length_mode: str = "medium") -> str:
    """
    length_mode: 'short', 'medium', 'long'
    """
    
    # Basit bir kesme işlemi (Gerçek AI entegrasyonuna kadar placeholder)
    if len(text) <= max_chars:
        summary_content = text
    else:
        summary_content = text[:max_chars].rsplit('.', 1)[0] + '.'

    # --- FORMATLAMA SİMÜLASYONU (UX Raporuna Göre) ---
    
    if length_mode == "short":
        # Ters Piramit: Tek paragraf, net bilgi.
        return f"<b>Öz (Abstract):</b> {summary_content}"

    elif length_mode == "medium":
        # Smart Brevity (Axios Stili): Kalın girişler, maddeler.
        # Bu sadece bir simülasyon, gerçek metni analiz etmiyoruz.
        return f"""
        <p><b>Büyük Resim:</b> {summary_content[:150]}...</p>
        <p><b>Neden Önemli:</b></p>
        <ul>
            <li>Temel veri noktası 1: Analiz edilen metindeki önemli bulgular.</li>
            <li>Temel veri noktası 2: İstatistiksel anlamlılık ve sonuçlar.</li>
            <li>Temel veri noktası 3: Pratik uygulamalar.</li>
        </ul>
        <p><b>Sonuç:</b> {summary_content[150:300]}...</p>
        """

    elif length_mode == "long":
        # Executive Summary: H2 Başlıklar (ToC için gerekli), Paragraflar.
        return f"""
        <h2>Yönetici Özeti Giriş</h2>
        <p>{summary_content[:400]}</p>
        
        <h2>Metodoloji ve Yaklaşım</h2>
        <p>{summary_content[400:800]}</p>
        
        <h2>Bulgular ve Analiz</h2>
        <p>{summary_content[800:1200]}</p>
        
        <h3>Kritik Veriler</h3>
        <p>Burada detaylı veri analizi yer alır.</p>
        
        <h2>Sonuç ve Öneriler</h2>
        <p>{summary_content[1200:]}</p>
        """
    
    return summary_content

def extract_keywords_yake(text: str, max_keywords: int = 8) -> List[str]:
    try:
        kw_extractor = yake.KeywordExtractor(lan="en", top=max_keywords)
        keywords = kw_extractor.extract_keywords(text)
        return [k for k, s in keywords]
    except Exception:
        tokens = text.split()
        frequent = sorted(set(tokens), key=lambda t: -tokens.count(t))
        return frequent[:max_keywords]