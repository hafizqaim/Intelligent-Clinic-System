from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def clinics_test():
    return {"module": "clinics", "status": "ok"}
