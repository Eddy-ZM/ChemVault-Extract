import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import DocumentStatus, JobStatus
from app.database import get_db
from app.dependencies import get_queue, get_storage
from app.models import Document, DocumentBlock, DocumentChunk, DocumentPage, ExtractionJob, Project, User
from app.queue import JobQueue
from app.schemas import (
    DocumentBlockRead,
    DocumentChunkRead,
    DocumentPageRead,
    DocumentWithLatestJob,
    ExtractionJobRead,
    UploadDocumentResponse,
)
from app.storage import S3Storage, sanitize_filename, validate_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


def _latest_job(db: Session, document_id: str) -> ExtractionJob | None:
    return db.scalars(
        select(ExtractionJob)
        .where(ExtractionJob.document_id == document_id)
        .order_by(ExtractionJob.created_at.desc(), ExtractionJob.id.desc())
        .limit(1)
    ).first()


def _document_response(db: Session, document: Document) -> DocumentWithLatestJob:
    latest = _latest_job(db, document.id)
    return DocumentWithLatestJob.model_validate(document).model_copy(
        update={"latest_job": ExtractionJobRead.model_validate(latest) if latest else None}
    )


def _get_or_create_default_project(db: Session) -> Project:
    settings = get_settings()
    user = db.scalars(select(User).where(User.email == settings.default_user_email)).first()
    if user is None:
        user = User(email=settings.default_user_email, name="Local User")
        db.add(user)
        db.flush()

    project = db.scalars(
        select(Project).where(
            Project.user_id == user.id,
            Project.name == settings.default_project_name,
        )
    ).first()
    if project is None:
        project = Project(user_id=user.id, name=settings.default_project_name)
        db.add(project)
        db.flush()
    return project


@router.get("", response_model=list[DocumentWithLatestJob])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentWithLatestJob]:
    documents = db.scalars(select(Document).order_by(Document.created_at.desc(), Document.id.desc())).all()
    return [_document_response(db, document) for document in documents]


@router.get("/{document_id}", response_model=DocumentWithLatestJob)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentWithLatestJob:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _document_response(db, document)


@router.get("/{document_id}/pages", response_model=list[DocumentPageRead])
def get_document_pages(document_id: str, db: Session = Depends(get_db)) -> list[DocumentPageRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    pages = db.scalars(
        select(DocumentPage).where(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)
    ).all()
    return [DocumentPageRead.model_validate(page) for page in pages]


@router.get("/{document_id}/blocks", response_model=list[DocumentBlockRead])
def get_document_blocks(document_id: str, db: Session = Depends(get_db)) -> list[DocumentBlockRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    blocks = db.scalars(
        select(DocumentBlock)
        .where(DocumentBlock.document_id == document_id)
        .order_by(DocumentBlock.page_number.is_(None), DocumentBlock.page_number, DocumentBlock.created_at, DocumentBlock.id)
    ).all()
    return [DocumentBlockRead.model_validate(block) for block in blocks]


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
def get_document_chunks(document_id: str, db: Session = Depends(get_db)) -> list[DocumentChunkRead]:
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    return [DocumentChunkRead.model_validate(chunk) for chunk in chunks]


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: S3Storage = Depends(get_storage),
    queue: JobQueue = Depends(get_queue),
) -> UploadDocumentResponse:
    file_type = validate_upload_file(file)
    project = _get_or_create_default_project(db)
    document_id = str(uuid.uuid4())
    filename = sanitize_filename(file.filename or f"document.{file_type}")
    storage_key = f"documents/{project.id}/{document_id}/{filename}"
    mime_type = file.content_type or "application/octet-stream"

    storage.upload_fileobj(storage_key, file.file, mime_type)

    document = Document(
        id=document_id,
        project_id=project.id,
        filename=filename,
        original_filename=file.filename or filename,
        file_type=file_type,
        mime_type=mime_type,
        storage_key=storage_key,
        status=DocumentStatus.UPLOADED.value,
    )
    job = ExtractionJob(document_id=document.id, status=JobStatus.QUEUED.value)
    db.add(document)
    db.add(job)
    db.commit()
    db.refresh(document)
    db.refresh(job)

    queue.push_job(job.id)

    return UploadDocumentResponse(
        document=DocumentWithLatestJob.model_validate(document),
        job=ExtractionJobRead.model_validate(job),
    )


@router.post("/{document_id}/extract", response_model=ExtractionJobRead, status_code=status.HTTP_201_CREATED)
def create_extraction_job(
    document_id: str,
    db: Session = Depends(get_db),
    queue: JobQueue = Depends(get_queue),
) -> ExtractionJobRead:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    job = ExtractionJob(document_id=document.id, status=JobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    queue.push_job(job.id)
    return ExtractionJobRead.model_validate(job)
