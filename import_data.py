"""API Router for Data Ingestion and Import Boundary."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.entities import ImportRun
from app.schemas.domain import ImportSummarySchema
from app.services.import_engine import (
    preview_import_data, process_telemetry_import, generate_sample_csv
)

router = APIRouter(prefix="/import", tags=["Data Import"])

@router.get("/sample-csv")
def download_sample_csv():
    """Returns a downloadable sample CSV with valid column structure and timestamps."""
    csv_text = generate_sample_csv()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plantpulse_telemetry_sample.csv"}
    )

@router.post("/preview")
async def preview_file(file: UploadFile = File(...)):
    """Previews first 10 rows and validates header schema before import."""
    contents = await file.read()
    text = contents.decode("utf-8", errors="replace")
    file_type = "CSV" if file.filename.endswith(".csv") else "JSON"
    return preview_import_data(text, file_type)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Processes CSV or JSON file and populates the telemetry table with provenance=IMPORTED."""
    contents = await file.read()
    text = contents.decode("utf-8", errors="replace")
    file_type = "CSV" if file.filename.endswith(".csv") else "JSON"
    
    try:
        summary = process_telemetry_import(db, file.filename, text, file_type=file_type)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@router.get("/runs", response_model=List[ImportSummarySchema])
def list_import_runs(db: Session = Depends(get_db)):
    return db.query(ImportRun).order_by(desc(ImportRun.imported_at)).limit(50).all()
