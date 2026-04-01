#!/usr/bin/env python3
"""
Özet Uzunluk Test Script
Farklı mod ve metin uzunluklarında özetleme performansını test eder.
"""

import sys
sys.path.append('.')

from app.services.ai_service import summarize_with_embeddings

# Test metinleri (farklı uzunluklar)
TEST_TEXTS = {
    "short": """
Artificial intelligence has revolutionized many aspects of modern life. 
From healthcare to transportation, AI systems are becoming increasingly sophisticated.
Machine learning algorithms can now recognize patterns in data that humans might miss.
Deep learning, a subset of machine learning, uses neural networks to process information.
These technologies continue to advance rapidly, promising exciting developments ahead.
""" * 10,  # ~500 words
    
    "medium": """
The field of artificial intelligence (AI) has seen remarkable progress in recent years, 
transforming industries and reshaping how we interact with technology. Machine learning, 
a core component of AI, enables computers to learn from data without being explicitly 
programmed. Deep learning, which uses artificial neural networks inspired by the human brain, 
has achieved breakthrough results in areas like image recognition, natural language processing, 
and game playing. These advancements have led to practical applications in healthcare, 
where AI assists in disease diagnosis and drug discovery, in autonomous vehicles that 
can navigate complex environments, and in virtual assistants that understand and respond 
to human speech. Despite these successes, challenges remain, including ensuring AI systems 
are fair, transparent, and aligned with human values. Researchers are working on developing 
more efficient algorithms, creating AI that can explain its decisions, and establishing 
ethical guidelines for AI development and deployment. As AI continues to evolve, it promises 
to unlock new possibilities while also requiring careful consideration of its societal impact.
""" * 50,  # ~5000 words
    
    "long": """
The rapid advancement of artificial intelligence (AI) represents one of the most significant 
technological revolutions of the 21st century. This transformation encompasses multiple 
disciplines, from computer science and mathematics to cognitive psychology and neuroscience. 
At its core, AI seeks to create machines capable of performing tasks that typically require 
human intelligence, such as visual perception, speech recognition, decision-making, and 
language translation. The field has evolved through several paradigms, from early rule-based 
expert systems to modern machine learning approaches that can automatically improve through 
experience. Deep learning, a particularly powerful branch of machine learning, utilizes 
artificial neural networks with multiple layers to model complex patterns in large datasets.
""" * 100  # ~10000 words
}

def test_summarization(text: str, length_mode: str, text_name: str):
    """Test summarization with specific parameters"""
    print("\n" + "="*80)
    print(f"TEST: {text_name.upper()} | Mode: {length_mode.upper()}")
    print("="*80)
    
    original_words = len(text.split())
    print(f"Original text: {original_words} words")
    
    try:
        summary = summarize_with_embeddings(
            text=text,
            owner_id=1,
            title=f"Test {text_name} {length_mode}",
            length_mode=length_mode,
            max_chars=10000,
            target_language="english"
        )
        
        summary_words = len(summary.split())
        percentage = int(summary_words * 100 / original_words)
        
        print(f"\n[RESULT]")
        print(f"  Summary length: {summary_words} words ({percentage}% of original)")
        print(f"  First 100 chars: {summary[:100]}...")
        
        # Beklenen aralıklar
        expected = {
            "short": (30, 60),
            "medium": (150, 400),
            "long": (500, 1500)
        }
        
        min_exp, max_exp = expected.get(length_mode, (0, 99999))
        if min_exp <= summary_words <= max_exp:
            print(f"  ✅ PASS: Within expected range ({min_exp}-{max_exp} words)")
        else:
            print(f"  ❌ FAIL: Outside expected range ({min_exp}-{max_exp} words)")
        
        return summary_words
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Run all tests"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║          Özet Uzunluk Test Script                         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    # Test tüm kombinasyonlar
    for text_name, text in TEST_TEXTS.items():
        for mode in ["short", "medium", "long"]:
            key = f"{text_name}_{mode}"
            results[key] = test_summarization(text, mode, text_name)
    
    # Özet rapor
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    
    for key, words in results.items():
        text_name, mode = key.split("_")
        expected = {"short": (30, 60), "medium": (150, 400), "long": (500, 1500)}
        min_exp, max_exp = expected[mode]
        status = "✅ PASS" if min_exp <= words <= max_exp else "❌ FAIL"
        print(f"{status} | {text_name:6} | {mode:6} | {words:4} words (expected: {min_exp}-{max_exp})")
    
    print("="*80)
    print("\n✅ Test tamamlandı!")


if __name__ == "__main__":
    main()
