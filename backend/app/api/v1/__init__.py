from fastapi import APIRouter
from app.api.v1.matters import router as matters_router
from app.api.v1.intake import router as intake_router
from app.api.v1.drafting import router as drafting_router
from app.api.v1.review import router as review_router
from app.api.v1.documents import router as documents_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.advisory import router as advisory_router
from app.api.v1.admin import router as admin_router
from app.api.v1.deeds import router as deeds_router

api_router = APIRouter()

api_router.include_router(matters_router, prefix="/matters", tags=["Matters"])
api_router.include_router(intake_router, prefix="/intake", tags=["Legal Intake"])
api_router.include_router(drafting_router, prefix="/drafting", tags=["Drafting Engine"])
api_router.include_router(review_router, prefix="/review", tags=["Review & Health Check"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents & Export"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Legal Knowledge Base"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["AI Evaluation & Feedback"])
api_router.include_router(advisory_router, prefix="/advisory", tags=["Legal Advisory & Problem Solver"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin & System Training"])
api_router.include_router(deeds_router, prefix="/deeds", tags=["Deed Intelligence & Fraud Detection"])
