from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def rag_test():
    return {"module": "rag", "status": "ok"}
