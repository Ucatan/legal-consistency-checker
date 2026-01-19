# nlp-service/pdf_generator.py
import pdfkit
from datetime import datetime
from models import AnalysisResult, Issue

def generate_pdf_report(result: AnalysisResult, output_path: str):
    """Генерирует PDF-отчёт по анализу ФЗ-152"""
    # HTML-шаблон отчёта
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px }}
            .issue {{ margin: 15px 0; padding: 10px; border-left: 3px solid #e74c3c }}
            .high {{ border-color: #e74c3c }}
            .medium {{ border-color: #f39c12 }}
            .low {{ border-color: #3498db }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 0.9em; color: #777 }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Отчёт по анализу ФЗ-152</h1>
            <p>Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>Документ: {result.document}</p>
        </div>
        
        <h2>Выявленные противоречия</h2>
        {"".join([
        f'<div class="issue {issue.severity}">'
        f'<strong>Тип:</strong> {issue.type}<br>'
        f'<strong>Описание:</strong> {issue.description}<br>'
        f'<strong>Местоположение:</strong> {issue.location or "Не указано"}'
        f'</div>'
        for issue in result.issues
    ]) if result.issues else "<p>Противоречий не обнаружено</p>"}
        
        <div class="footer">
            Система Legal Consistency Checker — автоматический анализ юридических документов
        </div>
    </body>
    </html>
    """

    # Конфигурация для Windows
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

    # Генерация PDF
    pdfkit.from_string(
        html,
        output_path,
        configuration=config,
        options={'encoding': 'UTF-8'}
    )
    return output_path