#!/usr/bin/env python3
"""Build and publish ai-config Cloud Run images to GHCR with provenance."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROVIDER_REPO = REPO_ROOT.parent / "ai-config-provider"
DOCKER_TAG_RE = re.compile(r"[^A-Za-z0-9_.-]+")
SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


@dataclass(frozen=True)
class ImageRelease:
    repository: str
    tag: str
    digest: str | None
    source_commit_sha: str
    source_repository: str
    bundle_version: str | None = None
    bundle_source_commit_sha: str | None = None

    @property
    def image_ref(self) -> str:
        if self.digest:
            return f"{self.repository}@{self.digest}"
        return f"{self.repository}:{self.tag}"


def _git_head(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    value = result.stdout.strip()
    if not value:
        raise ValueError(f"could not determine git HEAD for {repo_dir}")
    return value


def _sanitize_tag_fragment(value: str, *, fallback: str) -> str:
    cleaned = DOCKER_TAG_RE.sub("-", value.strip()).strip(".-")
    return cleaned or fallback


def default_selector_tag(commit_sha: str) -> str:
    short_sha = _sanitize_tag_fragment(commit_sha[:12], fallback="unknown")
    return f"selector-{short_sha}"


def default_provider_tag(commit_sha: str, bundle_version: str) -> str:
    short_sha = _sanitize_tag_fragment(commit_sha[:12], fallback="unknown")
    bundle_fragment = _sanitize_tag_fragment(bundle_version, fallback="bundle-unknown")
    return f"provider-{short_sha}-{bundle_fragment}"[:128]


def extract_buildx_digest(metadata: dict[str, Any]) -> str | None:
    direct = metadata.get("containerimage.digest")
    if isinstance(direct, str) and SHA256_RE.match(direct):
        return direct

    descriptor = metadata.get("containerimage.descriptor")
    if isinstance(descriptor, dict):
        nested = descriptor.get("digest")
        if isinstance(nested, str) and SHA256_RE.match(nested):
            return nested

    return None


def build_release_manifest(
    *,
    github_owner: str,
    generated_at: str,
    selector: ImageRelease,
    provider: ImageRelease,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "registry": "ghcr.io",
        "github_owner": github_owner,
        "registry_namespace": github_owner.lower(),
        "distribution": {
            "temporary_public_required_for_constrained_production": True,
            "note": "If production cannot authenticate to GHCR, temporarily switch the package visibility to public during deploy.",
        },
        "selector": {
            "repository": selector.repository,
            "tag": selector.tag,
            "digest": selector.digest,
            "image_ref": selector.image_ref,
            "source_commit_sha": selector.source_commit_sha,
            "source_repository": selector.source_repository,
        },
        "provider": {
            "repository": provider.repository,
            "tag": provider.tag,
            "digest": provider.digest,
            "image_ref": provider.image_ref,
            "source_commit_sha": provider.source_commit_sha,
            "source_repository": provider.source_repository,
            "bundle_version": provider.bundle_version,
            "bundle_source_commit_sha": provider.bundle_source_commit_sha,
        },
        "cloudrun": {
            "images": {
                "selector": selector.image_ref,
                "provider": provider.image_ref,
            },
            "provenance": {
                "selector_commit_sha": selector.source_commit_sha,
                "provider_commit_sha": provider.source_commit_sha,
                "provider_bundle_version": provider.bundle_version,
                "provider_bundle_source_commit_sha": provider.bundle_source_commit_sha,
            },
        },
    }


def _run(cmd: list[str], *, cwd: Path, dry_run: bool) -> None:
    print(f"+ {shlex.join(cmd)}", file=sys.stderr)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _run_capture(cmd: list[str], *, cwd: Path, dry_run: bool) -> subprocess.CompletedProcess[str] | None:
    print(f"+ {shlex.join(cmd)}", file=sys.stderr)
    if dry_run:
        return None
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _materialize_provider_bundle(ai_config_repo: Path, provider_repo: Path, *, dry_run: bool) -> None:
    npm_install = ["npm", "ci"] if (provider_repo / "package-lock.json").exists() else ["npm", "install"]
    _run(npm_install, cwd=provider_repo, dry_run=dry_run)
    _run(
        [
            "npm",
            "run",
            "bundle:from-ai-config",
            "--",
            "--ai-config-dir",
            str(ai_config_repo),
            "--output-dir",
            "provider-bundle",
        ],
        cwd=provider_repo,
        dry_run=dry_run,
    )


def _load_provider_bundle_metadata(provider_repo: Path) -> dict[str, Any]:
    metadata_path = provider_repo / "provider-bundle" / ".index" / "provider-bundle-metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"provider bundle metadata not found at {metadata_path}. "
            "Run bundle:from-ai-config before publishing."
        )
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"provider bundle metadata must be a JSON object: {metadata_path}")
    return payload


def _ensure_selector_index(ai_config_repo: Path, *, dry_run: bool) -> None:
    records_path = ai_config_repo / ".index" / "records.json"
    if records_path.exists():
        return

    _run([sys.executable, "-m", "pip", "install", "."], cwd=ai_config_repo, dry_run=dry_run)
    _run(
        [
            "ai-config-vendor-skills",
            "--repo-root",
            str(ai_config_repo),
            "sync-manifest",
        ],
        cwd=ai_config_repo,
        dry_run=dry_run,
    )
    _run(
        [
            "ai-config-index",
            "--repo-root",
            str(ai_config_repo),
            "--profile",
            "default",
        ],
        cwd=ai_config_repo,
        dry_run=dry_run,
    )


def buildx_available() -> bool:
    result = subprocess.run(
        ["docker", "buildx", "version"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def extract_push_digest(output: str) -> str | None:
    match = re.search(r"digest:\s*(sha256:[a-f0-9]{64})", output)
    if match:
        return match.group(1)
    return None


def _docker_build(
    *,
    context_dir: Path,
    dockerfile: Path,
    image_repository: str,
    tag: str,
    labels: dict[str, str],
    push: bool,
    platform: str,
    dry_run: bool,
) -> str | None:
    if not buildx_available():
        return _docker_build_legacy(
            context_dir=context_dir,
            dockerfile=dockerfile,
            image_repository=image_repository,
            tag=tag,
            labels=labels,
            push=push,
            platform=platform,
            dry_run=dry_run,
        )

    with tempfile.TemporaryDirectory(prefix="ai-config-ghcr-release-") as tmp_dir:
        metadata_path = Path(tmp_dir) / "buildx-metadata.json"
        cmd = [
            "docker",
            "buildx",
            "build",
            "--platform",
            platform,
            "--file",
            str(dockerfile),
            "--tag",
            f"{image_repository}:{tag}",
            "--metadata-file",
            str(metadata_path),
            "--pull",
        ]
        for key, value in labels.items():
            cmd.extend(["--label", f"{key}={value}"])
        cmd.append("--push" if push else "--load")
        cmd.append(str(context_dir))
        try:
            _run(cmd, cwd=context_dir, dry_run=dry_run)
        except subprocess.CalledProcessError as error:
            print(
                f"buildx path failed for {image_repository}:{tag}; falling back to docker build. "
                f"stderr={error.stderr!r}",
                file=sys.stderr,
            )
            return _docker_build_legacy(
                context_dir=context_dir,
                dockerfile=dockerfile,
                image_repository=image_repository,
                tag=tag,
                labels=labels,
                push=push,
                platform=platform,
                dry_run=dry_run,
            )
        if dry_run:
            return None
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        digest = extract_buildx_digest(payload)
        if push and digest is None:
            raise ValueError(f"buildx metadata did not contain a pushed digest for {image_repository}:{tag}")
        return digest


def _docker_build_legacy(
    *,
    context_dir: Path,
    dockerfile: Path,
    image_repository: str,
    tag: str,
    labels: dict[str, str],
    push: bool,
    platform: str,
    dry_run: bool,
) -> str | None:
    cmd = [
        "docker",
        "build",
        "--platform",
        platform,
        "--file",
        str(dockerfile),
        "--tag",
        f"{image_repository}:{tag}",
        "--pull",
    ]
    for key, value in labels.items():
        cmd.extend(["--label", f"{key}={value}"])
    cmd.append(str(context_dir))
    _run(cmd, cwd=context_dir, dry_run=dry_run)
    if not push:
        return None

    push_cmd = [
        "docker",
        "push",
        "--platform",
        platform,
        f"{image_repository}:{tag}",
    ]
    result = _run_capture(push_cmd, cwd=context_dir, dry_run=dry_run)
    if dry_run or result is None:
        return None

    combined_output = f"{result.stdout}\n{result.stderr}"
    digest = extract_push_digest(combined_output)
    if digest is None:
        raise ValueError(f"docker push output did not contain a digest for {image_repository}:{tag}")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish ai-config selector/provider images to GHCR")
    parser.add_argument("--github-owner", required=True, help="GHCR namespace owner (user or org)")
    parser.add_argument(
        "--provider-repo",
        type=Path,
        default=DEFAULT_PROVIDER_REPO,
        help="Path to the sibling ai-config-provider repository",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / ".artifacts" / "ghcr-release-manifest.json",
        help="Path to the generated release manifest JSON",
    )
    parser.add_argument("--selector-image-name", default="ai-config-selector-serving")
    parser.add_argument("--provider-image-name", default="ai-config-provider")
    parser.add_argument("--selector-tag", default="")
    parser.add_argument("--provider-tag", default="")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the built images to GHCR. Without this flag, the script only builds locally and emits tag refs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the npm/docker commands without executing them and emit tag-based refs.",
    )
    args = parser.parse_args(argv)

    ai_config_repo = REPO_ROOT
    provider_repo = args.provider_repo.resolve()
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    try:
        selector_commit_sha = _git_head(ai_config_repo)
        provider_commit_sha = _git_head(provider_repo)
        _ensure_selector_index(ai_config_repo, dry_run=args.dry_run)
        _materialize_provider_bundle(ai_config_repo, provider_repo, dry_run=args.dry_run)
        if args.dry_run:
            try:
                provider_bundle_metadata = _load_provider_bundle_metadata(provider_repo)
            except FileNotFoundError:
                provider_bundle_metadata = {
                    "bundle_version": "unknown",
                    "source_ai_config_commit_sha": selector_commit_sha,
                }
        else:
            provider_bundle_metadata = _load_provider_bundle_metadata(provider_repo)
        provider_bundle_version = str(provider_bundle_metadata.get("bundle_version") or "unknown").strip() or "unknown"
        provider_bundle_source_commit_sha = (
            str(provider_bundle_metadata.get("source_ai_config_commit_sha") or "").strip() or selector_commit_sha
        )

        selector_tag = args.selector_tag or default_selector_tag(selector_commit_sha)
        provider_tag = args.provider_tag or default_provider_tag(provider_commit_sha, provider_bundle_version)

        registry_namespace = args.github_owner.lower()
        selector_repository = f"ghcr.io/{registry_namespace}/{args.selector_image_name}"
        provider_repository = f"ghcr.io/{registry_namespace}/{args.provider_image_name}"

        selector_digest = _docker_build(
            context_dir=ai_config_repo,
            dockerfile=ai_config_repo / "deploy" / "cloudrun" / "Dockerfile",
            image_repository=selector_repository,
            tag=selector_tag,
            labels={
                "org.opencontainers.image.source": f"https://github.com/{args.github_owner}/ai-config",
                "org.opencontainers.image.revision": selector_commit_sha,
                "ai-config.dev/commit-sha": selector_commit_sha,
            },
            push=args.push,
            platform=args.platform,
            dry_run=args.dry_run,
        )
        provider_digest = _docker_build(
            context_dir=provider_repo,
            dockerfile=provider_repo / "Dockerfile",
            image_repository=provider_repository,
            tag=provider_tag,
            labels={
                "org.opencontainers.image.source": f"https://github.com/{args.github_owner}/ai-config-provider",
                "org.opencontainers.image.revision": provider_commit_sha,
                "ai-config.dev/commit-sha": provider_commit_sha,
                "ai-config.dev/provider-bundle-version": provider_bundle_version,
                "ai-config.dev/provider-bundle-source-commit-sha": provider_bundle_source_commit_sha,
            },
            push=args.push,
            platform=args.platform,
            dry_run=args.dry_run,
        )

        manifest = build_release_manifest(
            github_owner=args.github_owner,
            generated_at=generated_at,
            selector=ImageRelease(
                repository=selector_repository,
                tag=selector_tag,
                digest=selector_digest,
                source_commit_sha=selector_commit_sha,
                source_repository=f"https://github.com/{args.github_owner}/ai-config",
            ),
            provider=ImageRelease(
                repository=provider_repository,
                tag=provider_tag,
                digest=provider_digest,
                source_commit_sha=provider_commit_sha,
                source_repository=f"https://github.com/{args.github_owner}/ai-config-provider",
                bundle_version=provider_bundle_version,
                bundle_source_commit_sha=provider_bundle_source_commit_sha,
            ),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as error:  # pragma: no cover - exercised via CLI
        print(f"publish_ghcr_release.py: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "output": str(args.output),
                "push": args.push,
                "dry_run": args.dry_run,
                "selector_image_ref": manifest["selector"]["image_ref"],
                "provider_image_ref": manifest["provider"]["image_ref"],
                "provider_bundle_version": manifest["provider"]["bundle_version"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
