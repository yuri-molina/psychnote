"""
main.py — Entrypoint da API PsicRE-AI (FastAPI)

Responsabilidade: instanciar o app FastAPI, registrar os routers,
configurar CORS e expor os metadados da PoC para o Swagger UI.

Inicialização:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import sys
import os

# Garante que o diretório raiz do projeto esteja no PYTHONPATH,
# permitindo imports absolutos de analytics, config, database, orchestrator.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.triage import router as triage_router


# ---------------------------------------------------------------------------
# Lifespan: inicialização e teardown controlados
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Gerencia o ciclo de vida da aplicação.
    O PsychiatricOrchestrator (singleton) é carregado preguiçosamente na
    primeira requisição via lru_cache em triage.py — não é necessário
    pré-aquecer aqui para manter o startup rápido.
    """
    print("[+] PsicRE-AI API iniciada. Aguardando requisições...")
    yield
    print("[-] PsicRE-AI API encerrada.")


# ---------------------------------------------------------------------------
# Instância do app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PsicRE-AI — Edge AI para Gestão de Risco de Suicídio",
    description=(
        "Plataforma de análise semântica e auditoria de prontuários psiquiátricos via Edge AI. "
        "Execução 100% local em conformidade com a LGPD. "
        "Pipeline: Triagem Estruturada (Pydantic) → Contexto Longitudinal (ChromaDB) → Auditoria de Conduta Determinística → Parecer Executivo."
    ),
    version="0.1.0-poc",
    contact={
        "name": "MBA PoC — PsicRE-AI",
    },
    license_info={
        "name": "Uso Acadêmico — MBA TCC",
    },
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------------------------
# CORS (necessário se o front-end consumir a API localmente)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Registro de Routers
# ---------------------------------------------------------------------------

app.include_router(triage_router)


# ---------------------------------------------------------------------------
# Health check (útil para validar startup e testes de integração)
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Infraestrutura"], summary="Verificação de saúde da API")
async def health_check() -> dict:
    """Retorna status da API. Não aciona o LLM."""
    return {"status": "ok", "service": "PsicRE-AI", "version": app.version}


# ---------------------------------------------------------------------------
# Entrypoint direto (desenvolvimento)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
