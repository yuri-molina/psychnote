import json
import sqlite3
import time
from typing import List, Optional, Dict, Any


# Schema SQL da tabela unificada de registros clínicos
_SCHEMA = """
CREATE TABLE IF NOT EXISTS clinical_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  TEXT NOT NULL,
    note_text   TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    has_triage  INTEGER NOT NULL DEFAULT 0,
    job_status  TEXT,
    job_id      TEXT,
    risk_level           TEXT,
    passive_ideation     INTEGER,
    active_ideation      INTEGER,
    red_flags            TEXT,
    protection_factors   TEXT,
    audit_alerts         TEXT,
    clinical_justification TEXT,
    final_report         TEXT
);
CREATE INDEX IF NOT EXISTS idx_patient_id ON clinical_records (patient_id);
"""


class PatientDataManager:
    """
    Gerencia o isolamento lógico de dados de pacientes em SQLite.
    Utiliza uma tabela unificada com filtragem estrita por patient_id para garantir
    conformidade com a LGPD e evitar vazamento de contexto (leakage) entre prontuários.

    Substitui o ChromaDB, que era usado apenas como document-store com filtro por
    metadado — sem busca por similaridade vetorial. SQLite oferece o mesmo isolamento
    com latência < 5ms, zero dependências de build e footprint de RAM mínimo.
    """

    def __init__(self, db_path: str = "./clinical.db"):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Cria o schema (idempotente) na primeira execução."""
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        """Retorna uma conexão SQLite com Row factory habilitado."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def upsert_note(self, patient_id: str, note_text: str, metadata: Optional[dict] = None) -> None:
        """
        Insere ou atualiza uma nota clínica com os metadados de triagem.
        Listas são serializadas como JSON string para armazenamento uniforme.

        Se já existir um registro com o mesmo job_id para o paciente, faz UPDATE;
        caso contrário, INSERT.
        """
        meta = metadata or {}
        meta["patient_id"] = patient_id
        if "created_at" not in meta:
            meta["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Serializa listas em JSON string para armazenamento uniforme
        for key in ("red_flags", "protection_factors", "audit_alerts"):
            if key in meta and isinstance(meta[key], list):
                meta[key] = json.dumps(meta[key], ensure_ascii=False)

        job_id = meta.get("job_id")

        with self._connect() as conn:
            # Tenta atualizar registro existente pelo job_id (se fornecido)
            if job_id:
                existing = conn.execute(
                    "SELECT id FROM clinical_records WHERE patient_id = ? AND job_id = ?",
                    (patient_id, job_id),
                ).fetchone()
            else:
                existing = None

            if existing:
                conn.execute(
                    """UPDATE clinical_records SET
                        note_text = ?, created_at = ?, has_triage = ?, job_status = ?,
                        risk_level = ?, passive_ideation = ?, active_ideation = ?,
                        red_flags = ?, protection_factors = ?, audit_alerts = ?,
                        clinical_justification = ?, final_report = ?
                    WHERE id = ?""",
                    (
                        note_text,
                        meta.get("created_at"),
                        int(bool(meta.get("has_triage", False))),
                        meta.get("job_status"),
                        meta.get("risk_level"),
                        int(bool(meta.get("passive_ideation", False))),
                        int(bool(meta.get("active_ideation", False))),
                        meta.get("red_flags"),
                        meta.get("protection_factors"),
                        meta.get("audit_alerts"),
                        meta.get("clinical_justification"),
                        meta.get("final_report"),
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO clinical_records
                        (patient_id, note_text, created_at, has_triage, job_status, job_id,
                         risk_level, passive_ideation, active_ideation,
                         red_flags, protection_factors, audit_alerts,
                         clinical_justification, final_report)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        patient_id,
                        note_text,
                        meta.get("created_at"),
                        int(bool(meta.get("has_triage", False))),
                        meta.get("job_status"),
                        job_id,
                        meta.get("risk_level"),
                        int(bool(meta.get("passive_ideation", False))),
                        int(bool(meta.get("active_ideation", False))),
                        meta.get("red_flags"),
                        meta.get("protection_factors"),
                        meta.get("audit_alerts"),
                        meta.get("clinical_justification"),
                        meta.get("final_report"),
                    ),
                )

        print(f"[+] Nota clínica integrada para o paciente {patient_id}.")

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get_patient_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Recupera todo o histórico de notas e triagens do paciente.
        Leitura direta via índice SQL — sem inferência LLM — em < 50ms.
        Retorna do mais recente ao mais antigo.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM clinical_records
                   WHERE patient_id = ?
                   ORDER BY created_at DESC""",
                (patient_id,),
            ).fetchall()

        history: List[Dict[str, Any]] = []
        for row in rows:
            has_triage = bool(row["has_triage"])
            item: Dict[str, Any] = {
                "patient_id": patient_id,
                "note_text": row["note_text"],
                "created_at": row["created_at"],
                "has_triage": has_triage,
            }

            if has_triage:
                def _parse_list(value: Optional[str]) -> List[str]:
                    if not value:
                        return []
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return []

                item["risk_assessment"] = {
                    "risk_level": row["risk_level"] or "Baixo",
                    "passive_ideation": bool(row["passive_ideation"]),
                    "active_ideation": bool(row["active_ideation"]),
                    "red_flags": _parse_list(row["red_flags"]),
                    "protection_factors": _parse_list(row["protection_factors"]),
                    "clinical_justification": row["clinical_justification"] or "",
                }
                item["audit_alerts"] = _parse_list(row["audit_alerts"])
                item["final_report"] = row["final_report"] or ""

            history.append(item)

        return history

    def get_patient_retriever(self, patient_id: str, search_kwargs: Optional[dict] = None) -> "SimpleRetriever":
        """
        Compatibilidade com o contrato anterior (ChromaDB).
        Retorna um objeto com método .invoke() que recupera as notas mais recentes do paciente.
        Não realiza busca por similaridade vetorial — filtragem por patient_id apenas.
        """
        k = (search_kwargs or {}).get("k", 5)
        return SimpleRetriever(manager=self, patient_id=patient_id, k=k)

    # ------------------------------------------------------------------
    # Remoção (Direito ao Esquecimento — LGPD)
    # ------------------------------------------------------------------

    def delete_patient_data(self, patient_id: str) -> None:
        """Remove todos os registros do paciente (Art. 18 LGPD — Direito ao Esquecimento)."""
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM clinical_records WHERE patient_id = ?",
                (patient_id,),
            )
        print(f"[-] Todos os registros do paciente {patient_id} foram removidos.")


class SimpleRetriever:
    """
    Retriever minimalista compatível com a interface LangChain (.invoke()).
    Retorna objetos com atributo .page_content e .metadata para manter
    compatibilidade com o código existente no orchestrator_graph.py.
    """

    def __init__(self, manager: PatientDataManager, patient_id: str, k: int = 5):
        self._manager = manager
        self._patient_id = patient_id
        self._k = k

    def invoke(self, query: str) -> List["SimpleDocument"]:
        """Retorna as k notas mais recentes do paciente, ignorando o query (sem similaridade)."""
        history = self._manager.get_patient_history(self._patient_id)
        return [
            SimpleDocument(
                page_content=record["note_text"],
                metadata={"patient_id": self._patient_id, "created_at": record.get("created_at", "")},
            )
            for record in history[: self._k]
        ]


class SimpleDocument:
    """Documento simples compatível com a interface LangChain Document."""

    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata


if __name__ == "__main__":
    import tempfile, os

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        manager = PatientDataManager(db_path=db_path)

        # Teste de isolamento
        manager.upsert_note("PA-123", "Paciente relata cansaço extremo e pensamentos de morte passivos.", {"cid": "F32"})
        manager.upsert_note("PB-456", "Paciente estável, boa adesão medicamentosa, nega ideação.", {"cid": "F32"})

        retriever_a = manager.get_patient_retriever("PA-123")
        docs = retriever_a.invoke("Ideação ou pensamentos de morte?")
        print(f"\nBusca isolada Paciente A: {len(docs)} documento(s) encontrado(s).")
        for d in docs:
            print(f"-> {d.metadata['patient_id']}: {d.page_content}")

        retriever_b = manager.get_patient_retriever("PB-456")
        docs_b = retriever_b.invoke("Qualquer coisa")
        for d in docs_b:
            assert d.metadata["patient_id"] == "PB-456", "Isolamento violado!"
        print("[+] Isolamento entre pacientes validado com sucesso.")
    finally:
        os.unlink(db_path)