from pydantic import BaseModel
from datetime import datetime


class UploadDocumentResponse(BaseModel):
    message: str
    document_id: int
    file_name: str
    total_chunks: int


class DocumentResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_size: int
    total_chunks: int
    status: str
    uploaded_at: datetime


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    chunk_index: int


class DeleteDocumentResponse(BaseModel):
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]