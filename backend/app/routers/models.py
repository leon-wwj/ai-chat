from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.logging_setup import logger
from app.schemas import ModelsRequest
from app.services.chat import list_models
from app.utils import new_request_id

router = APIRouter()


@router.post("/models")
async def models_endpoint(req: ModelsRequest):
    rid = new_request_id()

    logger.info("req=%s /models start base_url=%s", rid, req.base_url)

    models, error = await list_models(rid, req)
    if error is not None:
        return JSONResponse(status_code=502, content={"error": error})

    return {"models": models}
