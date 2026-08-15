from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.nlp.schemas import NLPResult
from app.nlp.service import nlp_service

router = APIRouter()

class NLPRequest(BaseModel):
    text: str

@router.post("/process", response_model=NLPResult, summary="Process text through the NLP pipeline")
async def process_text_on_demand(payload: NLPRequest = Body(...)):
    """
    On-demand NLP service to extract entities and geocode locations from raw text.
    """
    return await nlp_service.process_text(payload.text)
