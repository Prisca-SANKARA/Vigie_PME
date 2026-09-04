from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.models import Client, FindingRecord, ScanRun
from db.session import get_db, init_db
from scanner.engine import perform_scan
from scanner.report import compute_score

from .auth import create_access_token, get_current_client, hash_password, verify_password
from .schemas import (
    ClientOut,
    ClientRegister,
    ScanRequest,
    ScanRunOut,
    ScanSummaryOut,
    Token,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Vigie_PME — API", lifespan=lifespan)

# Dashboard React servi séparément (Vite, port 5173 en dev) : CORS ouvert
# uniquement à cette origine locale pour l'instant.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token)
def register(payload: ClientRegister, db: Session = Depends(get_db)) -> Token:
    if db.query(Client).filter(Client.email == payload.email).first() is not None:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    client = Client(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        company_name=payload.company_name,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return Token(access_token=create_access_token(client.id))


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    client = db.query(Client).filter(Client.email == form_data.username).first()
    if client is None or not verify_password(form_data.password, client.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    return Token(access_token=create_access_token(client.id))


@app.get("/auth/me", response_model=ClientOut)
def me(current_client: Client = Depends(get_current_client)) -> Client:
    return current_client


@app.post("/scans", response_model=ScanRunOut)
def create_scan(
    request: ScanRequest,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> ScanRun:
    hostname, findings = perform_scan(request.target)
    score = compute_score(findings)

    scan_run = ScanRun(owner_id=current_client.id, target=hostname, score=score)
    scan_run.findings = [
        FindingRecord(
            category=f.category,
            severity=f.severity.name,
            title=f.title,
            detail=f.detail,
            recommendation=f.recommendation,
        )
        for f in findings
    ]

    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)
    return scan_run


@app.get("/scans", response_model=list[ScanSummaryOut])
def list_all_scans(
    db: Session = Depends(get_db), current_client: Client = Depends(get_current_client)
) -> list[ScanRun]:
    return (
        db.query(ScanRun)
        .filter(ScanRun.owner_id == current_client.id)
        .order_by(ScanRun.created_at.desc())
        .all()
    )


@app.get("/scans/{target}", response_model=list[ScanSummaryOut])
def list_scans_for_target(
    target: str,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> list[ScanRun]:
    return (
        db.query(ScanRun)
        .filter(ScanRun.owner_id == current_client.id, ScanRun.target == target)
        .order_by(ScanRun.created_at.desc())
        .all()
    )


@app.get("/scans/detail/{scan_id}", response_model=ScanRunOut)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> ScanRun:
    scan_run = db.get(ScanRun, scan_id)
    if scan_run is None or scan_run.owner_id != current_client.id:
        raise HTTPException(status_code=404, detail="Scan introuvable")
    return scan_run
