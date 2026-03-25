"""Compatibility import shim for the external dispatch runtime package."""

from ai_config.dispatch._compat import load_external_module

create_dispatch_agent = load_external_module("graph").create_dispatch_agent

__all__ = ["create_dispatch_agent"]
