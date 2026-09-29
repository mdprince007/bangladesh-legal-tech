import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1 import api_router
from app.services.knowledge_service import KnowledgeService

# Ensure storage directory exists
os.makedirs(os.path.abspath(settings.STORAGE_DIR), exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure new columns exist in documents and deed_records tables (for existing SQLite databases)
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA table_info(documents);")).fetchall()
        col_names = [r[1] for r in res]
        if "book_grounding_score" not in col_names:
            conn.execute(text("ALTER TABLE documents ADD COLUMN book_grounding_score INTEGER;"))
        if "book_chapter_reference" not in col_names:
            conn.execute(text("ALTER TABLE documents ADD COLUMN book_chapter_reference VARCHAR(500);"))
        if "book_applied_rules" not in col_names:
            conn.execute(text("ALTER TABLE documents ADD COLUMN book_applied_rules JSON;"))
        if "draft_audit" not in col_names:
            conn.execute(text("ALTER TABLE documents ADD COLUMN draft_audit JSON;"))

        # Deed records columns
        d_res = conn.execute(text("PRAGMA table_info(deed_records);")).fetchall()
        d_cols = [r[1] for r in d_res]
        if "image_quality_report" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN image_quality_report JSON;"))
        if "layout_zones" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN layout_zones JSON;"))
        if "text_lines" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN text_lines JSON;"))
        if "structured_fields" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN structured_fields JSON;"))
        if "reading_report" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN reading_report JSON;"))
        if "page_image_paths" not in d_cols:
            conn.execute(text("ALTER TABLE deed_records ADD COLUMN page_image_paths JSON;"))
        conn.commit()
except Exception:
    pass


# Seed initial verified statutes
db = SessionLocal()
try:
    KnowledgeService.seed_initial_statutes(db)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Bangladesh Legal Intelligence & Legal Operations SaaS API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount storage directory for direct document previews/downloads
app.mount("/storage", StaticFiles(directory=os.path.abspath(settings.STORAGE_DIR)), name="storage")

# Mount Next.js build assets if available
frontend_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "out"))
next_assets = os.path.join(frontend_out, "_next")
if os.path.exists(next_assets):
    app.mount("/_next", StaticFiles(directory=next_assets), name="next_assets")

# Mount static directory for fallback assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_dashboard():
    # Serve Next.js production build if available
    next_index = os.path.join(frontend_out, "index.html")
    if os.path.exists(next_index):
        from fastapi.responses import FileResponse
        return FileResponse(next_index)
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
    return {
        "platform": settings.PROJECT_NAME,
        "jurisdiction": "Bangladesh",
        "status": "operational",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/classic")
@app.get("/classic/")
def serve_classic_dashboard():
    # The hand-written static UI (includes the deed crop-test tool) is shadowed at "/" by the Next.js build
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

@app.get("/admin")
@app.get("/admin/")
def serve_admin_portal():
    # Serve Next.js admin build if available
    next_admin = os.path.join(frontend_out, "admin", "index.html")
    if os.path.exists(next_admin):
        from fastapi.responses import FileResponse
        return FileResponse(next_admin)
    admin_file = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if os.path.exists(admin_file):
        from fastapi.responses import FileResponse
        return FileResponse(admin_file)
    return {"error": "Admin portal UI not found"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "legal-ai-saas-core"}
