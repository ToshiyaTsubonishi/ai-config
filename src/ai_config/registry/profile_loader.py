"""Index profile loader and source-path filtering."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

import yaml

from ai_config.registry.models import ToolRecord

DEFAULT_PROFILE_CONFIG = "config/index_profiles.yaml"


@dataclass
class IndexProfile:
    name: str
    include: list[str]
    exclude: list[str]


def load_profiles(repo_root: Path, config_rel: str = DEFAULT_PROFILE_CONFIG) -> dict[str, IndexProfile]:
    config_path = repo_root / config_rel
    if not config_path.exists():
        return {
            "default": IndexProfile(name="default", include=["**"], exclude=[]),
            "full": IndexProfile(name="full", include=["**"], exclude=[]),
        }

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    profiles_raw = raw.get("profiles") or {}
    profiles: dict[str, IndexProfile] = {}
    for name, cfg in profiles_raw.items():
        cfg = cfg or {}
        include = [str(x) for x in (cfg.get("include") or ["**"])]
        exclude = [str(x) for x in (cfg.get("exclude") or [])]
        profiles[str(name)] = IndexProfile(name=str(name), include=include, exclude=exclude)

    if "full" not in profiles:
        profiles["full"] = IndexProfile(name="full", include=["**"], exclude=[])
    if "default" not in profiles:
        profiles["default"] = IndexProfile(name="default", include=["**"], exclude=[])
    return profiles


def filter_records_by_profile(records: list[ToolRecord], profile: IndexProfile) -> list[ToolRecord]:
    filtered: list[ToolRecord] = []
    include = profile.include or ["**"]
    exclude = profile.exclude or []
    for record in records:
        source = record.source_path
        included = any(fnmatch(source, pattern) for pattern in include)
        if not included:
            continue
        if any(fnmatch(source, pattern) for pattern in exclude):
            continue
        filtered.append(record)
    return filtered
