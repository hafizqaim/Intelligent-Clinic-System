from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def patients_test():
    return {"module": "patients", "status": "ok"}
