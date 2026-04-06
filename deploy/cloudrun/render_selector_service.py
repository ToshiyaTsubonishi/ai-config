#!/usr/bin/env python3
"""Render a Cloud Run Service manifest for ai-config selector-serving."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "ai-config-selector.service.yaml"


def _replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Expected exactly one match for pattern: {pattern}")
    return updated


def render_selector_service(
    *,
    project_id: str,
    project_number: str,
    region: str,
    image: str,
    output_path: Path,
    service_name: str = "ai-config-selector",
    service_account: str | None = None,
) -> None:
    _ = project_id  # Included for CLI symmetry with other deploy commands.
    text = TEMPLATE_PATH.read_text(encoding="utf-8")

    text = _replace_once(text, r"^  name: ai-config-selector$", f"  name: {service_name}")
    text = _replace_once(text, r'^  namespace: "424287527578"$', f'  namespace: "{project_number}"')
    text = _replace_once(
        text,
        r"^    cloud\.googleapis\.com/location: asia-northeast1$",
        f"    cloud.googleapis.com/location: {region}",
    )
    text = _replace_once(
        text,
        r"^      - name: ai-config-selector-1$",
        f"      - name: {service_name}-1",
    )
    text = _replace_once(
        text,
        r"^        image: .+$",
        f"        image: {image}",
    )

    if service_account:
        text = _replace_once(
            text,
            r"^      serviceAccountName: .+$",
            f"      serviceAccountName: {service_account}",
        )
    else:
        text = _replace_once(text, r"^      serviceAccountName: .+\n", "")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", required=True, help="GCP project ID (for documentation parity)")
    parser.add_argument("--project-number", required=True, help="GCP project number used as the Cloud Run namespace")
    parser.add_argument("--region", required=True, help="Cloud Run region")
    parser.add_argument("--image", required=True, help="Container image URL for ai-config-selector-serving")
    parser.add_argument(
        "--service-name",
        default="ai-config-selector",
        help="Cloud Run service name (default: ai-config-selector)",
    )
    parser.add_argument(
        "--service-account",
        default=None,
        help="Optional service account email. If omitted, the field is removed from the rendered manifest.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output path for the rendered YAML",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_selector_service(
        project_id=args.project_id,
        project_number=args.project_number,
        region=args.region,
        image=args.image,
        output_path=args.output,
        service_name=args.service_name,
        service_account=args.service_account,
    )


if __name__ == "__main__":
    main()
