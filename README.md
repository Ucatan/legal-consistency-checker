# Legal Consistency Checker

AI-агент для анализа юридических документов на противоречия, циклические ссылки и логическую целостность.

## Стек
- Java 17 + Spring Boot (backend, API)
- Python 3.10+ + FastAPI + spaCy (NLP/анализ)
- Запуск: локально / Docker / Cloud

## Старт
```bash
# Запуск Python-сервиса
cd nlp-service && uvicorn main:app --reload

# Запуск Java-сервиса
./mvnw spring-boot:run -pl backend