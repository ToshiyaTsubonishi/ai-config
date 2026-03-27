"""Vendor-layer helpers for repo-managed external and official skill imports."""

from ai_config.vendor.models import (
    LegacyBootstrapResult,
    VendorImportResult,
    VendorImportSpec,
    VendorProvenance,
)
from ai_config.vendor.skill_vendor import (
    bootstrap_legacy_imports,
    import_skill_repo,
    remove_imported_skill,
    update_imported_skills,
)

__all__ = [
    "LegacyBootstrapResult",
    "VendorImportResult",
    "VendorImportSpec",
    "VendorProvenance",
    "bootstrap_legacy_imports",
    "import_skill_repo",
    "remove_imported_skill",
    "update_imported_skills",
]
