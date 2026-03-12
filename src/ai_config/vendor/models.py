"""Data models for the vendor-layer skill import workflow."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROVENANCE_FILENAME = ".import.json"
PROVENANCE_SCHEMA_VERSION = 1


@dataclass(slots=True)
class VendorImportSpec:
    """Input for importing or updating a repo-managed external skill source."""

    source_url: str
    local_name: str | None = None
    branch: str | None = None
    force: bool = False
    dry_run: bool = False


@dataclass(slots=True)
class VendorProvenance:
    """Provenance metadata stored alongside imported skill directories."""

    schema_version: int
    source_url: str
    branch: str
    commit_sha: str
    original_paths: list[str]
    imported_at: str
    updated_at: str
    import_tool: str
    skill_count: int
    local_name: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_path(cls, path: Path) -> VendorProvenance:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid provenance payload: {path}")
        return cls(
            schema_version=int(payload.get("schema_version", PROVENANCE_SCHEMA_VERSION)),
            source_url=str(payload.get("source_url", "")),
            branch=str(payload.get("branch", "")),
            commit_sha=str(payload.get("commit_sha", "")),
            original_paths=[str(item) for item in payload.get("original_paths", []) or []],
            imported_at=str(payload.get("imported_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            import_tool=str(payload.get("import_tool", "")),
            skill_count=int(payload.get("skill_count", 0)),
            local_name=str(payload.get("local_name", "")),
        )


@dataclass(slots=True)
class VendorImportResult:
    """Outcome of an import, update, or removal operation."""

    local_name: str
    status: str
    skill_count: int = 0
    target_dir: str = ""
    provenance_path: str = ""
    orphaned_dirs: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class LegacyBootstrapResult:
    """Outcome of the temporary legacy provenance bootstrap utility."""

    local_name: str
    status: str
    skill_count: int = 0
    target_dir: str = ""
    provenance_path: str = ""
    source_url: str = ""
    message: str = ""
