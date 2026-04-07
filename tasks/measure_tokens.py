"""
Measure the token usage of ai-config MCP responses.

Simulates a typical agent invocation:
  - search_tools (returns 5 results, compact)
  - get_tool_detail x2  (2 SKILL details)
  - get_tool_detail x1  (1 MCP server detail)
  - list_mcp_server_tools (downstream MCP tools list)

Counts both character count and tiktoken token count (cl100k_base).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

# ── Token counter ──────────────────────────────────────────────────────────
def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (cl100k_base = GPT-4 / Claude compatible)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: rough approximation (1 token ≈ 4 chars)
        return len(text) // 4


# ── Load index ─────────────────────────────────────────────────────────────
from ai_config.mcp_server.tools import ToolIndex

index_dir = repo_root / ".index"
tool_index = ToolIndex(index_dir)

print("=" * 70)
print("ai-config Token Usage Measurement")
print("Scenario: search_tools + 2 SKILL details + 1 MCP detail")
print("=" * 70)

total_chars = 0
total_tokens = 0
results_summary = []

# ── Step 1: search_tools ───────────────────────────────────────────────────
query = "web search and browsing"
top_k = 5
results = tool_index.search(query, top_k=top_k)
search_json = json.dumps({"count": len(results), "results": results}, ensure_ascii=False)

chars = len(search_json)
tokens = count_tokens(search_json)
total_chars += chars
total_tokens += tokens
results_summary.append({
    "step": f"search_tools(query='{query}', top_k={top_k})",
    "chars": chars,
    "tokens": tokens,
    "preview": search_json[:200] + "..." if len(search_json) > 200 else search_json,
})

print(f"\n[1] search_tools: {chars} chars / {tokens} tokens")
print(f"    Query: '{query}', top_k={top_k}")
print(f"    Results: {len(results)} tools returned")
for r in results:
    print(f"      - {r['id']} ({r['tool_kind']}, {r['layer']})")

# ── Step 2: get_tool_detail for 2 SKILLs ──────────────────────────────────
skill_ids = [r["id"] for r in results if r["tool_kind"] == "skill"][:2]
if len(skill_ids) < 2:
    # fallback: pick first 2 from results
    skill_ids = [r["id"] for r in results[:2]]

for i, tool_id in enumerate(skill_ids, start=2):
    detail = tool_index.get_detail(tool_id)
    if detail is None:
        detail_json = json.dumps({"error": f"Tool '{tool_id}' not found."})
    else:
        detail_json = json.dumps(detail, ensure_ascii=False)

    chars = len(detail_json)
    tokens = count_tokens(detail_json)
    total_chars += chars
    total_tokens += tokens
    results_summary.append({
        "step": f"get_tool_detail('{tool_id}') [SKILL]",
        "chars": chars,
        "tokens": tokens,
    })
    print(f"\n[{i}] get_tool_detail('{tool_id}') [SKILL]: {chars} chars / {tokens} tokens")

# ── Step 3: get_tool_detail for 1 MCP ─────────────────────────────────────
mcp_ids = [r["id"] for r in results if r["tool_kind"] == "mcp_server"][:1]
if not mcp_ids:
    # fallback: search for an mcp_server specifically
    mcp_results = tool_index.search("mcp server firecrawl", top_k=5)
    mcp_ids = [r["id"] for r in mcp_results if r["tool_kind"] == "mcp_server"][:1]
    if not mcp_ids:
        # Just grab any mcp
        for rec in tool_index.records:
            if rec.tool_kind == "mcp_server":
                mcp_ids = [rec.id]
                break

if mcp_ids:
    mcp_id = mcp_ids[0]
    detail = tool_index.get_detail(mcp_id)
    if detail is None:
        detail_json = json.dumps({"error": f"Tool '{mcp_id}' not found."})
    else:
        detail_json = json.dumps(detail, ensure_ascii=False)

    chars = len(detail_json)
    tokens = count_tokens(detail_json)
    total_chars += chars
    total_tokens += tokens
    results_summary.append({
        "step": f"get_tool_detail('{mcp_id}') [MCP]",
        "chars": chars,
        "tokens": tokens,
    })
    print(f"\n[{len(results_summary)}] get_tool_detail('{mcp_id}') [MCP]: {chars} chars / {tokens} tokens")
else:
    print("\n[MCP] No MCP server found in results, skipping.")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"{'Step':<55} {'Chars':>8} {'Tokens':>8}")
print("-" * 73)
for r in results_summary:
    print(f"{r['step']:<55} {r['chars']:>8,} {r['tokens']:>8,}")
print("-" * 73)
print(f"{'TOTAL':<55} {total_chars:>8,} {total_tokens:>8,}")
print()

# ── Context window comparison ──────────────────────────────────────────────
print("Context Window Reference:")
print(f"  Claude 3.5 Sonnet: 200K tokens  → using {total_tokens/200000*100:.2f}%")
print(f"  GPT-4o:            128K tokens  → using {total_tokens/128000*100:.2f}%")
print(f"  Gemini 1.5 Pro:   1000K tokens  → using {total_tokens/1000000*100:.3f}%")
print()
print(f"Estimated 'all tools loaded' baseline:")

# estimate if ALL tools were in context
records = tool_index.records
all_text = " ".join(r.search_text for r in records)
all_tokens = count_tokens(all_text)
print(f"  Total tools: {len(records)}")
print(f"  All search_text combined: {len(all_text):,} chars / ~{all_tokens:,} tokens")
print(f"  Savings vs ai-config selector (2 skill + 1 mcp): {all_tokens - total_tokens:,} tokens ({(all_tokens - total_tokens)/all_tokens*100:.1f}% reduction)")
