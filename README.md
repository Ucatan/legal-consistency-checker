# Legal Consistency Checker

AI-агент для анализа юридических документов на противоречия, циклические ссылки и логическую целостность.
Система анализа юридических документов на противоречия в ФЗ-152.

## Стек
- Java 17 + Spring Boot (backend, API)
- Python 3.10+ + FastAPI + spaCy (NLP/анализ)
- Запуск: локально / Docker / Cloud

### Запуск
```bash
# Backend (Spring Boot)
cd backend
mvn spring-boot:run

# NLP Service (FastAPI)
cd nlp-service
uvicorn main:app --port 8001