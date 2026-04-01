#!/usr/bin/env python3
"""
Multilingual Summarization Test Script
Tests various language combinations and modes
"""

import sys
sys.path.append('.')

from app.services.ai_service import (
    summarize_multilingual,
    detect_language,
    is_language_supported,
    get_supported_languages,
    LANGUAGE_NAMES
)

# Test texts in different languages
TEST_TEXTS = {
    'en': """
Artificial intelligence represents one of the most significant technological 
revolutions of our time. Machine learning algorithms are transforming industries 
from healthcare to finance, enabling computers to learn from data and make 
intelligent decisions. Deep learning, powered by neural networks, has achieved 
remarkable breakthroughs in image recognition, natural language processing, 
and game playing. As AI continues to advance, it promises to reshape our world 
in unprecedented ways, while also raising important questions about ethics, 
privacy, and the future of work.
""",
    
    'tr': """
Yapay zeka, çağımızın en önemli teknolojik devrimlerinden birini temsil etmektedir. 
Makine öğrenmesi algoritmaları sağlıktan finansa kadar birçok sektörü dönüştürmekte, 
bilgisayarların verilerden öğrenmesini ve akıllı kararlar almasını sağlamaktadır. 
Yapay sinir ağları tarafından desteklenen derin öğrenme, görüntü tanıma, doğal dil 
işleme ve oyun oynamada dikkate değer başarılar elde etmiştir. Yapay zeka gelişmeye 
devam ettikçe, dünyamızı benzeri görülmemiş şekillerde yeniden şekillendirmeyi 
vaat ederken etik, gizlilik ve işin geleceği hakkında önemli sorular da ortaya 
çıkarmaktadır.
""",
    
    'de': """
Künstliche Intelligenz stellt eine der bedeutendsten technologischen Revolutionen 
unserer Zeit dar. Algorithmen des maschinellen Lernens transformieren Industrien 
vom Gesundheitswesen bis zum Finanzwesen und ermöglichen es Computern, aus Daten 
zu lernen und intelligente Entscheidungen zu treffen. Deep Learning, angetrieben 
durch neuronale Netze, hat bemerkenswerte Durchbrüche in der Bilderkennung, 
natürlichen Sprachverarbeitung und beim Spielen von Spielen erzielt.
""",
    
    'fr': """
L'intelligence artificielle représente l'une des révolutions technologiques les 
plus importantes de notre époque. Les algorithmes d'apprentissage automatique 
transforment les industries de la santé à la finance, permettant aux ordinateurs 
d'apprendre à partir des données et de prendre des décisions intelligentes. 
L'apprentissage profond, alimenté par les réseaux de neurones, a réalisé des 
percées remarquables dans la reconnaissance d'images, le traitement du langage 
naturel et les jeux.
""",
    
    'es': """
La inteligencia artificial representa una de las revoluciones tecnológicas más 
significativas de nuestro tiempo. Los algoritmos de aprendizaje automático están 
transformando industrias desde la salud hasta las finanzas, permitiendo que las 
computadoras aprendan de los datos y tomen decisiones inteligentes. El aprendizaje 
profundo, impulsado por redes neuronales, ha logrado avances notables en el 
reconocimiento de imágenes, el procesamiento del lenguaje natural y los juegos.
"""
}


def test_language_detection():
    """Test automatic language detection"""
    print("\n" + "="*80)
    print("TEST 1: Language Detection")
    print("="*80)
    
    for lang_code, text in TEST_TEXTS.items():
        detected = detect_language(text)
        expected = lang_code
        status = "✅ PASS" if detected == expected else "❌ FAIL"
        
        print(f"\nExpected: {expected} ({LANGUAGE_NAMES.get(expected, 'Unknown')})")
        print(f"Detected: {detected} ({LANGUAGE_NAMES.get(detected, 'Unknown')})")
        print(f"Status: {status}")


