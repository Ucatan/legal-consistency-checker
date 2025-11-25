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

    # 1. Находим все статьи: Статья 1, ст.5, Ст. 10.1
    article_pattern = r'(?:Статья|Ст\.?)\s+(\d+(?:\.\d+)?)'
    articles = set(re.findall(article_pattern, text, re.IGNORECASE))

    # 2. Находим ссылки: ст. 5, п. 3, статья 7
    ref_pattern = r'(?:стать[ия]|ст\.?|пункт|п\.?)\s*(\d+(?:\.\d+)?)'
    references = re.findall(ref_pattern, text, re.IGNORECASE)

    # 3. Проверяем ссылки на несуществующие статьи
    for ref in set(references):
        if ref not in articles:
            issues.append(Issue(
                type="missing_reference",
                description=f"Ссылка на несуществующую статью/пункт «ст.{ref}»",
                location=f"ссылка на ст.{ref}"
            ))

    # 4. Простой поиск противоречий по ключевым фразам
    contradictions = [
        ("согласие обязательно", "согласие не требуется"),
        ("возможно без согласия", "требуется согласие"),
        ("вправе отказать", "обязан предоставить"),
    ]

    lines = text.splitlines()
    for i, line in enumerate(lines):
        for phrase1, phrase2 in contradictions:
            if phrase1.lower() in line.lower():
                # Ищем противоположную фразу в том же параграфе/статье
                start = max(0, i - 5)
                end = min(len(lines), i + 5)
                context = " ".join(lines[start:end]).lower()
                if phrase2.lower() in context:
                    issues.append(Issue(
                        type="semantic_contradiction",
                        description=f"Обнаружено противоречие: «{phrase1}» ↔ «{phrase2}»",
                        location=f"около строки {i + 1}"
                    ))

    return issues


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_document(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("cp1251")  # поддержка Windows-кодировки

    filename = file.filename or "document"
    issues = analyze_legal_text(text)

    return AnalysisResult(
        document=filename,
        issues=issues
    )
