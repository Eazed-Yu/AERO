import time
from collections.abc import AsyncGenerator
from typing import Any

from app.rag.rag_service import LightRAGService


class KnowledgeService:
    def __init__(self, rag_service: LightRAGService):
        self.rag = rag_service

    # ── Document Management ───────────────────────────────

    async def ingest_text(self, text: str) -> dict:
        start = time.time()
        track_id = await self.rag.insert_text(text)
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "track_id": track_id,
            "processing_time_ms": elapsed_ms,
        }

    async def ingest_file(self, file_path: str) -> dict:
        start = time.time()
        track_id = await self.rag.insert_file(file_path)
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "track_id": track_id,
            "processing_time_ms": elapsed_ms,
        }

    async def list_documents(
        self, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> dict:
        return await self.rag.list_documents(status=status, page=page, page_size=page_size)

    async def get_document(self, doc_id: str) -> dict | None:
        return await self.rag.get_document_by_id(doc_id)

    async def delete_document(self, doc_id: str) -> dict:
        return await self.rag.delete_document(doc_id)

    async def get_processing_status(self) -> dict[str, int]:
        return await self.rag.get_processing_status()

    # ── Query ─────────────────────────────────────────────

    async def ask(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 10,
        only_need_context: bool = False,
        response_type: str = "Multiple Paragraphs",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict:
        start = time.time()
        answer = await self.rag.query(
            question,
            mode=mode,
            top_k=top_k,
            only_need_context=only_need_context,
            response_type=response_type,
            conversation_history=conversation_history,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "answer": answer,
            "mode_used": mode,
            "processing_time_ms": elapsed_ms,
        }

    async def ask_stream(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 10,
        response_type: str = "Multiple Paragraphs",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.rag.query_stream(
            question,
            mode=mode,
            top_k=top_k,
            response_type=response_type,
            conversation_history=conversation_history,
        ):
            yield chunk

    # ── Graph Exploration ─────────────────────────────────

    async def get_graph_labels(self) -> list:
        return await self.rag.get_graph_labels()

    async def get_subgraph(
        self, label: str, max_depth: int = 3, max_nodes: int = 100
    ) -> dict:
        return await self.rag.get_knowledge_graph(label, max_depth=max_depth, max_nodes=max_nodes)

    async def get_entity_info(self, entity_name: str) -> dict:
        return await self.rag.get_entity_info(entity_name)

    async def update_entity(
        self,
        entity_name: str,
        updated_data: dict[str, str],
        allow_rename: bool = True,
        allow_merge: bool = False,
    ) -> dict:
        return await self.rag.edit_entity(
            entity_name, updated_data, allow_rename=allow_rename, allow_merge=allow_merge
        )

    async def create_entity(self, entity_name: str, entity_data: dict[str, Any]) -> dict:
        return await self.rag.create_entity(entity_name, entity_data)

    async def delete_entity(self, entity_name: str) -> dict:
        return await self.rag.delete_entity(entity_name)

    async def merge_entities(
        self,
        source_entities: list[str],
        target_entity: str,
        merge_strategy: dict[str, str] | None = None,
        target_entity_data: dict[str, Any] | None = None,
    ) -> dict:
        return await self.rag.merge_entities(
            source_entities, target_entity,
            merge_strategy=merge_strategy,
            target_entity_data=target_entity_data,
        )

    async def get_relation_info(self, src_entity: str, tgt_entity: str) -> dict:
        return await self.rag.get_relation_info(src_entity, tgt_entity)

    async def create_relation(
        self, source_entity: str, target_entity: str, relation_data: dict[str, Any]
    ) -> dict:
        return await self.rag.create_relation(source_entity, target_entity, relation_data)

    async def update_relation(
        self, source_entity: str, target_entity: str, updated_data: dict[str, Any]
    ) -> dict:
        return await self.rag.edit_relation(source_entity, target_entity, updated_data)

    async def delete_relation(self, source_entity: str, target_entity: str) -> dict:
        return await self.rag.delete_relation(source_entity, target_entity)
