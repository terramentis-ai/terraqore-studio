"""Simple FastAPI wrapper around the RAG retriever for internal use."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from appshell.core.rag_service import get_default_store

app = FastAPI(title="TerraQore RAG Retriever API")
store = get_default_store()


class AddDocRequest(BaseModel):
    doc_id: str
    text: str
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 5


@app.post("/add")
def add_doc(req: AddDocRequest):
    try:
        store.add(req.doc_id, req.text, req.metadata or {})
        return {"status": "ok", "doc_id": req.doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
def search(req: SearchRequest):
    try:
        results = store.search(req.query, k=req.k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "store_type": type(store).__name__}
