from typing import List, Dict

def analyze_legal_text(text: str) -> List[Dict]:
    print(f"🔍 Анализируем текст длиной {len(text)} символов")
    print(f"Текст: '{text}'")

    issues = []
    text_lower = text.lower()
    print(f"В нижнем регистре: '{text_lower}'")

    # Проверка ключевых слов
    print(f"'согласие' in text? { 'согласие' in text_lower }")
    print(f"'без согласия' in text? { 'без согласия' in text_lower }")

    if "согласие" in text_lower and "без согласия" in text_lower:
        issues.append({
            "type": "semantic_contradiction",
            "description": "ТЕСТ: согласие + без согласия",
            "location": "документ",
            "severity": "high"
        })

    if "ст.99" in text_lower:
        issues.append({
            "type": "missing_reference",
            "description": "ТЕСТ: ст.99",
            "location": "документ",
            "severity": "high"
        })

    print(f"Найдено проблем: {len(issues)}")
    return issues