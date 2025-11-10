# app/services/ai_service.py
from typing import Tuple, List
import yake

def summarize_text_simple(text: str, max_chars: int = 800) -> str:
   
    if len(text) <= max_chars:
        return text

    return text[:max_chars].rsplit('.', 1)[0] + '.'

def extract_keywords_yake(text: str, max_keywords: int = 8) -> List[str]:
    try:
        kw_extractor = yake.KeywordExtractor(lan="en", top=max_keywords)
        keywords = kw_extractor.extract_keywords(text)
        return [k for k, s in keywords]
    except Exception:
        tokens = text.split()
        frequent = sorted(set(tokens), key=lambda t: -tokens.count(t))
        return frequent[:max_keywords]
