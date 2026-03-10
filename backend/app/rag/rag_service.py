import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class LightRAGService:
    """
    Complete wrapper around LightRAG exposing document management,
    graph exploration, and multi-mode query capabilities.
    """

    def __init__(self):
        self._rag = None
        self._initialized = False

    # ── Lifecycle ─────────────────────────────────────────

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            from lightrag import LightRAG
            from lightrag.utils import EmbeddingFunc
        except ImportError:
            logger.warning(
                "lightrag-hku not installed. Q&A features will be unavailable."
            )
            return

        os.environ["POSTGRES_HOST"] = settings.POSTGRES_HOST
        os.environ["POSTGRES_PORT"] = str(settings.POSTGRES_PORT)
        os.environ["POSTGRES_USER"] = settings.POSTGRES_USER
        os.environ["POSTGRES_PASSWORD"] = settings.POSTGRES_PASSWORD
        os.environ["POSTGRES_DATABASE"] = settings.POSTGRES_DATABASE

        working_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "rag_storage",
        )
        os.makedirs(working_dir, exist_ok=True)

        try:
            if settings.LLM_PROVIDER == "ollama":
                rag_kwargs = self._build_ollama_config()
            else:
                rag_kwargs = self._build_api_config()

            self._rag = LightRAG(
                working_dir=working_dir,
                kv_storage="JsonKVStorage",
                vector_storage="NanoVectorDBStorage",
                graph_storage="NetworkXStorage",
                doc_status_storage="JsonDocStatusStorage",
                **rag_kwargs,
            )
            await self._rag.initialize_storages()
            self._initialized = True
            logger.info(
                "LightRAG initialized (provider=%s)", settings.LLM_PROVIDER
            )
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            self._rag = None

    @staticmethod
    def _build_ollama_config() -> dict:
        from lightrag.llm.ollama import ollama_model_complete, ollama_embed
        from lightrag.utils import EmbeddingFunc

        return {
            "llm_model_func": ollama_model_complete,
            "llm_model_name": settings.OLLAMA_LLM_MODEL,
            "llm_model_kwargs": {"host": settings.OLLAMA_HOST},
            "embedding_func": EmbeddingFunc(
                embedding_dim=settings.OLLAMA_EMBEDDING_DIM,
                max_token_size=8192,
                func=lambda texts: ollama_embed(
                    texts,
                    embed_model=settings.OLLAMA_EMBEDDING_MODEL,
                    host=settings.OLLAMA_HOST,
                ),
            ),
        }

    @staticmethod
    def _build_api_config() -> dict:
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        from lightrag.utils import EmbeddingFunc

        os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
        os.environ["OPENAI_API_BASE"] = settings.LLM_API_BASE

        return {
            "llm_model_func": openai_complete_if_cache,
            "llm_model_name": settings.LLM_MODEL_NAME,
            "llm_model_kwargs": {
                "base_url": settings.LLM_API_BASE,
                "api_key": settings.LLM_API_KEY,
            },
            "embedding_func": EmbeddingFunc(
                embedding_dim=settings.EMBEDDING_DIMENSIONS,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts,
                    model=settings.EMBEDDING_MODEL_NAME,
                    base_url=settings.LLM_API_BASE,
                    api_key=settings.LLM_API_KEY,
                    embedding_dim=settings.EMBEDDING_DIMENSIONS,
                ),
            ),
        }

    async def shutdown(self) -> None:
        if self._rag:
            try:
                await self._rag.finalize_storages()
            except Exception as e:
                logger.warning(f"Error shutting down LightRAG: {e}")
            self._rag = None
            self._initialized = False

    @property
    def is_available(self) -> bool:
        return self._initialized and self._rag is not None

    def _ensure_ready(self):
        if not self._rag:
            raise RuntimeError("LightRAG not initialized")

    # ── Document Management ───────────────────────────────

    async def insert_text(self, text: str) -> str:
        self._ensure_ready()
        track_id = await self._rag.ainsert(text)
        return track_id

    async def insert_file(self, file_path: str) -> str:
        self._ensure_ready()
        from app.rag.document_processor import PlainTextProcessor

        processor = PlainTextProcessor()
        chunks = await processor.process(file_path)
        combined = "\n\n".join(chunks)
        track_id = await self._rag.ainsert(combined, file_paths=[file_path])
        return track_id

    async def get_processing_status(self) -> dict[str, int]:
        self._ensure_ready()
        return await self._rag.get_processing_status()

    async def list_documents(
        self, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> dict:
        self._ensure_ready()
        from lightrag.base import DocStatus

        all_docs: dict[str, Any] = {}

        if status:
            status_enum = DocStatus(status)
            all_docs = await self._rag.get_docs_by_status(status_enum)
        else:
            for s in DocStatus:
                docs = await self._rag.get_docs_by_status(s)
                all_docs.update(docs)

        sorted_ids = sorted(
            all_docs.keys(),
            key=lambda did: getattr(all_docs[did], "created_at", ""),
            reverse=True,
        )
        total = len(sorted_ids)
        start = (page - 1) * page_size
        end = start + page_size
        page_ids = sorted_ids[start:end]

        items = []
        for doc_id in page_ids:
            doc = all_docs[doc_id]
            items.append(
                {
                    "id": doc_id,
                    "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
                    "content_summary": getattr(doc, "content_summary", ""),
                    "content_length": getattr(doc, "content_length", 0),
                    "created_at": getattr(doc, "created_at", ""),
                    "updated_at": getattr(doc, "updated_at", ""),
                    "file_path": getattr(doc, "file_path", ""),
                    "chunks_count": getattr(doc, "chunks_count", None),
                    "error_msg": getattr(doc, "error_msg", None),
                }
            )

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_document_by_id(self, doc_id: str) -> dict | None:
        self._ensure_ready()
        docs = await self._rag.aget_docs_by_ids(doc_id)
        if doc_id not in docs:
            return None
        doc = docs[doc_id]
        return {
            "id": doc_id,
            "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            "content_summary": getattr(doc, "content_summary", ""),
            "content_length": getattr(doc, "content_length", 0),
            "created_at": getattr(doc, "created_at", ""),
            "updated_at": getattr(doc, "updated_at", ""),
            "file_path": getattr(doc, "file_path", ""),
            "chunks_count": getattr(doc, "chunks_count", None),
            "error_msg": getattr(doc, "error_msg", None),
        }

    async def delete_document(self, doc_id: str) -> dict:
        self._ensure_ready()
        result = await self._rag.adelete_by_doc_id(doc_id)
        return {
            "status": result.status,
            "doc_id": result.doc_id,
            "message": result.message,
        }

    # ── Query ─────────────────────────────────────────────

    async def query(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 10,
        only_need_context: bool = False,
        response_type: str = "Multiple Paragraphs",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        self._ensure_ready()
        from lightrag import QueryParam

        param = QueryParam(
            mode=mode,
            top_k=top_k,
            only_need_context=only_need_context,
            response_type=response_type,
            stream=False,
            conversation_history=conversation_history or [],
        )
        result = await self._rag.aquery(question, param=param)
        return result

    async def query_stream(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 10,
        response_type: str = "Multiple Paragraphs",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        self._ensure_ready()
        from lightrag import QueryParam

        param = QueryParam(
            mode=mode,
            top_k=top_k,
            response_type=response_type,
            stream=True,
            conversation_history=conversation_history or [],
        )
        result = await self._rag.aquery(question, param=param)
        async for chunk in result:
            yield chunk

    # ── Graph Exploration ─────────────────────────────────

    async def get_graph_labels(self) -> list:
        self._ensure_ready()
        return await self._rag.get_graph_labels()

    async def get_knowledge_graph(
        self, label: str, max_depth: int = 3, max_nodes: int = 100
    ) -> dict:
        self._ensure_ready()
        kg = await self._rag.get_knowledge_graph(
            node_label=label, max_depth=max_depth, max_nodes=max_nodes
        )
        nodes = []
        edges = []
        if hasattr(kg, "nodes"):
            for node in kg.nodes:
                nodes.append(
                    {
                        "id": getattr(node, "id", str(node)),
                        "label": getattr(node, "label", str(node)),
                        "properties": getattr(node, "properties", {}),
                    }
                )
        if hasattr(kg, "edges"):
            for edge in kg.edges:
                edges.append(
                    {
                        "source": getattr(edge, "source", ""),
                        "target": getattr(edge, "target", ""),
                        "relation": getattr(edge, "label", getattr(edge, "relation", "")),
                        "properties": getattr(edge, "properties", {}),
                    }
                )
        return {"nodes": nodes, "edges": edges}

    async def get_entity_info(self, entity_name: str) -> dict:
        self._ensure_ready()
        return await self._rag.get_entity_info(entity_name)

    async def edit_entity(
        self,
        entity_name: str,
        updated_data: dict[str, str],
        allow_rename: bool = True,
        allow_merge: bool = False,
    ) -> dict:
        self._ensure_ready()
        return await self._rag.aedit_entity(
            entity_name, updated_data, allow_rename=allow_rename, allow_merge=allow_merge
        )

    async def create_entity(self, entity_name: str, entity_data: dict[str, Any]) -> dict:
        self._ensure_ready()
        return await self._rag.acreate_entity(entity_name, entity_data)

    async def delete_entity(self, entity_name: str) -> dict:
        self._ensure_ready()
        result = await self._rag.adelete_by_entity(entity_name)
        return {
            "status": result.status,
            "message": result.message,
        }

    async def merge_entities(
        self,
        source_entities: list[str],
        target_entity: str,
        merge_strategy: dict[str, str] | None = None,
        target_entity_data: dict[str, Any] | None = None,
    ) -> dict:
        self._ensure_ready()
        return await self._rag.amerge_entities(
            source_entities,
            target_entity,
            merge_strategy=merge_strategy,
            target_entity_data=target_entity_data,
        )

    async def get_relation_info(self, src_entity: str, tgt_entity: str) -> dict:
        self._ensure_ready()
        return await self._rag.get_relation_info(src_entity, tgt_entity)

    async def create_relation(
        self, source_entity: str, target_entity: str, relation_data: dict[str, Any]
    ) -> dict:
        self._ensure_ready()
        return await self._rag.acreate_relation(source_entity, target_entity, relation_data)

    async def edit_relation(
        self, source_entity: str, target_entity: str, updated_data: dict[str, Any]
    ) -> dict:
        self._ensure_ready()
        return await self._rag.aedit_relation(source_entity, target_entity, updated_data)

    async def delete_relation(self, source_entity: str, target_entity: str) -> dict:
        self._ensure_ready()
        result = await self._rag.adelete_by_relation(source_entity, target_entity)
        return {
            "status": result.status,
            "message": result.message,
        }
