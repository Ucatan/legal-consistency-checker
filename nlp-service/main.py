from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List

app = FastAPI()


class Issue(BaseModel):
    type: str
    description: str


class AnalysisResult(BaseModel):
    document: str
    issues: List[Issue]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)):
    # Читаем файл
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("cp1251")

    # Анализ (минимальная версия)
    issues = []
    text_lower = text.lower()

    if "согласие" in text_lower and "без согласия" in text_lower:
        issues.append(Issue(
            type="semantic_contradiction",
            description="Требуется и запрещено согласие"
        ))

    if "ст.99" in text_lower:
        issues.append(Issue(
            type="missing_reference",
            description="Ссылка на несуществующую статью ст.99"
        ))

    return AnalysisResult(
        document=file.filename or "unknown",
        issues=issues
    )
