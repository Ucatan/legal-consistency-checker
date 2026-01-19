from fileinput import filename
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import re
from fastapi.responses import FileResponse
import tempfile
import os
import pdfkit
from datetime import datetime

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



# Настройка пути к wkhtmltopdf для Windows
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

def generate_pdf_report(result: AnalysisResult, output_path: str):
    """Генерирует PDF-отчёт по анализу документа"""
    # HTML-шаблон с русской кодировкой
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6 }}
            .header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px }}
            .issue {{ margin: 15px 0; padding: 15px; border-radius: 5px; background: #f8f9fa }}
            .high {{ border-left: 4px solid #e74c3c; background: #fef6f6 }}
            .medium {{ border-left: 4px solid #f39c12; background: #fff8f0 }}
            .low {{ border-left: 4px solid #3498db; background: #f0f8ff }}
            .footer {{ margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 0.9em }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0 }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left }}
            th {{ background-color: #2c3e50; color: white }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="color: #2c3e50">Аналитический отчёт</h1>
            <h2>Федеральный закон "О персональных данных" (№152-ФЗ)</h2>
            <p>Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>Имя файла: {result.document}</p>
        </div>
        
        <h2 style="color: #2c3e50">Выявленные несоответствия</h2>
        {"".join([
        f'<div class="issue {issue.severity}">'
        f'<h3 style="margin-top: 0; color: #2c3e50">[{issue.type.upper()}] {issue.description}</h3>'
        f'<p><strong>Местоположение:</strong> {issue.location}</p>'
        f'<p><strong>Критичность:</strong> '
        f'<span style="color: {"#e74c3c" if issue.severity=="high" else "#f39c12" if issue.severity=="medium" else "#3498db"}">'
        f'{issue.severity.capitalize()}</span></p>'
        f'</div>'
        for issue in result.issues
    ]) if result.issues else "<p style='color: #27ae60; font-weight: bold'>Противоречий не обнаружено</p>"}
        
        <div class="footer">
            <p>Система Legal Consistency Checker — автоматический анализ юридических документов</p>
            <p>Рекомендация: Все выявленные противоречия требуют проверки квалифицированным юристом</p>
        </div>
    </body>
    </html>
    """

    # Генерация PDF
    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    pdfkit.from_string(
        html,
        output_path,
        configuration=config,
        options={
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm'
        }
    )
    return output_path

@app.post("/generate-report")
async def generate_report(file: UploadFile = File(...)):
    """Генерирует PDF-отчёт по анализу документа"""
    try:
        # Анализ документа
        content = await file.read()
        text = content.decode('utf-8-sig', errors='ignore')
        issues = analyze_legal_text(text)

        # Формирование результата
        result = AnalysisResult(
            document=file.filename,
            issues=issues,
            status="completed"
        )

        # Генерация PDF во временном файле
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = generate_pdf_report(result, tmp.name)

        # Отправка файла клиенту
        response = FileResponse(
            pdf_path,
            filename=f"legal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            media_type="application/pdf"
        )

        # Автоматическая очистка временного файла после отправки
        response.background = lambda: os.unlink(pdf_path)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчёта: {str(e)}")


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
    # Читаем содержимое файла
    content = await file.read()
    text = content.decode('utf-8-sig', errors='ignore')

    # Анализируем текст
    issues = analyze_legal_text(text)

    return AnalysisResult(
        document=file.filename,
        issues=issues,
        status="completed"
    )