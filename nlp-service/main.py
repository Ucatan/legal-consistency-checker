from fileinput import filename

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import re

app = FastAPI(
    title="Legal Consistency Checker — NLP Service",
    description="Анализ юридических документов на противоречия и логические несоответствия",
    version="0.1.0"
)


class Issue(BaseModel):
    type: str
    description: str
    location: Optional[str] = None
    severity: str = "medium"


class AnalysisResult(BaseModel):
    document: str
    issues: List[Issue]
    status: str = "completed"


@app.get("/health")
def health():
    return {"status": "ok", "service": "nlp"}


def analyze_legal_text(text: str):
    issues = []

    # 1. Извлекаем статьи с нумерацией: "Статья 5.", "Ст. 10.1"
    article_lines = []
    for i, line in enumerate(text.splitlines()):
        if re.search(r'^\s*(Статья|Ст\.)\s+\d', line, re.IGNORECASE):
            num = re.search(r'(Статья|Ст\.)\s+(\d+(?:\.\d+)?)', line, re.IGNORECASE)
            if num:
                article_lines.append((num.group(2), i+1, line.strip()))

    articles = {num: line_num for num, line_num, _ in article_lines}

    # 2. Ищем ссылки: "ст. 5", "пункт 3 статьи 7", "в ред. ФЗ №152"
    all_refs = []
    for i, line in enumerate(text.splitlines()):
        # Шаблоны ссылок
        patterns = [
            r'ст\.?\s*(\d+(?:\.\d+)?)',           # ст.5, ст 5.1
            r'пункт\s+(\d+)\s+стать[ии]',          # пункт 3 статьи
            r'стать[ия]\s+(\d+(?:\.\d+)?)',        # статья 10
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                ref = match.group(1)
                all_refs.append((ref, i+1))

    # 3. Проверка: ссылка → несуществующая статья
    for ref, line_num in all_refs:
        if ref not in articles:
            issues.append(Issue(
                type="missing_reference",
                description=f"Ссылка на несуществующую статью «ст.{ref}»",
                location=f"строка {line_num}",
                severity="high"
            ))

    # 4. Поиск противоречий по смыслу (улучшенный)
    # Контекст: собираем текст по статьям
    article_texts = {}
    current_article = None
    for line in text.splitlines():
        art_match = re.match(r'^\s*(Статья|Ст\.)\s+(\d+(?:\.\d+)?)', line, re.IGNORECASE)
        if art_match:
            current_article = art_match.group(2)
            article_texts[current_article] = line
        elif current_article:
            article_texts[current_article] += " " + line.strip()

    # Проверяем пары статей на противоречия
    contradictions = [
        ("согласие субъекта", "без согласия субъекта"),
        ("обязан получить согласие", "возможно без согласия"),
        ("недопустимо", "допускается"),
    ]

    articles_list = list(article_texts.keys())
    for i in range(len(articles_list)):
        for j in range(i+1, len(articles_list)):
            a1, a2 = articles_list[i], articles_list[j]
            t1, t2 = article_texts[a1].lower(), article_texts[a2].lower()
            for phrase1, phrase2 in contradictions:
                if phrase1 in t1 and phrase2 in t2:
                    issues.append(Issue(
                        type="semantic_contradiction",
                        description=f"Противоречие между ст.{a1} и ст.{a2}: «{phrase1}» ↔ «{phrase2}»",
                        location=f"ст.{a1} ↔ ст.{a2}",
                        severity="medium"
                    ))

    return issues

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_document(file: UploadFile = File(...)):
    # ... ваш анализ ...
    return AnalysisResult(
        document=filename,
        issues=[
            Issue(
                type="missing_reference",
                description="Ссылка на несуществующую статью",
                location="ст. 99",
                severity="high"
            )
        ]
    )
