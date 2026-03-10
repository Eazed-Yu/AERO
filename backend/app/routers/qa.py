import json
import logging
import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.knowledge import (
    DocumentIngestText,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusCounts,
    EntityCreateRequest,
    EntityInfoRequest,
    EntityMergeRequest,
    EntityUpdateRequest,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    RelationCreateRequest,
    RelationDeleteRequest,
    RelationInfoRequest,
    RelationUpdateRequest,
    SubgraphRequest,
    SubgraphResponse,
)
from app.services.qa_service import KnowledgeService

logger = logging.getLogger(__name__)

router = APIRouter()

_knowledge_service: KnowledgeService | None = None


def set_knowledge_service(svc: KnowledgeService):
    global _knowledge_service
    _knowledge_service = svc


def _svc() -> KnowledgeService:
    if _knowledge_service is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge service not initialized. LightRAG may not be configured.",
        )
    return _knowledge_service


# ── Document Management ───────────────────────────────────


@router.post("/documents/text")
async def ingest_text(data: DocumentIngestText):
    return await _svc().ingest_text(data.text)


@router.post("/documents/upload")
async def upload_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".txt", ".md"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Only .txt and .md are supported.",
        )

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
        result = await _svc().ingest_file(tmp_path)
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    return await _svc().list_documents(status=status, page=page, page_size=page_size)


@router.get("/documents/status", response_model=DocumentStatusCounts)
async def document_status_counts():
    return await _svc().get_processing_status()


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    doc = await _svc().get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    return await _svc().delete_document(doc_id)


# ── Graph Exploration ─────────────────────────────────────


@router.get("/graph/labels")
async def get_graph_labels():
    return await _svc().get_graph_labels()


@router.post("/graph/subgraph", response_model=SubgraphResponse)
async def get_subgraph(data: SubgraphRequest):
    return await _svc().get_subgraph(
        label=data.label, max_depth=data.max_depth, max_nodes=data.max_nodes
    )


@router.post("/graph/entity/info")
async def get_entity_info(data: EntityInfoRequest):
    return await _svc().get_entity_info(data.entity_name)


@router.post("/graph/entity")
async def create_entity(data: EntityCreateRequest):
    return await _svc().create_entity(data.entity_name, data.entity_data)


@router.put("/graph/entity")
async def update_entity(data: EntityUpdateRequest):
    return await _svc().update_entity(
        data.entity_name,
        data.updated_data,
        allow_rename=data.allow_rename,
        allow_merge=data.allow_merge,
    )


@router.delete("/graph/entity/{entity_name}")
async def delete_entity(entity_name: str):
    return await _svc().delete_entity(entity_name)


@router.post("/graph/entity/merge")
async def merge_entities(data: EntityMergeRequest):
    return await _svc().merge_entities(
        data.source_entities,
        data.target_entity,
        merge_strategy=data.merge_strategy,
        target_entity_data=data.target_entity_data,
    )


@router.post("/graph/relation/info")
async def get_relation_info(data: RelationInfoRequest):
    return await _svc().get_relation_info(data.source_entity, data.target_entity)


@router.post("/graph/relation")
async def create_relation(data: RelationCreateRequest):
    return await _svc().create_relation(
        data.source_entity, data.target_entity, data.relation_data
    )


@router.put("/graph/relation")
async def update_relation(data: RelationUpdateRequest):
    return await _svc().update_relation(
        data.source_entity, data.target_entity, data.updated_data
    )


@router.post("/graph/relation/delete")
async def delete_relation(data: RelationDeleteRequest):
    return await _svc().delete_relation(data.source_entity, data.target_entity)


# ── Query ─────────────────────────────────────────────────


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query(data: KnowledgeQueryRequest):
    result = await _svc().ask(
        question=data.question,
        mode=data.mode,
        top_k=data.top_k,
        only_need_context=data.only_need_context,
        response_type=data.response_type,
        conversation_history=data.conversation_history,
    )
    return KnowledgeQueryResponse(**result)


@router.post("/query/stream")
async def query_stream(data: KnowledgeQueryRequest):
    svc = _svc()

    async def event_generator():
        try:
            async for chunk in svc.ask_stream(
                question=data.question,
                mode=data.mode,
                top_k=data.top_k,
                response_type=data.response_type,
                conversation_history=data.conversation_history,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/modes")
async def list_modes():
    return {
        "modes": [
            {"id": "local", "name": "局部检索", "description": "检索与问题直接相关的实体和关系"},
            {"id": "global", "name": "全局检索", "description": "跨文档集合的广泛知识图谱检索"},
            {"id": "hybrid", "name": "混合检索", "description": "结合局部和全局检索（推荐）"},
            {"id": "naive", "name": "朴素检索", "description": "简单的向量相似度检索"},
            {"id": "mix", "name": "融合检索", "description": "整合知识图谱和向量检索"},
            {"id": "bypass", "name": "直接问答", "description": "跳过知识检索，直接使用 LLM"},
        ]
    }
