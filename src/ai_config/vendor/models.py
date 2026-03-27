"""Data models for the vendor-layer skill import workflow."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROVENANCE_FILENAME = ".import.json"
PROVENANCE_SCHEMA_VERSION = 1
DEFAULT_VENDOR_MANIFEST = "config/vendor_skills.yaml"
DEFAULT_EXTERNAL_TARGET_ROOT = "skills/external"
DEFAULT_SKILLS_SH_OFFICIAL_MANIFEST = "config/skills_sh_official.yaml"
DEFAULT_SKILLS_SH_OFFICIAL_SKIPPED_REPORT = "config/skills_sh_official_skipped.json"
DEFAULT_OFFICIAL_TARGET_ROOT = "skills/official"
VENDOR_STATUS_SCHEMA_VERSION = 1


@dataclass(slots=True)
class VendorImportSpec:
    """Input for importing or updating a repo-managed external skill source."""

    source_url: str
    local_name: str | None = None
    branch: str | None = None
    ref: str | None = None
    target_root: str = DEFAULT_EXTERNAL_TARGET_ROOT
    import_tool: str | None = None
    force: bool = False
    dry_run: bool = False


@dataclass(slots=True)
class VendorProvenance:
    """Provenance metadata stored alongside imported skill directories."""

    schema_version: int
    source_url: str
    branch: str
    requested_ref: str | None
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
        requested_ref = payload.get("requested_ref")
        return cls(
            schema_version=int(payload.get("schema_version", PROVENANCE_SCHEMA_VERSION)),
            source_url=str(payload.get("source_url", "")),
            branch=str(payload.get("branch", "")),
            requested_ref=None if requested_ref in (None, "") else str(requested_ref),
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


@dataclass(slots=True)
class VendorManifestEntry:
    """A curated external skill source pinned for reproducible materialization."""

    name: str
    source_url: str
    local_name: str
    branch: str = "main"
    ref: str | None = None


@dataclass(slots=True)
class VendorManifest:
    """Manifest of curated external skill sources."""

    version: str = "1.0.0"
    sources: list[VendorManifestEntry] = field(default_factory=list)


@dataclass(slots=True)
class VendorSyncResult:
    """Outcome of manifest-driven materialization and optional pruning."""

    local_name: str
    status: str
    target_dir: str = ""
    provenance_path: str = ""
    source_url: str = ""
    requested_ref: str | None = None
    message: str = ""


@dataclass(slots=True)
class LegacyCleanupResult:
    """Outcome of converting a legacy skill submodule into a local artifact."""

    local_name: str
    status: str
    target_dir: str = ""
    provenance_path: str = ""
    actions: list[str] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class VendorStatusEntry:
    """Read-only inspection result for one vendor-managed or local external directory."""

    manifest_name: str | None
    local_name: str
    status: str
    source_url: str = ""
    branch: str = ""
    target_dir: str = ""
    provenance_path: str = ""
    manifest_ref: str | None = None
    provenance_commit_sha: str | None = None
    provenance_requested_ref: str | None = None
    skill_count: int = 0
    target_exists: bool = False
    provenance_exists: bool = False
    is_git_submodule: bool = False
    git_ignored: bool = False
    is_manifest_managed: bool = False
    message: str = ""


@dataclass(slots=True)
class VendorStatusSummary:
    """Aggregate counts for vendor inspection statuses."""

    total_manifest_entries: int = 0
    ready: int = 0
    needs_align: int = 0
    needs_sync: int = 0
    missing: int = 0
    legacy_submodule: int = 0
    missing_provenance: int = 0
    extra_local: int = 0
    unmanaged_local: int = 0


@dataclass(slots=True)
class VendorStatusReport:
    """Stable JSON/report surface for vendor-layer observability."""

    schema_version: int
    generated_at: str
    repo_root: str
    manifest_path: str
    summary: VendorStatusSummary
    entries: list[VendorStatusEntry] = field(default_factory=list)
    manifest_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
