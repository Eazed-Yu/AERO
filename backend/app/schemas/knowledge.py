from pydantic import BaseModel, Field


# ── 文档管理 ──────────────────────────────────────────────

class DocumentIngestText(BaseModel):
    text: str = Field(..., min_length=1)
    description: str | None = None


class DocumentResponse(BaseModel):
    id: str
    status: str
    content_summary: str = ""
    content_length: int = 0
    created_at: str = ""
    updated_at: str = ""
    file_path: str = ""
    chunks_count: int | None = None
    error_msg: str | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentStatusCounts(BaseModel):
    pending: int = 0
    processing: int = 0
    preprocessed: int = 0
    processed: int = 0
    failed: int = 0


# ── 查询 ──────────────────────────────────────────────────

class KnowledgeQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: str = Field("hybrid", pattern="^(local|global|hybrid|mix|naive|bypass)$")
    top_k: int = Field(10, ge=1, le=200)
    only_need_context: bool = False
    response_type: str = "Multiple Paragraphs"
    conversation_history: list[dict[str, str]] = []
    stream: bool = False


class KnowledgeQueryResponse(BaseModel):
    answer: str
    mode_used: str
    processing_time_ms: int


class QueryModeInfo(BaseModel):
    id: str
    name: str
    description: str


# ── 图谱 ──────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    properties: dict = {}


class SubgraphRequest(BaseModel):
    label: str
    max_depth: int = Field(3, ge=1, le=10)
    max_nodes: int = Field(100, ge=1, le=1000)


class SubgraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class EntityInfoRequest(BaseModel):
    entity_name: str


class EntityUpdateRequest(BaseModel):
    entity_name: str
    updated_data: dict[str, str]
    allow_rename: bool = True
    allow_merge: bool = False


class EntityCreateRequest(BaseModel):
    entity_name: str
    entity_data: dict[str, str]


class EntityMergeRequest(BaseModel):
    source_entities: list[str] = Field(..., min_length=2)
    target_entity: str
    merge_strategy: dict[str, str] | None = None
    target_entity_data: dict[str, str] | None = None


class RelationDeleteRequest(BaseModel):
    source_entity: str
    target_entity: str


class RelationInfoRequest(BaseModel):
    source_entity: str
    target_entity: str


class RelationCreateRequest(BaseModel):
    source_entity: str
    target_entity: str
    relation_data: dict[str, str]


class RelationUpdateRequest(BaseModel):
    source_entity: str
    target_entity: str
    updated_data: dict[str, str]