def test_cross_lingual_summarization():
    """Test cross-lingual summarization (e.g., Turkish → English)"""
    print("\n" + "="*80)
    print("TEST 2: Cross-Lingual Summarization")
    print("="*80)
    
    test_cases = [
        {'source': 'tr', 'target': 'en', 'name': 'Turkish → English'},
        {'source': 'en', 'target': 'tr', 'name': 'English → Turkish'},
        {'source': 'de', 'target': 'fr', 'name': 'German → French'},
        {'source': 'fr', 'target': 'es', 'name': 'French → Spanish'},
    ]
    
    for case in test_cases:
        source_lang = case['source']
        target_lang = case['target']
        
        if source_lang not in TEST_TEXTS:
            print(f"\n⚠️  SKIP: {case['name']} (no test text)")
            continue
        
        print(f"\n{'─'*80}")
        print(f"Test Case: {case['name']}")
        print(f"{'─'*80}")
        
        text = TEST_TEXTS[source_lang]
        
        try:
            summary = summarize_multilingual(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                length_mode='short'
            )
            
            summary_words = len(summary.split())
            print(f"\n✅ SUCCESS")
            print(f"Original: {len(text.split())} words")
            print(f"Summary: {summary_words} words")
            print(f"\nSummary text:")
            print(f"  {summary}")
            
            # Verify length is within expected range (30-60 words for short mode)
            if 20 <= summary_words <= 80:
                print(f"\n  Length check: ✅ PASS ({summary_words} words in range 20-80)")
            else:
                print(f"\n  Length check: ⚠️  WARN ({summary_words} words outside range 20-80)")
            
        except Exception as e:
            print(f"\n❌ FAILED: {e}")


def test_same_language_summarization():
    """Test summarization in the same language"""
    print("\n" + "="*80)
    print("TEST 3: Same-Language Summarization")
    print("="*80)
    
    test_cases = [
        {'lang': 'en', 'name': 'English → English'},
        {'lang': 'tr', 'name': 'Turkish → Turkish'},
        {'lang': 'de', 'name': 'German → German'},
    ]
    
    for case in test_cases:
        lang = case['lang']
        
        if lang not in TEST_TEXTS:
            print(f"\n⚠️  SKIP: {case['name']} (no test text)")
            continue
        
        print(f"\n{'─'*80}")
        print(f"Test Case: {case['name']}")
        print(f"{'─'*80}")
        
        text = TEST_TEXTS[lang]
        
        try:
            summary = summarize_multilingual(
                text=text,
                source_lang=lang,
                target_lang=lang,
                length_mode='short'
            )
            
            summary_words = len(summary.split())
            print(f"\n✅ SUCCESS")
            print(f"Original: {len(text.split())} words")
            print(f"Summary: {summary_words} words")
            print(f"\nSummary text:")
            print(f"  {summary[:200]}...")
            
        except Exception as e:
            print(f"\n❌ FAILED: {e}")


def test_length_modes():
    """Test different length modes (short, medium, long)"""
    print("\n" + "="*80)
    print("TEST 4: Length Modes")
    print("="*80)
    
    # Use a longer text for testing
    long_text = TEST_TEXTS['en'] * 10  # ~1000 words
    
    modes = ['short', 'medium', 'long']
    
    for mode in modes:
        print(f"\n{'─'*80}")
        print(f"Mode: {mode.upper()}")
        print(f"{'─'*80}")
        
        try:
            summary = summarize_multilingual(
                text=long_text,
                source_lang='en',
                target_lang='en',
                length_mode=mode,
                original_word_count=len(long_text.split())
            )
            
            summary_words = len(summary.split())
            original_words = len(long_text.split())
            percentage = int(summary_words * 100 / original_words)
            
            print(f"✅ SUCCESS")
            print(f"Original: {original_words} words")
            print(f"Summary: {summary_words} words ({percentage}% of original)")
            
            # Expected ranges
            if mode == 'short':
                expected = "30-60 words"
                in_range = 30 <= summary_words <= 60
            elif mode == 'medium':
                expected = "~10% of original"
                in_range = 0.05 <= summary_words / original_words <= 0.15
            elif mode == 'long':
                expected = "~25% of original"
                in_range = 0.15 <= summary_words / original_words <= 0.35
            
            status = "✅ PASS" if in_range else "⚠️  OUTSIDE RANGE"
            print(f"Expected: {expected}")
            print(f"Status: {status}")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")


def test_supported_languages():
    """Test getting list of supported languages"""
    print("\n" + "="*80)
    print("TEST 5: Supported Languages")
    print("="*80)
    
    try:
        languages = get_supported_languages()
        
        print(f"\n✅ Total supported languages: {len(languages)}")
        print(f"\nSample languages (first 10):")
        
        for lang in languages[:10]:
            supported = "✅" if is_language_supported(lang['code']) else "❌"
            print(f"  {supported} {lang['name']} ({lang['code']}) - mBART: {lang['mbart_code']}")
        
        print(f"\n  ... and {len(languages) - 10} more languages")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("MULTILINGUAL SUMMARIZATION TEST SUITE")
    print("="*80)
    
    try:
        # Run tests
        test_language_detection()
        test_supported_languages()
        test_same_language_summarization()
        test_cross_lingual_summarization()
        test_length_modes()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
