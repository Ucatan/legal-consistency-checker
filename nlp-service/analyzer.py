import re
from typing import List, Dict, Any
from vector_db import LegalVectorDB  # ← ИМПОРТ QDRANT-ИНТЕГРАЦИИ

# === 1. ПАРСИНГ СТАТЕЙ (без изменений) ===
def extract_articles(text: str) -> Dict[str, str]:
    """Извлекает статьи: {номер: полный текст}"""
    articles = {}
    current_num = None
    current_lines = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Ищем начало статьи: "Статья 5.", "Ст. 10.1"
        match = re.search(r'(?:^|\s)(?:Статья|Ст\.?)\s*(\d+(?:\.\d+)?)(?:\.|\s|$)', line, re.IGNORECASE)
        if match:
            if current_num:
                articles[current_num] = " ".join(current_lines)
            current_num = match.group(1)
            current_lines = [line]
        elif current_num:
            current_lines.append(line)

    if current_num:
        articles[current_num] = " ".join(current_lines)

    return articles

# === 2. ПРОВЕРКА ССЫЛОК (без изменений) ===
def find_missing_references(text: str, articles: Dict[str, str]) -> List[Dict]:
    issues = []
    # Ищем ссылки: ст.5, статья 10, п.3
    refs = re.findall(r'(?:стать[ия]|ст\.?|пункт|п\.?)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)

    for ref in set(refs):
        if ref not in articles:
            issues.append({
                "type": "missing_reference",
                "description": f"Ссылка на несуществующую статью «ст.{ref}»",
                "location": f"ссылка на ст.{ref}",
                "severity": "high"
            })
    return issues

# === 3. ГЛАВНЫЙ АНАЛИЗАТОР (С ИНТЕГРАЦИЕЙ QDRANT) ===
_vector_db = None

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        _vector_db = LegalVectorDB()  # ← ИНИЦИАЛИЗАЦИЯ QDRANT-КЛИЕНТА
    return _vector_db

def analyze_legal_text(text: str) -> List[Dict]:
    """Анализ с использованием Qdrant вместо локальных эмбеддингов"""
    articles = extract_articles(text)

    # 1. Индексируем статьи в Qdrant
    db = get_vector_db()
    db.index_articles(articles)

    # 2. Собираем проблемы
    issues = []
    issues.extend(find_missing_references(text, articles))

    # 3. Ищем противоречия через Qdrant (замена find_contradictions)
    for article_num, content in articles.items():
        contradictions = db.find_contradictions(content, article_num)
        for match in contradictions:
            if match["score"] > 0.65:  # Порог для ФЗ-152
                issues.append({
                    "type": "semantic_contradiction",
                    "description": f"Противоречие между ст.{article_num} и ст.{match['article_num']} (сходство: {match['score']:.2f})",
                    "location": f"ст.{article_num} ↔ ст.{match['article_num']}",
                    "severity": "high" if match["score"] > 0.8 else "medium"
                })

    return issues