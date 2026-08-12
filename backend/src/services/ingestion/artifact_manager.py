from src.repositories.s3.storage_repository import S3Storage

class ArtifactManager:
    """
    Single source of truth for all S3 key conventions for one document.
    Injected into every pipeline stage. Never hard-code S3 paths elsewhere.
    """
    def __init__(self, document_id: str, s3_prefix: str, s3: S3Storage = None):
        self.document_id = document_id
        self.s3_prefix = s3_prefix
        self.s3 = s3 if s3 is not None else S3Storage()

    # --- Key Conventions ---
    
    def original_key(self, filename: str) -> str:
        return f"{self.s3_prefix}/original/{filename}"

    def parser_key(self, parser_name: str) -> str:
        return f"{self.s3_prefix}/parsers/{parser_name}.json"

    def canonical_key(self) -> str:
        return f"{self.s3_prefix}/canonical/canonical.json"

    def hierarchy_key(self) -> str:
        return f"{self.s3_prefix}/canonical/hierarchy.json"

    def knowledge_key(self, artifact: str) -> str:
        return f"{self.s3_prefix}/knowledge/{artifact}.json"

    def chunks_key(self) -> str:
        return f"{self.s3_prefix}/retrieval/chunks.json"

    def asset_key(self, filename: str) -> str:
        return f"{self.s3_prefix}/assets/{filename}"

    def page_key(self, page_num: int) -> str:
        return f"{self.s3_prefix}/pages/{page_num:03d}.png"

    def analysis_key(self, analysis_type: str, analysis_id: str, ext: str) -> str:
        # Note: Analysis for a specific document can go under its analysis folder.
        # However, multi-doc analyses go to analyses/{analysis_id}/. This is for per-document analysis.
        return f"{self.s3_prefix}/analysis/{analysis_type}/{analysis_id}.{ext}"

    def manifest_key(self) -> str:
        return f"{self.s3_prefix}/manifest.json"

    def log_key(self) -> str:
        return f"{self.s3_prefix}/ingestion_log.json"

    def prefix(self) -> str:
        return self.s3_prefix

    # --- S3 Helpers ---
    
    def upload_json(self, key: str, data: dict) -> str:
        return self.s3.upload_json(key, data)

    def upload_text(self, key: str, text: str) -> str:
        return self.s3.upload_text(key, text)

    def download_json(self, key: str) -> dict:
        return self.s3.download_json(key)

    def exists(self, key: str) -> bool:
        return self.s3.exists(key)

    # --- Manifest Management ---
    
    def init_manifest(self, doc_metadata: dict = None) -> None:
        """Initializes a blank manifest for the document."""
        manifest = {
            "document_id": self.document_id,
            "metadata": doc_metadata or {},
            "artifacts": {}
        }
        self.upload_json(self.manifest_key(), manifest)

    def read_manifest(self) -> dict:
        """Reads the current manifest from S3."""
        if not self.exists(self.manifest_key()):
            return {}
        return self.download_json(self.manifest_key())

    def update_manifest(self, updates: dict) -> None:
        """Updates the manifest with new keys or metadata."""
        manifest = self.read_manifest()
        if not manifest:
            manifest = {"document_id": self.document_id, "metadata": {}, "artifacts": {}}
        
        # Merge dictionaries (basic level)
        if "artifacts" in updates:
            manifest["artifacts"].update(updates["artifacts"])
        if "metadata" in updates:
            manifest["metadata"].update(updates["metadata"])
            
        self.upload_json(self.manifest_key(), manifest)
