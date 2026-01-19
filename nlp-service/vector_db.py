from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LegalVectorDB:
    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

        # загрузка модели
        self.model_path = self._get_model_path()
        logger.info(f"📥 Загружаем модель из: {self.model_path}")

        try:
            self.model = SentenceTransformer(str(self.model_path))
            logger.info("✅ Модель успешно загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            logger.warning("🔄 Пытаемся загрузить из интернета...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Модель загружена из интернета")

        self.collection_name = "fz_articles"
        self._init_collection()

    def _get_model_path(self) -> Path:
        """Определяет правильный путь к модели"""
        # 1. Сначала проверяем переменную окружения (для Docker)
        env_path = os.getenv("MODEL_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)

        # 2. Для локального запуска из nlp-service
        local_path = Path(__file__).parent.parent.parent / "models" / "all-MiniLM-L6-v2"
        if local_path.exists():
            return local_path

        # 3. Для запуска из корня проекта
        root_path = Path.cwd() / "models" / "all-MiniLM-L6-v2"
        if root_path.exists():
            return root_path

        # 4. Fallback для Windows (абсолютный путь)
        windows_path = Path("C:/Users/telem/IdeaProjects/legal-consistency-checker/models/all-MiniLM-L6-v2")
        if windows_path.exists():
            return windows_path

        # 5. Если ничего не найдено - используем имя модели (загрузка из интернета)
        logger.warning("⚠️ Модель не найдена локально. Будет загружена из интернета.")
        return "all-MiniLM-L6-v2"

    def _init_collection(self):
        """Создаёт коллекцию, если её нет"""
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Размер эмбеддингов all-MiniLM-L6-v2
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"✅ Коллекция {self.collection_name} создана")
        except Exception as e:
            logger.error(f"❌ Ошибка создания коллекции: {e}")
            raise

    def index_articles(self, articles: dict):
        """Индексирует статьи в Qdrant"""
        points = []
        for article_num, text in articles.items():
            try:
                embedding = self.model.encode([text])[0].tolist()
                points.append(
                    models.PointStruct(
                        id=hash(article_num),
                        vector=embedding,
                        payload={
                            "article_num": article_num,
                            "text": text[:200],
                            "type": "law_article"
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка эмбеддинга для статьи {article_num}: {e}")

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"✅ Проиндексировано {len(points)} статей")

    def find_contradictions(self, query_text: str, article_num: str, top_k: int = 3):
        """Ищет противоречия для конкретной статьи"""
        try:
            query_vector = self.model.encode([query_text])[0].tolist()
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must_not=[
                        models.FieldCondition(
                            key="article_num",
                            match=models.MatchValue(value=article_num)
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True
            )

            contradictions = []
            for hit in results:
                # Проверяем на юридические противоречия
                if self._is_contradiction(query_text, hit.payload["text"]):
                    contradictions.append({
                        "article_num": hit.payload["article_num"],
                        "score": hit.score,
                        "text_preview": hit.payload["text"]
                    })
            return contradictions
        except Exception as e:
            logger.error(f"❌ Ошибка поиска противоречий: {e}")
            return []

    def _is_contradiction(self, text1: str, text2: str) -> bool:
        """Проверяет наличие юридического противоречия"""
        text1 = text1.lower()
        text2 = text2.lower()

        # Правила для ФЗ-152
        CONTRADICTION_RULES = [
            ("согласие", ["без согласия", "в отсутствие согласия"]),
            ("обязательно", ["не требуется", "допускается без"]),
            ("запрещено", ["разрешено", "допускается"]),
        ]

        for trigger, contradictions in CONTRADICTION_RULES:
            if trigger in text1:
                return any(contradiction in text2 for contradiction in contradictions)
            if trigger in text2:
                return any(contradiction in text1 for contradiction in contradictions)
        return False