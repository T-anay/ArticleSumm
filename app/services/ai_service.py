# app/services/ai_service.py
from typing import List, Dict, Any, Optional
import os
import uuid
import traceback
import numpy as np
import requests

import yake
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import torch
from sqlalchemy.orm import Session

# Language detection
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("[AI] langdetect not available, language auto-detection disabled")

# Chroma DB (opsiyonel - eğer kuruluysa kullan)
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("[AI] ChromaDB not available, using direct summarization")

# Not: Gerçek bir LLM (Gemini/GPT) kullanıldığında buradaki 'logic' 
# Prompt içine gömülmelidir. Şimdilik simülasyon yapıyoruz. 

_EMBEDDING_MODEL: SentenceTransformer | None = None
_SUMMARIZER = None
_SUMMARIZER_MODEL: str | None = None
_MBART_MODEL = None
_MBART_TOKENIZER = None
_DEVICE = None  # GPU device cache

# mBART-50 Language Codes (50 languages supported)
MBART_LANG_CODES = {
    'ar': 'ar_AR', 'cs': 'cs_CZ', 'de': 'de_DE', 'en': 'en_XX', 'es': 'es_XX',
    'et': 'et_EE', 'fi': 'fi_FI', 'fr': 'fr_XX', 'gu': 'gu_IN', 'hi': 'hi_IN',
    'it': 'it_IT', 'ja': 'ja_XX', 'kk': 'kk_KZ', 'ko': 'ko_KR', 'lt': 'lt_LT',
    'lv': 'lv_LV', 'my': 'my_MM', 'ne': 'ne_NP', 'nl': 'nl_XX', 'ro': 'ro_RO',
    'ru': 'ru_RU', 'si': 'si_LK', 'tr': 'tr_TR', 'vi': 'vi_VN', 'zh': 'zh_CN',
    'af': 'af_ZA', 'az': 'az_AZ', 'bn': 'bn_IN', 'fa': 'fa_IR', 'he': 'he_IL',
    'hr': 'hr_HR', 'id': 'id_ID', 'ka': 'ka_GE', 'km': 'km_KH', 'mk': 'mk_MK',
    'ml': 'ml_IN', 'mn': 'mn_MN', 'mr': 'mr_IN', 'pl': 'pl_PL', 'ps': 'ps_AF',
    'pt': 'pt_XX', 'sv': 'sv_SE', 'sw': 'sw_KE', 'ta': 'ta_IN', 'te': 'te_IN',
    'th': 'th_TH', 'tl': 'tl_XX', 'uk': 'uk_UA', 'ur': 'ur_PK', 'xh': 'xh_ZA',
    'gl': 'gl_ES', 'sl': 'sl_SI'
}

# Human-readable language names
LANGUAGE_NAMES = {
    'ar': 'Arabic', 'cs': 'Czech', 'de': 'German', 'en': 'English', 'es': 'Spanish',
    'et': 'Estonian', 'fi': 'Finnish', 'fr': 'French', 'gu': 'Gujarati', 'hi': 'Hindi',
    'it': 'Italian', 'ja': 'Japanese', 'kk': 'Kazakh', 'ko': 'Korean', 'lt': 'Lithuanian',
    'lv': 'Latvian', 'my': 'Burmese', 'ne': 'Nepali', 'nl': 'Dutch', 'ro': 'Romanian',
    'ru': 'Russian', 'si': 'Sinhala', 'tr': 'Turkish', 'vi': 'Vietnamese', 'zh': 'Chinese',
    'af': 'Afrikaans', 'az': 'Azerbaijani', 'bn': 'Bengali', 'fa': 'Persian', 'he': 'Hebrew',
    'hr': 'Croatian', 'id': 'Indonesian', 'ka': 'Georgian', 'km': 'Khmer', 'mk': 'Macedonian',
    'ml': 'Malayalam', 'mn': 'Mongolian', 'mr': 'Marathi', 'pl': 'Polish', 'ps': 'Pashto',
    'pt': 'Portuguese', 'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil', 'te': 'Telugu',
    'th': 'Thai', 'tl': 'Tagalog', 'uk': 'Ukrainian', 'ur': 'Urdu', 'xh': 'Xhosa',
    'gl': 'Galician', 'sl': 'Slovenian'
}


def _normalize_lang_code(lang: str) -> str:
    """Normalize language value to ISO-like short code used internally."""
    if not lang:
        return "en"

    lang_norm = lang.strip().lower()
    aliases = {
        "english": "en",
        "turkish": "tr",
        "german": "de",
        "french": "fr",
        "spanish": "es",
        "italian": "it",
        "portuguese": "pt",
        "arabic": "ar",
        "russian": "ru",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
    }
    return aliases.get(lang_norm, lang_norm)


def _target_word_count(length_mode: str, original_word_count: int) -> int:
    """Calculate expected output length in words."""
    if length_mode == "short":
        return min(60, max(30, int(original_word_count * 0.05)))
    if length_mode == "long":
        # Cap long summaries for external providers to keep response latency bounded.
        return min(900, max(120, int(original_word_count * 0.25)))
    return max(60, int(original_word_count * 0.10))


