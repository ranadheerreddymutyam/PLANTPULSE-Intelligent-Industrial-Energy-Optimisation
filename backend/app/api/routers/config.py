"""API Router for Site Configuration & Settings."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import SiteConfig, AuditLog
from app.schemas.domain import SiteConfigSchema, SiteConfigUpdate
from app.core.provenance import ProvenanceType

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.get("/", response_model=SiteConfigSchema)
def get_site_config(db: Session = Depends(get_db)):
    config = db.query(SiteConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="Site configuration not found")
    return config

@router.put("/", response_model=SiteConfigSchema)
def update_site_config(payload: SiteConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(SiteConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="Site configuration not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
        
    config.provenance = ProvenanceType.CONFIGURED
    
    audit = AuditLog(
        user_id="ADMIN",
        role="ADMIN",
        action="UPDATE_SITE_CONFIG",
        entity="SITE_CONFIG",
        entity_id=config.id,
        details=update_data,
        provenance=ProvenanceType.CONFIGURED
    )
    db.add(audit)
    db.commit()
    db.refresh(config)
    return config
