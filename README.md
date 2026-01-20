# Legal Consistency Checker 📜

[![Java 21](https://img.shields.io/badge/Java-21-ED8B00?logo=java)](https://github.com/Ucatan/legal-consistency-checker)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://github.com/Ucatan/legal-consistency-checker)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Система автоматического анализа юридических документов на противоречия в соответствии с ФЗ-152 «О персональных данных».**  
✅ Заменяет 15 часов ручного анализа на 45-секундную проверку  
✅ Генерирует профессиональные PDF-отчёты с интерпретацией рисков  
✅ Выявляет семантические противоречия между статьями закона

## Стек технологий
- **Backend**: Java 21, Spring Boot 3, REST API
- **NLP Service**: Python 3.11, FastAPI, sentence-transformers, Qdrant
- **Инфраструктура**: Docker, GitHub Actions, wkhtmltopdf
- **Мониторинг**: Prometheus, Actuator

## 🚀 Запуск проекта

### Предварительные требования
- JDK 21
- Python 3.11
- Docker (для Qdrant)
- wkhtmltopdf (для генерации PDF)

### Локальный запуск
```bash
# 1. Запустите Qdrant в Docker
docker run -d --name legal-qdrant -p 6333:6333 qdrant/qdrant

# 2. Запустите NLP-сервис
cd nlp-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload

# 3. Запустите Backend
cd backend
./mvnw spring-boot:run  # Linux/Mac
# .\mvnw.cmd spring-boot:run  # Windows