def _summarize_with_external_api(
    text: str,
    source_language: str,
    target_language: str,
    length_mode: str,
    original_word_count: int,
) -> str:
    """Summarize via OpenAI-compatible external chat completions API."""
    api_key = os.getenv("EXTERNAL_LLM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("EXTERNAL_LLM_API_KEY is not set")

    base_url = os.getenv("EXTERNAL_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    endpoint = os.getenv("EXTERNAL_LLM_ENDPOINT", "/chat/completions")
    model = os.getenv("EXTERNAL_LLM_MODEL", "gpt-4o-mini")
    timeout_seconds = int(os.getenv("EXTERNAL_LLM_TIMEOUT_SECONDS", "90"))
    max_input_chars = int(os.getenv("EXTERNAL_LLM_MAX_INPUT_CHARS", "24000"))

    text_for_model = text[:max_input_chars]
    target_words = _target_word_count(length_mode, original_word_count)

    source_code = _normalize_lang_code(source_language)
    target_code = _normalize_lang_code(target_language)
    source_name = LANGUAGE_NAMES.get(source_code, source_code)
    target_name = LANGUAGE_NAMES.get(target_code, target_code)

    system_prompt = (
        "You are an expert academic summarizer. "
        "Return only the final summary text with no bullets, no markdown, and no preface."
    )
    user_prompt = (
        f"Summarize the following academic text. Source language: {source_name}. "
        f"Output language must be {target_name}. "
        f"Target length: approximately {target_words} words. "
        "Keep factual accuracy, remove author metadata/noise, and preserve key findings.\n\n"
        f"TEXT:\n{text_for_model}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{base_url}{endpoint}",
        json=payload,
        headers=headers,
        timeout=timeout_seconds,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"External API error {response.status_code}: {response.text[:300]}")

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not content:
        raise RuntimeError("External API returned empty summary")

    return content


def _is_mostly_english(text: str) -> bool:
    """Check if text is mostly English (not Turkish). STRICT filtering."""
    import re
    if not text or len(text.strip()) < 10:
        return False
    
    # Count Turkish-specific characters
    turkish_chars = len(re.findall(r'[çğışöüÇĞİŞÖÜ]', text))
    alpha_chars = len(re.findall(r'[a-zA-ZçğışöüÇĞİŞÖÜ]', text))
    
    # Even 1 Turkish character per 100 is too much - reject
    if alpha_chars > 0 and turkish_chars > 0:
        turkish_ratio = turkish_chars / alpha_chars
        if turkish_ratio > 0.01:  # More than 1% Turkish = reject
            return False
    
    # Check for common Turkish words (very strict)
    turkish_words = [
        'ile', 've', 'bir', 'bu', 'olan', 'üzerinde', 'olarak', 'gere', 
        'olduğu', 'olabilir', 'için', 'gibi', 'daha', 'çok', 'kadar',
        'böyle', 'şekilde', 'ancak', 'sonra', 'önce', 'yapay', 'toplum',
        'gelişme', 'teknoloji', 'içinde', 'arasında', 'karşı'
    ]
    text_lower = text.lower()
    turkish_word_count = sum(1 for word in turkish_words if re.search(rf'\b{word}\b', text_lower))
    
    # If ANY Turkish word found, reject
    if turkish_word_count > 0:
        return False
    
    return True

def _remove_ocr_gibberish(text: str) -> str:
    """Remove OCR artifacts: repeated words, garbled sequences, corrupted text."""
    import re
    
    # Remove sequences of repeated words (e.g., "still both only the only both still")
    # Split into tokens and look for patterns like word1 word2 word3 word1 word2, etc.
    text = re.sub(r'\b(\w+)\s+(\w+)\s+(\w+)\s+(?:\1\s+)(?:\2\s+)?(?:\3\s+)?(?:\1\s+)+', '', text, flags=re.IGNORECASE)
    
    # Remove sequences of the same word repeated 3+ times in a row
    text = re.sub(r'\b(\w+)(?:\s+\1){2,}\b', '', text, flags=re.IGNORECASE)
    
    # Remove garbled patterns: multiple single letters with mixed case (e.g., "oOneoJust these still")
    text = re.sub(r'(?:[A-Z][a-z]?\s+){4,}(?:[A-Z][a-z]?\s+)*', ' ', text)
    
    # Remove sequences of words that look like corrupted tokens (short fragments mixed with normal words)
    # Pattern: "shorto shortto" etc. (word ending with 'o' followed by word starting with lowercase)
    text = re.sub(r'\b(\w{1,3}o)\s+([a-z]{1,3}[a-z])\b', '', text, flags=re.IGNORECASE)
    
    # Remove isolated character+number patterns that are OCR artifacts (e.g., "Te", "Y", "W", "SheShe")
    text = re.sub(r'\b[A-Z](?:e|o|a|u|i)(?:\s+[A-Z](?:e|o|a|u|i))+\b', '', text)
    
    # Remove lines with mostly duplicate words (signal of OCR corruption)
    lines = text.split('.')
    filtered_lines = []
    for line in lines:
        words = line.lower().split()
        if len(words) > 3:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.4:  # At least 40% unique words (not repetitive)
                filtered_lines.append(line)
        else:
            filtered_lines.append(line)
    
    text = '. '.join(filtered_lines)
    return text


def _clean_text(text: str, strict_english_only: bool = True) -> str:
    """Clean text from PDF extraction artifacts, author info, and non-English content.
    
    Args:
        text: Text to clean
        strict_english_only: If True (DEFAULT), aggressively remove all non-English content
    """
    import re
    
    # === PHASE 0: Remove OCR Gibberish ===
    text = _remove_ocr_gibberish(text)
    
    # === PHASE 1: Remove Author/Header Information ===
    # Remove author name patterns: "Dr. John Smith", "Prof. Jane Doe", etc.
    text = re.sub(r'(Prof\.|Dr\.|Professor|Associate Professor)\s+[A-Z][a-z]+\s+[A-Z][a-z]+', '', text, flags=re.IGNORECASE)
    
    # Remove author affiliations and email patterns
    text = re.sub(r'(Department of|Faculty of|University of|Institute of)[^.]*\.', '', text)
    text = re.sub(r'\S+@\S+\.(edu|com|org|net)', '', text)
    
    # Remove author bio patterns: "... is a Professor at ..."
    text = re.sub(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+is\s+(a|an)\s+(Professor|researcher|expert|scientist)[^.]*\.', '', text)
    
    # Remove "Author:" or "Authors:" sections
    text = re.sub(r'Autho?r?s?:\s*[^\n]*', '', text, flags=re.IGNORECASE)
    
    # === PHASE 2: Remove PDF Artifacts ===
    # Remove page numbers and section numbers
    text = re.sub(r'\b\d{1,3}\s+(Abstract|Introduction|Summary|Conclusion)\b', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+\d{1,3}\s+', ' ', text)
    
    # Remove URLs and DOIs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'doi:\s*\S+', '', text, flags=re.IGNORECASE)
    
    # Remove reference citations: "Smith (2020)", "Johnson et al. (2019)"
    text = re.sub(r'\b[A-Z][a-z]+(\s+et\s+al\.)?\s*\(\d{4}[a-z]?\)', '', text)
    
    # Remove common footer/header artifacts
    text = re.sub(r'\bH\.R\.\d+\b', '', text)
    text = re.sub(r'The \d+(th|st|nd|rd)\s+(Congress|Conference|Symposium)', '', text)
    
    # === PHASE 3: Fix PDF Extraction Issues ===
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)  # Add space after punctuation
    text = re.sub(r'([.,!?;:]){2,}', r'\1', text)  # Remove excessive punctuation
    
    # === PHASE 4: STRICT ENGLISH-ONLY MODE (DEFAULT) ===
    if strict_english_only:
        # Split into sentences and filter
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        cleaned_sentences = []
        
        for sentence in sentences:
            if len(sentence) < 15:  # Skip very short fragments
                continue
            
            # Reject if contains Turkish/non-Latin characters
            if re.search(r'[çğışöüÇĞİŞÖÜâîûêôАБВГДабвгд]', sentence):
                continue
            
            # Reject if contains common Turkish words
            turkish_words = [
                'ile', 've', 'bir', 'bu', 'olan', 'üzerinde', 'olarak', 'için',
                'gibi', 'daha', 'çok', 'kadar', 'böyle', 'şekilde', 'yapay',
                'toplum', 'gelişme', 'teknoloji', 'olmak', 'yapmak', 'olabilir',
                'değil', 'vardır', 've', 'ise', 'çünkü', 'ancak', 'sonuç',
                'gerekmektedir', 'kullanılmaktadır'
            ]
            
            sentence_lower = sentence.lower()
            has_turkish = any(re.search(rf'\b{word}\b', sentence_lower) for word in turkish_words)
            if has_turkish:
                continue
            
            # Only keep sentences that are mostly ASCII and look like English
            ascii_ratio = sum(1 for c in sentence if ord(c) < 128) / len(sentence)
            if ascii_ratio > 0.95:  # At least 95% ASCII
                cleaned_sentences.append(sentence)
        
        text = '. '.join(cleaned_sentences)
        if text and not text.endswith('.'):
            text += '.'
    
    return text.strip()

def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks sized for embedding and storage."""
    chunks: List[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start = max(0, end - chunk_overlap)
    return chunks


def _get_user_context_from_db(db: Optional[Session], owner_id: int, current_text: str) -> str:
    """
    Get all user's previous summaries from database and merge with current text
    for better context-aware summarization.
    
    Args:
        db: Database session (optional)
        owner_id: User ID
        current_text: Current document text to summarize
        
    Returns:
        Merged text with context from similar previous documents
    """
    if db is None:
        print("[CONTEXT] No database session, using only current text")
        return current_text
    
    try:
        # Import here to avoid circular dependency
        from app.models.models import Ozet

        max_candidates = int(os.getenv("CONTEXT_MAX_CANDIDATES", "40"))
        top_k = int(os.getenv("CONTEXT_TOP_K", "2"))
        snippet_chars = int(os.getenv("CONTEXT_SNIPPET_CHARS", "300"))
        similarity_threshold = float(os.getenv("CONTEXT_SIM_THRESHOLD", "0.72"))

        # Limit candidate set to keep latency predictable on heavy user history.
        previous_summaries = (
            db.query(Ozet)
            .filter(Ozet.sahip_id == owner_id)
            .order_by(Ozet.created_at.desc())
            .limit(max_candidates)
            .all()
        )
        
        if not previous_summaries:
            print(f"[CONTEXT] No previous summaries for user {owner_id}")
            return current_text
        
        print(f"[CONTEXT] Found {len(previous_summaries)} previous summaries (limited)")

        # Create embeddings for similarity comparison
        model = _get_embedding_model()
        current_embedding = model.encode([current_text], normalize_embeddings=True)[0]

        # Deduplicate repeated texts before embedding.
        unique_candidates: list[tuple[str, str]] = []
        seen_text_keys: set[str] = set()
        for summary in previous_summaries:
            prev_text = summary.orijinal_metin
            if not prev_text or len(prev_text) < 100:
                continue

            text_key = " ".join(prev_text.split())[:1200]
            if text_key in seen_text_keys:
                continue

            seen_text_keys.add(text_key)
            unique_candidates.append((summary.baslik or "Untitled", prev_text))

        if not unique_candidates:
            print("[CONTEXT] No eligible previous texts after dedup/filter")
            return current_text

        # Batch embedding is much faster than one-by-one encoding.
        candidate_texts = [text for _, text in unique_candidates]
        candidate_embeddings = model.encode(candidate_texts, normalize_embeddings=True)

        similar_contexts = []
        for (title, prev_text), prev_embedding in zip(unique_candidates, candidate_embeddings):
            similarity = float(np.dot(current_embedding, prev_embedding))
            if similarity >= similarity_threshold:
                similar_contexts.append((similarity, prev_text[:snippet_chars]))
                print(f"[CONTEXT] Similar doc (sim={similarity:.2f}): {title[:50]}")

        # Merge only top-k contexts to avoid growing prompt size too much.
        if similar_contexts:
            similar_contexts.sort(reverse=True, key=lambda x: x[0])
            context_texts = [ctx[1] for ctx in similar_contexts[:top_k]]
            merged = " ".join(context_texts) + " " + current_text
            print(f"[CONTEXT] Merged with {len(context_texts)} similar documents")
            return merged
        else:
            print(f"[CONTEXT] No similar documents found (threshold: {similarity_threshold})")
            return current_text
            
    except Exception as e:
        print(f"[CONTEXT ERROR] {e}")
        traceback.print_exc()
        return current_text


def summarize_text_simple(text: str, max_chars: int = 800, length_mode: str = "medium") -> str:
    """
    Fallback summarization: simple text cutting based on length_mode.
    NEW Target lengths:
    - short: 30-60 words (mobile-friendly, article topic)
    - medium: 10% of original text
    - long: 25% of original text
    """
    words = text.split()
    word_count = len(words)
    
    # Calculate target word count
    if length_mode == "short":
        target_words = min(60, max(30, int(word_count * 0.05)))  # 30-60 words
    elif length_mode == "medium":
        target_words = int(word_count * 0.10)  # 10% of original
    elif length_mode == "long":
        target_words = int(word_count * 0.25)  # 25% of original
    else:
        target_words = int(word_count * 0.10)
    
    # Extract sentences up to target
    sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
    summary_words = []
    
    for sentence in sentences:
        sentence_words = sentence.split()
        if len(summary_words) + len(sentence_words) <= target_words:
            summary_words.extend(sentence_words)
        else:
            break
    
    if not summary_words:
        summary_words = words[:target_words]
    
    return ' '.join(summary_words)

def extract_keywords_yake(text: str, max_keywords: int = 8) -> List[str]:
    try:
        kw_extractor = yake.KeywordExtractor(lan="en", top=max_keywords)
        keywords = kw_extractor.extract_keywords(text)
        return [k for k, s in keywords]
    except Exception:
        tokens = text.split()
        frequent = sorted(set(tokens), key=lambda t: -tokens.count(t))
        return frequent[:max_keywords]


def _get_embedding_model() -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _EMBEDDING_MODEL = SentenceTransformer(model_name)
    return _EMBEDDING_MODEL


def _get_device() -> int:
    """Get device for model inference (-1 for CPU, 0+ for GPU)"""
    global _DEVICE
    if _DEVICE is None:
        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        if use_gpu and torch.cuda.is_available():
            _DEVICE = 0
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[AI] Using GPU: {gpu_name}")
        else:
            _DEVICE = -1
            print(f"[AI] Using CPU (GPU not available or disabled)")
    return _DEVICE


def detect_language(text: str) -> str:
    """
    Detect the language of the input text.
    Returns ISO 639-1 code (e.g., 'en', 'tr', 'de')
    """
    if not LANGDETECT_AVAILABLE:
        print("[LANG DETECT] langdetect not available, assuming English")
        return 'en'
    
    try:
        # Take a sample from the text (first 1000 chars for speed)
        sample = text[:1000]
        detected = detect(sample)
        print(f"[LANG DETECT] Detected language: {detected} ({LANGUAGE_NAMES.get(detected, 'Unknown')})")
        return detected
    except LangDetectException as e:
        print(f"[LANG DETECT ERROR] {e}, defaulting to English")
        return 'en'
    except Exception as e:
        print(f"[LANG DETECT ERROR] {e}, defaulting to English")
        return 'en'


def _get_mbart_model():
    """Load and cache mBART-50 model for multilingual summarization"""
    global _MBART_MODEL, _MBART_TOKENIZER
    
    if _MBART_MODEL is None or _MBART_TOKENIZER is None:
        print("[MBART] Loading mBART-50 multilingual model...")
        try:
            from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
            
            model_name = "facebook/mbart-large-50-many-to-many-mmt"
            _MBART_TOKENIZER = MBart50TokenizerFast.from_pretrained(model_name)
            _MBART_MODEL = MBartForConditionalGeneration.from_pretrained(model_name)
            
            # Move to GPU if available
            device = _get_device()
            if device >= 0:
                _MBART_MODEL = _MBART_MODEL.to(f"cuda:{device}")
                _MBART_MODEL = _MBART_MODEL.half()  # FP16 for faster inference
                print(f"[MBART] Model loaded on GPU (FP16)")
            else:
                print(f"[MBART] Model loaded on CPU")
            
            print(f"[MBART] ✓ Model ready: {model_name}")
            
        except ImportError:
            print("[MBART ERROR] transformers or sentencepiece not installed")
            print("[MBART ERROR] Run: pip install transformers sentencepiece")
            raise
        except Exception as e:
            print(f"[MBART ERROR] Failed to load model: {e}")
            raise
    
    return _MBART_MODEL, _MBART_TOKENIZER


def is_language_supported(lang_code: str) -> bool:
    """Check if a language is supported by mBART-50"""
    return lang_code in MBART_LANG_CODES


def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of all supported languages with codes and names"""
    return [
        {"code": code, "name": name, "mbart_code": MBART_LANG_CODES[code]}
        for code, name in sorted(LANGUAGE_NAMES.items(), key=lambda x: x[1])
    ]


def _translate_to_turkish(text: str) -> str:
    """
    DEPRECATED: Use summarize_multilingual() instead
    Basit İngilizce -> Türkçe çeviri (Helsinki-NLP modeli ile)
    Şimdilik placeholder - gerçek implementasyon gerekirse eklenecek
    """
    try:
        # ÖNEMLİ: Bu feature şimdilik devre dışı
        # Çeviri modeli yüklemek çok zaman alıyor
        # Alternatif: googletrans kütüphanesi veya API kullan
        return text
    except Exception as e:
        print(f"[TRANSLATE ERROR] {e}")
        return text


def _mbart_summarize(model, tokenizer, device, text: str, target_language: str, min_len: int, max_len: int) -> str:
    """
    mBART model ile çok dilli özetleme
    """
    try:
        # Dil kodları
        lang_codes = {
            "turkish": "tr_TR",
            "english": "en_XX",
            "german": "de_DE",
            "french": "fr_XX",
        }
        
        src_lang = lang_codes.get(target_language, "en_XX")
        tgt_lang = src_lang  # Aynı dilde özet
        
        # Tokenize
        tokenizer.src_lang = src_lang
        inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        
        if device >= 0:
            inputs = {k: v.to(f"cuda:{device}") for k, v in inputs.items()}
        
        # Generate
        forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
        outputs = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            min_length=min_len,
            max_length=max_len,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
            no_repeat_ngram_size=3,
        )
        
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary
        
    except Exception as e:
        print(f"[MBART ERROR] {e}")
        # Fallback: simple truncation
        words = text.split()[:max_len]
        return " ".join(words)


def _truncate_to_target(text: str, target_words: int, min_words: int) -> str:
    """
    SADECE LOG İÇİN - Artık kırpma yapmıyor, sadece uyarı veriyor
    """
    words = text.split()
    current_length = len(words)
    
    print(f"[LENGTH CHECK] Current: {current_length}w, Target: {target_words}w, Min: {min_words}w")
    
    # Artık kırpma yapma, model'ın çıktısını olduğu gibi kullan
    if current_length < min_words * 0.5:
        print(f"[WARNING] Summary much shorter than expected!")
    elif current_length > target_words * 2:
        print(f"[WARNING] Summary much longer than expected!")
    else:
        print(f"[INFO] Length is acceptable")
    
    return text  # HER ZAMAN ORİJİNAL METİNİ DÖNDÜR


def _get_summarizer() -> Any:
    global _SUMMARIZER, _SUMMARIZER_MODEL
    # BASITLEŞTİRİLMIS: Standard BART kullan (daha stabil)
    # Türkçe/İngilizce post-processing ile halledelim
    model_name = os.getenv("SUMMARY_MODEL", "facebook/bart-large-cnn")
    
    if _SUMMARIZER is None or _SUMMARIZER_MODEL != model_name:
        print(f"[AI] Loading summarizer model: {model_name}")
        device = _get_device()

        try:
            _SUMMARIZER = pipeline(
                "summarization",
                model=model_name,
                device=device,
                torch_dtype=torch.float16 if device >= 0 else torch.float32,
            )
            print("[AI] Summarization pipeline loaded")
        except KeyError as task_err:
            print(f"[AI WARNING] summarization task unavailable: {task_err}")
            print("[AI] Falling back to text2text-generation pipeline")
            try:
                _SUMMARIZER = pipeline(
                    "text2text-generation",
                    model=model_name,
                    device=device,
                    torch_dtype=torch.float16 if device >= 0 else torch.float32,
                )
            except KeyError as task_err_2:
                print(f"[AI WARNING] text2text-generation task unavailable: {task_err_2}")
                print("[AI] Falling back to text-generation pipeline")
                _SUMMARIZER = pipeline(
                    "text-generation",
                    model=model_name,
                    device=device,
                    torch_dtype=torch.float16 if device >= 0 else torch.float32,
                )
        
        _SUMMARIZER_MODEL = model_name
        print(f"[AI] Model loaded successfully (type: standard pipeline)")
    return _SUMMARIZER


def _extract_summary_text(result: Any) -> str:
    """Read model output across summarization/text2text-generation tasks."""
    if not result:
        return ""
    first = result[0] if isinstance(result, list) else result
    if isinstance(first, dict):
        return (first.get("summary_text") or first.get("generated_text") or "").strip()
    return str(first).strip()


def summarize_multilingual(
    text: str,
    source_lang: str,
    target_lang: str,
    length_mode: str = "medium",
    original_word_count: Optional[int] = None
) -> str:
    """
    Multilingual summarization using mBART-50.
    Can summarize text in one language and output in another.
    
    Examples:
        - Turkish article → English summary
        - English article → German summary
        - French article → Turkish summary
    
    Args:
        text: Input text to summarize
        source_lang: Source language code (e.g., 'tr', 'en', 'de')
        target_lang: Target language code for summary
        length_mode: 'short', 'medium', or 'long'
        original_word_count: Original full text word count (for percentage calculation)
        
    Returns:
        Summary in target language
    """
    print(f"\n{'='*60}")
    print(f"[MULTILINGUAL] Source: {LANGUAGE_NAMES.get(source_lang, source_lang)} → Target: {LANGUAGE_NAMES.get(target_lang, target_lang)}")
    print(f"[MULTILINGUAL] Mode: {length_mode}")
    
    # Validate language support
    if not is_language_supported(source_lang):
        print(f"[MULTILINGUAL ERROR] Source language '{source_lang}' not supported by mBART-50")
        print(f"[MULTILINGUAL] Supported languages: {', '.join(sorted(MBART_LANG_CODES.keys()))}")
        raise ValueError(f"Language '{source_lang}' not supported. Use one of: {', '.join(sorted(MBART_LANG_CODES.keys()))}")
    
    if not is_language_supported(target_lang):
        print(f"[MULTILINGUAL ERROR] Target language '{target_lang}' not supported by mBART-50")
        raise ValueError(f"Language '{target_lang}' not supported")
    
    try:
        # Load mBART model
        model, tokenizer = _get_mbart_model()
        device = _get_device()
        
        # Calculate target lengths
        if original_word_count is None:
            original_word_count = len(text.split())
        
        if length_mode == "short":
            target_words = min(60, max(30, int(original_word_count * 0.05)))
            min_len = 20
            max_len = 80
        elif length_mode == "medium":
            target_words = int(original_word_count * 0.10)
            min_len = max(50, int(target_words * 0.6))
            max_len = min(400, int(target_words * 1.5))
        elif length_mode == "long":
            target_words = int(original_word_count * 0.25)
            min_len = max(100, int(target_words * 0.3))
            max_len = min(1024, int(target_words * 0.6))  # mBART max
        else:
            target_words = int(original_word_count * 0.10)
            min_len = 50
            max_len = 200
        
        print(f"[MULTILINGUAL] Original: {original_word_count}w → Target: {target_words}w ({int(target_words*100/original_word_count)}%)")
        print(f"[MULTILINGUAL] mBART range: min={min_len}, max={max_len}")
        
        # Set source language
        src_lang_code = MBART_LANG_CODES[source_lang]
        tgt_lang_code = MBART_LANG_CODES[target_lang]
        tokenizer.src_lang = src_lang_code
        
        # For long texts, use multi-chunk strategy
        current_word_count = len(text.split())
        if current_word_count > 1000:
            print(f"[MULTILINGUAL] Long text detected ({current_word_count}w), using chunking strategy")
            chunks = chunk_text(text, chunk_size=900, chunk_overlap=100)
            print(f"[MULTILINGUAL] Split into {len(chunks)} chunks")
            
            partials = []
            max_chunks = min(len(chunks), 10 if length_mode == "long" else 5)
            
            for i, chunk in enumerate(chunks[:max_chunks]):
                try:
                    # Encode chunk
                    inputs = tokenizer(
                        chunk,
                        return_tensors="pt",
                        max_length=1024,
                        truncation=True
                    )
                    
                    if device >= 0:
                        inputs = {k: v.to(f"cuda:{device}") for k, v in inputs.items()}
                    
                    # Generate summary
                    outputs = model.generate(
                        **inputs,
                        forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang_code],
                        min_length=max(20, min_len // max_chunks),
                        max_length=min(200, max_len // max_chunks),
                        num_beams=4,
                        length_penalty=1.5,
                        early_stopping=True,
                        no_repeat_ngram_size=3
                    )
                    
                    partial = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    partials.append(partial)
                    print(f"[MULTILINGUAL] Chunk {i+1}/{max_chunks}: {len(chunk.split())}w → {len(partial.split())}w")
                    
                except Exception as e:
                    print(f"[MULTILINGUAL] Chunk {i+1} failed: {e}")
                    continue
            
            if not partials:
                print(f"[MULTILINGUAL ERROR] No valid chunks processed")
                return "Error: Could not generate summary"
            
            # Merge partials
            merged = " ".join(partials)
            print(f"[MULTILINGUAL] ✓ Final: {len(merged.split())}w")
            print(f"{'='*60}\n")
            return merged
        
        else:
            # Single-pass summarization for shorter texts
            print(f"[MULTILINGUAL] Short text, single-pass summarization")
            
            inputs = tokenizer(
                text,
                return_tensors="pt",
                max_length=1024,
                truncation=True
            )
            
            if device >= 0:
                inputs = {k: v.to(f"cuda:{device}") for k, v in inputs.items()}
            
            # Generate summary
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang_code],
                min_length=min_len,
                max_length=max_len,
                num_beams=4,
                length_penalty=1.5,
                early_stopping=True,
                no_repeat_ngram_size=3
            )
            
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"[MULTILINGUAL] ✓ Final: {len(summary.split())}w")
            print(f"{'='*60}\n")
            return summary
            
    except Exception as e:
        print(f"[MULTILINGUAL ERROR] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        # Fallback
        return summarize_text_simple(text, length_mode=length_mode)


def _get_chroma_client():
    """Get Chroma client (returns None if not available)"""
    if not CHROMA_AVAILABLE:
        return None
    
    try:
        host = os.getenv("CHROMA_HOST", "api.trychroma.com")
        port = int(os.getenv("CHROMA_PORT", "443"))
        ssl = os.getenv("CHROMA_SSL", "true").lower() == "true"
        api_key = os.getenv("CHROMA_API_KEY")
        tenant = os.getenv("CHROMA_TENANT")
        database = os.getenv("CHROMA_DATABASE")

        if not tenant or not database:
            print("[AI] Chroma tenant/database not configured, skipping Chroma")
            return None

        headers: Dict[str, str] = {}
        if api_key:
            headers["X-Chroma-Token"] = api_key

        return chromadb.HttpClient(
            host=host,
            port=port,
            ssl=ssl,
            headers=headers,
            tenant=tenant,
            database=database,
        )
    except Exception as e:
        print(f"[AI] Chroma client error: {e}")
        return None


def _get_chroma_collection(client):
    """Get Chroma collection (returns None if client is None)"""
    if client is None:
        return None
    try:
        collection_name = os.getenv("CHROMA_COLLECTION", "ozet_chunks")
        return client.get_or_create_collection(name=collection_name)
    except Exception as e:
        print(f"[AI] Chroma collection error: {e}")
        return None


def _mean_embedding(embeddings: List[List[float]]) -> List[float]:
    if not embeddings:
        return []
    dim = len(embeddings[0])
    sums = [0.0] * dim
    for emb in embeddings:
        for i, val in enumerate(emb):
            sums[i] += float(val)
    count = float(len(embeddings))
    return [val / count for val in sums]


def _apply_hard_limit(text: str, max_chars: int | None) -> str:
    if not max_chars or len(text) <= max_chars:
        return text
    trimmed = text[:max_chars]
    return trimmed.rsplit(".", 1)[0] + "." if "." in trimmed else trimmed


def _summarize_with_transformers(text: str, length_mode: str, original_word_count: int = None, target_language: str = "turkish") -> str:
    """
    Summarize text using transformer model.
    Target lengths (based on ORIGINAL text):
    - short: 5% of original (min 30, max 60 words)
    - medium: 15% of original (min 150, max 400 words)
    - long: 25% of original (min 500, max 1500 words)
    
    Args:
        text: Text to summarize (usually reduced/merged chunks)
        length_mode: 'short', 'medium', 'long'
        original_word_count: Original full text word count (for percentage calculation)
        target_language: Target language for summary ('turkish', 'english', etc.)
    """
    try:
        summarizer = _get_summarizer()
        
        # Use original word count if provided, otherwise use current text
        if original_word_count is None:
            original_word_count = len(text.split())
        
        # NEW TARGET LENGTHS (based on original text):
        # - short: 30-60 words (article topic, mobile-friendly)
        # - medium: 10% of original
        # - long: 25% of original
        
        if length_mode == "short":
            # SHORT: 30-60 words about what the article is about
            target_words = min(60, max(30, int(original_word_count * 0.05)))
            min_len = 25
            max_len = 80  # Allow up to 80 to ensure we get 30-60
        elif length_mode == "medium":
            # MEDIUM: 10% of original
            target_words = int(original_word_count * 0.10)
            min_len = max(50, int(target_words * 0.6))
            max_len = min(500, int(target_words * 1.5))
        elif length_mode == "long":
            # LONG: 25% of original (multi-pass strategy)
            target_words = int(original_word_count * 0.25)
            min_len = max(100, int(target_words * 0.3))
            max_len = min(400, int(target_words * 0.5))  # Per chunk
        else:
            target_words = int(original_word_count * 0.10)
            min_len = 50
            max_len = 200
        
        current_word_count = len(text.split())
        percentage = int(target_words*100/original_word_count) if original_word_count > 0 else 0
        print(f"[TRANSFORMER] Mode: {length_mode} | Language: {target_language} (ENGLISH ONLY)")
        print(f"[TRANSFORMER]   Original: {original_word_count}w | Current: {current_word_count}w")
        print(f"[TRANSFORMER]   Target: {target_words}w ({percentage}% of original)")
        if length_mode == "short":
            print(f"[TRANSFORMER]   Goal: 30-60 words about article topic (mobile-friendly)")
        elif length_mode == "medium":
            print(f"[TRANSFORMER]   Goal: 10% of original text")
        elif length_mode == "long":
            print(f"[TRANSFORMER]   Goal: 25% of original text")
        print(f"[TRANSFORMER]   Range: min={min_len}w, max={max_len}w")

        MAX_WORDS_PER_CHUNK = 700
        
        # LONG MODE: Her zaman multi-chunk strategy kullan (tek pass yeterli değil)
        if length_mode == "long" and current_word_count > 300:
            # KÜÇÜK CHUNK'lar kullan: Her chunk daha iyi özetlenecek
            chunks = chunk_text(text, chunk_size=1100, chunk_overlap=180)  # Daha büyük chunk'lar + overlap
            print(f"[TRANSFORMER] Long mode: {len(chunks)} chunks (multi-pass strategy)")
            
            # Her chunk'ı özetle VE HEMEN TEMİZLE
            partials = []
            # ÖNEMLİ: Daha fazla chunk işle, her birinden maksimum kelime al
            # Hedef: 10-15 chunk × 150-200w = 1500-3000w → Final 1500w
            # BART max ~350-400w per summary ama genelde 150-200w üretiyor
            
            # Tüm chunk'ları işle (ilk 5 değil, hepsini)
            max_chunks_to_process = min(len(chunks), int(os.getenv("LOCAL_LONG_MAX_CHUNKS", "8")))
            
            for i, chunk in enumerate(chunks[:max_chunks_to_process]):
                try:
                    chunk_words = len(chunk.split())
                    if chunk_words < 40:  # Threshold düşürüldü (50 → 40)
                        continue
                    
                    # Chunk'ı önce temizle (STRICT mode)
                    chunk = _clean_text(chunk, strict_english_only=True)
                    if not _is_mostly_english(chunk):
                        print(f"[TRANSFORMER] Chunk {i+1} skipped: Contains Turkish content")
                        continue
                    
                    # MAKSIMUM özet üret: Her chunk'tan en fazla kelime al
                    # BART limitleri: min=30, max=400 (ideal: 150-250w üretir)
                    chunk_min = max(100, min(200, int(chunk_words * 0.3)))  # Chunk'un %30'u
                    chunk_max = min(400, max(200, int(chunk_words * 0.5)))  # Chunk'un %50'si (BART max)
                    
                    result = summarizer(chunk, min_length=chunk_min, max_length=chunk_max, do_sample=False, truncation=True)
                    partial = _extract_summary_text(result)
                    
                    # ÖNEMLİ: Üretilen partial'ı da temizle! (STRICT mode)
                    partial = _clean_text(partial, strict_english_only=True)
                    
                    # Daha düşük threshold: >30w (50w'dan düşürüldü)
                    if _is_mostly_english(partial) and len(partial.split()) > 30:
                        partials.append(partial)
                        print(f"[TRANSFORMER] Chunk {i+1}/{max_chunks_to_process}: {chunk_words}w → {len(partial.split())}w ✓")
                    else:
                        print(f"[TRANSFORMER] Chunk {i+1} output REJECTED: Contains Turkish or too short")
                        
                except Exception as e:
                    print(f"[TRANSFORMER] Chunk {i+1} failed: {e}")
                    continue
            
            if not partials:
                print(f"[TRANSFORMER] No valid partial summaries, using fallback")
                # Fallback: Sadece İngilizce cümleleri al
                sentences = [s.strip() for s in text.split('.') if _is_mostly_english(s) and len(s.strip()) > 30]
                return '. '.join(sentences[:25]) + '.' if sentences else text[:1500]
            
            # Tüm partial özetleri birleştir (sadece İngilizce olanlar)
            merged_text = " ".join(partials)
            merged_words = len(merged_text.split())
            print(f"[TRANSFORMER] Merged {len(partials)} valid partials: {merged_words}w")
            
            # UZUN ÖZET İÇİN: Final pass YAPMA, merged partials'ı döndür!
            # Çünkü her partial zaten temiz ve İngilizce, tekrar özetlersek kısalır
            if merged_words < target_words * 0.4:  # Çok kısa kaldıysa
                print(f"[TRANSFORMER] Warning: Merged output too short ({merged_words}w < {target_words*0.4}w)")
                print(f"[TRANSFORMER] Tip: Consider using a larger document or adjusting chunk parameters")
            
            # Son bir temizlik yap
            try:
                merged_text = _clean_text(merged_text, strict_english_only=True)
            except:
                pass
            
            final_words = len(merged_text.split())
            print(f"[TRANSFORMER] Long mode final: {final_words}w (target: {target_words}w, {len(partials)} partials)")
            return merged_text
        
        # MEDIUM MODE: Text uzunsa multi-chunk strategy kullan
        if length_mode == "medium" and current_word_count > 500:
            # Medium chunk'lar: 2-3 partial üret, birleştir
            chunks = chunk_text(text, chunk_size=800, chunk_overlap=120)
            print(f"[TRANSFORMER] Medium mode: {len(chunks)} chunks (multi-pass for length target)")
            
            partials = []
            # Her chunk 150-200 kelime üretmeli (2-3 chunk x 180w = 360-540w)
            words_per_chunk = min(200, max(150, target_words // max(2, min(3, len(chunks)))))
            
            for i, chunk in enumerate(chunks[:3]):  # Max 3 chunk al
                try:
                    chunk_words = len(chunk.split())
                    if chunk_words < 40:
                        continue
                    
                    # Temizle
                    chunk = _clean_text(chunk, strict_english_only=True)
                    if not _is_mostly_english(chunk):
                        print(f"[TRANSFORMER] Chunk {i+1} skipped: Turkish content")
                        continue
                    
                    chunk_min = max(120, int(words_per_chunk * 0.7))
                    chunk_max = min(250, int(words_per_chunk * 1.3))
                    
                    result = summarizer(chunk, min_length=chunk_min, max_length=chunk_max, do_sample=False, truncation=True)
                    partial = _extract_summary_text(result)
                    
                    partial = _clean_text(partial, strict_english_only=True)
                    if _is_mostly_english(partial) and len(partial.split()) > 40:
                        partials.append(partial)
                        print(f"[TRANSFORMER] Medium chunk {i+1}: {chunk_words}w → {len(partial.split())}w ✓")
                    
                except Exception as e:
                    print(f"[TRANSFORMER] Medium chunk {i+1} failed: {e}")
                    continue
            
            if len(partials) >= 2:  # En az 2 partial varsa birleştir
                merged_text = " ".join(partials)
                try:
                    merged_text = _clean_text(merged_text, strict_english_only=True)
                except:
                    pass
                final_words = len(merged_text.split())
                print(f"[TRANSFORMER] Medium mode final: {final_words}w (merged {len(partials)} partials)")
                return merged_text
            # Eğer partial yetersizse, tek pass'e düş
        
        # SHORT/MEDIUM (kısa text): If text fits in one chunk, directly summarize
        if current_word_count <= MAX_WORDS_PER_CHUNK:
            # Clean input text if English is selected
            if target_language == "english":
                text = _clean_text(text, strict_english_only=True)
            
            # Standard BART pipeline
            result = summarizer(text, min_length=min_len, max_length=max_len, do_sample=False, truncation=True)
            summary = _extract_summary_text(result)
            
            # Clean output if English is selected
            if target_language == "english":
                summary = _clean_text(summary, strict_english_only=True)
                # Verify it's actually English
                if not _is_mostly_english(summary) and len(summary) > 20:
                    print(f"[TRANSFORMER] WARNING: Summary contains Turkish, re-cleaning...")
                    # Try to extract only English sentences
                    sentences = [s.strip() for s in summary.split('.') if _is_mostly_english(s) and len(s.strip()) > 15]
                    summary = '. '.join(sentences) + '.' if sentences else summary
            
            # Log final summary length (no truncation applied)
            print(f"[TRANSFORMER] Single pass: {len(summary.split())}w (target: {target_words}w)")
            return summary
        
        # ORTA/KISA METIN İÇİN Multi-chunk strategy (long mode değil)
        # For long text: calculate what % to keep per chunk
        # Goal: reduce text to ~3x target (daha fazla içerik koru), then final summary to target
        # Medium için daha gevşek bir reduction ratio kullan
        target_reduction_ratio = min(0.8, (target_words * 3.5) / current_word_count)  # 2.5 → 3.5
        print(f"[TRANSFORMER] Multi-chunk strategy: reduce each chunk to {target_reduction_ratio:.1%}")
        
        chunks = chunk_text(text, chunk_size=900, chunk_overlap=100)
        print(f"[TRANSFORMER] Split into {len(chunks)} chunks")
        
        partials: List[str] = []
        for i, chunk in enumerate(chunks):
            try:
                # Clean chunk if English mode
                if target_language == "english":
                    chunk = _clean_text(chunk, strict_english_only=True)
                    if not _is_mostly_english(chunk):
                        print(f"[TRANSFORMER] Chunk {i+1} skipped: Contains Turkish")
                        continue
                
                chunk_words = len(chunk.split())
                # Target for this chunk based on reduction ratio
                chunk_target = int(chunk_words * target_reduction_ratio)
                chunk_max = max(30, int(chunk_target * 1.3))
                chunk_min = max(10, int(chunk_max * 0.6))
                
                # Chunk summarization
                result = summarizer(chunk, min_length=chunk_min, max_length=chunk_max, do_sample=False, truncation=True)
                partial_summary = _extract_summary_text(result)
                
                # Clean partial if English mode
                if target_language == "english":
                    partial_summary = _clean_text(partial_summary, strict_english_only=True)
                    if not _is_mostly_english(partial_summary):
                        print(f"[TRANSFORMER] Chunk {i+1} output rejected: Contains Turkish")
                        continue
                
                partials.append(partial_summary)
                print(f"[TRANSFORMER] Chunk {i+1}/{len(chunks)}: {chunk_words}w → {len(partial_summary.split())}w")
            except Exception as chunk_err:
                print(f"[TRANSFORMER] ERROR on chunk {i+1}: {chunk_err}")
                # Fallback: keep proportional amount
                fallback_chars = int(len(chunk) * target_reduction_ratio)
                fallback_text = chunk[:fallback_chars].rsplit('.', 1)[0] + '.' if '.' in chunk[:fallback_chars] else chunk[:fallback_chars]
                partials.append(fallback_text)

        # Merge and final summary to exact target
        merged = " ".join(partials)
        
        # Clean merged text if English mode
        if target_language == "english":
            merged = _clean_text(merged, strict_english_only=True)
        
        merged_words = len(merged.split())
        print(f"[TRANSFORMER] Merged: {merged_words}w → target: {target_words}w")
        
        # Final pass SADECE çok gerekirse yap (merged çok uzunsa veya target'a çok uzaksa)
        # Medium/short için merged zaten yaklaşık doğru boyutta olmalı
        if merged_words <= target_words * 1.3:  # Target'a yeterince yakınsa
            # Final pass yapma, direkt döndür
            print(f"[TRANSFORMER] Merged close enough to target, no final pass needed")
            final_summary = merged
        elif merged_words <= MAX_WORDS_PER_CHUNK:
            # Final pass yap
            result = summarizer(merged, min_length=min_len, max_length=max_len, do_sample=False, truncation=True)
            final_summary = _extract_summary_text(result)
            
            # Clean final summary if English mode
            if target_language == "english":
                final_summary = _clean_text(final_summary, strict_english_only=True)
        else:
            # Still too long, take most relevant sentences
            sentences = merged.split('. ')
            
            # Filter English sentences if English mode
            if target_language == "english":
                sentences = [s for s in sentences if _is_mostly_english(s) and len(s.strip()) > 15]
            
            target_sentences = max(3, int(len(sentences) * (target_words / merged_words)))
            final_summary = '. '.join(sentences[:target_sentences]) + '.'
        
        # Truncate fonksiyonunu kaldırdık - merged zaten doğru boyutta
        final_words = len(final_summary.split())
        print(f"[TRANSFORMER] Final: {final_words}w ({int(final_words*100/original_word_count)}% of original)")
        return final_summary
        
    except Exception as e:
        print(f"[TRANSFORMER ERROR] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        # Fallback: simple cut
        target_percent = 0.03 if length_mode == "short" else (0.10 if length_mode == "medium" else 0.25)
        target_chars = int(len(text) * target_percent)
        fallback = text[:target_chars].rsplit('.', 1)[0] + '.' if '.' in text[:target_chars] else text[:target_chars]
        return fallback


def summarize_with_embeddings(
    text: str,
    owner_id: int,
    title: str,
    length_mode: str,
    max_chars: int,
    target_language: str = "english",
    source_language: str = "auto",
    db: Optional[Session] = None,
    use_multilingual: bool = True,
) -> str:
    """
    Main summarization function with context-aware and multilingual support.
    
    NEW FEATURES V3.0 (MULTILINGUAL):
    - ✅ 50+ languages supported via mBART-50
    - ✅ Auto language detection
    - ✅ Cross-lingual summarization (e.g., Turkish → English)
    - ✅ Database context integration
    - ✅ Author information removal
    
    SUPPORTED LANGUAGES: tr, en, de, fr, es, it, ru, ar, ja, ko, zh, nl, pt, hi, and 35+ more
    
    LENGTH TARGETS:
    - short: 30-60 words (what the article is about, mobile-friendly)
    - medium: 10% of original text
    - long: 25% of original text
    
    Args:
        text: Document text to summarize
        owner_id: User ID
        title: Document title
        length_mode: 'short', 'medium', or 'long'
        max_chars: Maximum character limit (fallback)
        target_language: Target language for summary (e.g., 'en', 'tr', 'de')
        source_language: Source language of document ('auto' for detection)
        db: Database session for context loading (optional)
        use_multilingual: Use mBART-50 for multilingual support (default: True)
    """
    print(f"\n{'='*60}")
    print(f"[SUMMARY] New request: {length_mode} mode")
    print(f"[SUMMARY] Input: {len(text)} chars, {len(text.split())} words")

    provider = os.getenv("AI_PROVIDER", "local").strip().lower()
    if provider not in {"local", "external"}:
        provider = "local"
    print(f"[SUMMARY] Provider: {provider}")
    
    # PHASE 0: Language Detection
    if source_language == "auto":
        detected_lang = detect_language(text)
        source_language = detected_lang
        print(f"[SUMMARY] Auto-detected source language: {LANGUAGE_NAMES.get(source_language, source_language)}")
    else:
        print(f"[SUMMARY] Source language: {LANGUAGE_NAMES.get(source_language, source_language)}")
    
    print(f"[SUMMARY] Target language: {LANGUAGE_NAMES.get(target_language, target_language)}")
    
    # Check if multilingual model is needed
    needs_multilingual = (
        use_multilingual and 
        (source_language != 'en' or target_language != 'en') and
        is_language_supported(source_language) and
        is_language_supported(target_language)
    )
    
    if needs_multilingual:
        print(f"[SUMMARY] Using mBART-50 for multilingual summarization")
    else:
        print(f"[SUMMARY] Using BART for English-only summarization")
    
    
    # PHASE 1: Clean text (only for English mode, others keep original)
    if source_language == 'en' or not use_multilingual:
        print(f"[SUMMARY] Phase 1: Cleaning English text (removing author info, non-English content)...")
        text = _clean_text(text, strict_english_only=True)
        print(f"[SUMMARY] After cleaning: {len(text)} chars, {len(text.split())} words")
        
        if len(text) < 100:
            print(f"[SUMMARY ERROR] Text too short after cleaning (<100 chars)")
            return "Error: Document contains insufficient English content for summarization."
    else:
        print(f"[SUMMARY] Phase 1: Skipping English-only cleaning (multilingual mode)")
    
    # PHASE 2: Load context from database (merge similar previous documents)
    print(f"[SUMMARY] Phase 2: Loading user context from database...")
    text = _get_user_context_from_db(db, owner_id, text)
    
    # PHASE 3: Skip author sections and find main content
    print(f"[SUMMARY] Phase 3: Identifying main content...")
    main_content_markers = ['Abstract', 'Introduction', 'Background', 'Overview', 'Summary', 'ABSTRACT', 'INTRODUCTION']
    for marker in main_content_markers:
        marker_pos = text.find(marker)
        if marker_pos > 0 and marker_pos < len(text) * 0.3:  # Found in first 30%
            text = text[marker_pos + len(marker):]
            print(f"[SUMMARY] Skipped to '{marker}' section")
            break
    
    # PHASE 4: Create chunks
    print(f"[SUMMARY] Phase 4: Creating text chunks...")
    chunks = chunk_text(text)
    if not chunks:
        print(f"[SUMMARY] No chunks created, using fallback")
        return summarize_text_simple(text, max_chars=max_chars, length_mode=length_mode)

    # Store original text info for percentage calculation
    original_word_count = len(text.split())

    # External API path (OpenAI-compatible). Falls back to local if any failure occurs.
    if provider == "external":
        try:
            print("[SUMMARY] Using external API model")
            ext_summary = _summarize_with_external_api(
                text=text,
                source_language=source_language,
                target_language=target_language,
                length_mode=length_mode,
                original_word_count=original_word_count,
            )
            final = _apply_hard_limit(ext_summary, max_chars)
            print(f"[SUMMARY] ✓ External success: {len(final)} chars, {len(final.split())} words")
            print(f"{'='*60}\n")
            return final
        except Exception as ext_err:
            print(f"[SUMMARY WARNING] External model failed, fallback path: {ext_err}")

            # Long mode can exceed proxy timeout when falling back to local multi-pass.
            # Retry once with a reduced target, then fail fast to simple summarization.
            if length_mode == "long":
                try:
                    print("[SUMMARY] Retrying external call in medium mode for long request")
                    ext_retry = _summarize_with_external_api(
                        text=text,
                        source_language=source_language,
                        target_language=target_language,
                        length_mode="medium",
                        original_word_count=original_word_count,
                    )
                    final_retry = _apply_hard_limit(ext_retry, max_chars)
                    print(f"[SUMMARY] ✓ External retry success: {len(final_retry)} chars, {len(final_retry.split())} words")
                    print(f"{'='*60}\n")
                    return final_retry
                except Exception as retry_err:
                    print(f"[SUMMARY WARNING] External retry failed, using fast fallback: {retry_err}")
                    quick = summarize_text_simple(text, max_chars=max_chars, length_mode="medium")
                    final_quick = _apply_hard_limit(quick, max_chars)
                    print(f"[SUMMARY] ✓ Fast fallback success: {len(final_quick)} chars, {len(final_quick.split())} words")
                    print(f"{'='*60}\n")
                    return final_quick
    
    # PHASE 5: Summarization (choose appropriate model)
    print(f"[SUMMARY] Phase 5: Generating summary...")
    print(f"[SUMMARY] Length mode: {length_mode}")
    if length_mode == "short":
        print(f"[SUMMARY]   → Target: 30-60 words (what the article is about)")
    elif length_mode == "medium":
        print(f"[SUMMARY]   → Target: ~{int(original_word_count * 0.10)} words (10% of original)")
    elif length_mode == "long":
        print(f"[SUMMARY]   → Target: ~{int(original_word_count * 0.25)} words (25% of original)")
    
    try:
        # Choose summarization strategy
        if needs_multilingual:
            # Use mBART-50 for multilingual summarization
            print(f"[SUMMARY] Using mBART-50 multilingual model")
            summary = summarize_multilingual(
                text=text,
                source_lang=source_language,
                target_lang=target_language,
                length_mode=length_mode,
                original_word_count=original_word_count
            )
        else:
            # Use BART for English-only (faster)
            print(f"[SUMMARY] Using BART English-only model")
            # Convert language codes to full names for compatibility
            target_lang_name = "english" if target_language == "en" else target_language
            summary = _summarize_with_transformers(
                text, 
                length_mode, 
                original_word_count, 
                target_lang_name
            )
            
            # Verify output is English (only for English mode)
            if target_language == 'en' and not _is_mostly_english(summary):
                print(f"[SUMMARY WARNING] Output contains non-English content, re-cleaning...")
                summary = _clean_text(summary, strict_english_only=True)
        
        # Apply hard character limit as final fallback
        final = _apply_hard_limit(summary, max_chars)
        final_words = len(final.split())
        final_chars = len(final)
        
        print(f"[SUMMARY] ✓ Success: {final_chars} chars, {final_words} words")
        print(f"{'='*60}\n")
        return final
        
    except Exception as e:
        print(f"[SUMMARY] ✗ Summarization failed: {e}")
        traceback.print_exc()
        summary = summarize_text_simple(text, max_chars=max_chars, length_mode=length_mode)
        return _apply_hard_limit(summary, max_chars)


def _summarize_with_chroma(
    text: str,
    chunks: List[str],
    owner_id: int,
    title: str,
    length_mode: str,
    max_chars: int,
    original_word_count: int,
    target_language: str = "turkish"
) -> str:
    """Chroma-based summarization with embedding similarity"""
    # Step 1: Embedding
    model = _get_embedding_model()
    embeddings = model.encode(chunks, normalize_embeddings=True).tolist()
    print(f"[CHROMA] Embeddings created: {len(embeddings)} vectors")

    # Step 2: Store in Chroma
    client = _get_chroma_client()
    if client is None:
        raise RuntimeError("Chroma client not available")
    
    collection = _get_chroma_collection(client)
    if collection is None:
        raise RuntimeError("Chroma collection not available")
    
    print(f"[CHROMA] Connected to collection")

    doc_id = str(uuid.uuid4())
    ids = [f"{doc_id}-{index}" for index in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "owner_id": owner_id,
            "title": title,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"[CHROMA] Stored {len(chunks)} chunks")

    # Step 3: Find most similar chunks
    query_embedding = _mean_embedding(embeddings)
    n_results = min(8, len(chunks))
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"$and": [{"doc_id": doc_id}, {"owner_id": owner_id}]},
    )
    top_chunks = results.get("documents", [[]])[0]
    print(f"[CHROMA] Retrieved top {len(top_chunks)} similar chunks")
    
    # Step 4: Merge similar chunks into coherent text
    reduced_text = "\n".join(top_chunks) if top_chunks else "\n".join(chunks)
    print(f"[CHROMA] Merged text: {len(reduced_text)} chars, {len(reduced_text.split())} words")

    # Step 5: Generate actual summary using transformer
    summary = _summarize_with_transformers(reduced_text, length_mode, original_word_count=original_word_count, target_language=target_language)
    
    final = _apply_hard_limit(summary, max_chars)
    print(f"[CHROMA] Final: {len(final)} chars")
    return final