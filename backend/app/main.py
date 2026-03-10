import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.lightrag_launcher import start_lightrag_server, stop_lightrag_server
from app.rag.rag_service import LightRAGService
from app.mcp.server import get_mcp_lifespan_context, is_mcp_enabled, mount_mcp
from app.routers import (
    anomaly,
    buildings,
    data_import,
    energy,
    equipment,
    export,
    mcp_manage,
    qa,
    statistics,
)
from app.services.qa_service import KnowledgeService

logger = logging.getLogger(__name__)

rag_service = LightRAGService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        # Startup
        logger.info("Starting AERO application...")

        # Initialize FastMCP mounted app lifespan if present.
        mcp_lifespan = get_mcp_lifespan_context()
        if mcp_lifespan is not None:
            await stack.enter_async_context(mcp_lifespan(app))

        # Start LightRAG Web UI Server
        await start_lightrag_server()

        # Initialize LightRAG
        try:
            await rag_service.initialize()
            if rag_service.is_available:
                knowledge_svc = KnowledgeService(rag_service)
                qa.set_knowledge_service(knowledge_svc)
                logger.info("LightRAG initialized successfully")
            else:
                logger.warning("LightRAG not available. Knowledge features disabled.")
        except Exception as e:
            logger.warning(f"LightRAG initialization failed: {e}")

        yield

        # Shutdown
        logger.info("Shutting down AERO application...")
        await stop_lightrag_server()
        await rag_service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AERO - 建筑能源智能管理系统",
        description="Building Energy Intelligent Management System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(
        buildings.router, prefix="/api/v1/buildings", tags=["buildings"]
    )
    app.include_router(
        data_import.router, prefix="/api/v1/import", tags=["import"]
    )
    app.include_router(
        energy.router, prefix="/api/v1/energy", tags=["energy"]
    )
    app.include_router(
        statistics.router, prefix="/api/v1/statistics", tags=["statistics"]
    )
    app.include_router(
        anomaly.router, prefix="/api/v1/anomaly", tags=["anomaly"]
    )
    app.include_router(
        equipment.router, prefix="/api/v1/equipment", tags=["equipment"]
    )
    app.include_router(
        export.router, prefix="/api/v1/export", tags=["export"]
    )
    app.include_router(qa.router, prefix="/api/v1/knowledge", tags=["knowledge"])
    app.include_router(
        mcp_manage.router, prefix="/api/v1/mcp", tags=["mcp"]
    )

    # Mount MCP server
    mount_mcp(app)

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "rag_available": rag_service.is_available,
            "mcp_available": is_mcp_enabled(),
        }

    return app


app = create_app()
