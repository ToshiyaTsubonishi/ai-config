---
name: {skill_name}
description: {skill_description}
---

# {skill_title}

## 1. Overview
**What is this?**
{skill_description}

**When to use this?**
- [Condition 1: e.g., When the user asks for X]
- [Condition 2: e.g., When a specific error Y occurs]

## 2. Capability Instructions

### 2.1 Core Workflow
1.  **Understand:** Analyze the user's input to identify [Key Entities].
2.  **Plan:** Determine the necessary steps to [Goal].
3.  **Execute:** Use the provided tools or scripts to perform the action.
4.  **Verify:** Check if the output meets [Quality Criteria].

### 2.2 Tool/Script Usage
If this skill involves running specific scripts:

*   **Script:** `scripts/{script_name}.py`
*   **Purpose:** [Explain what the script does]
*   **Usage:**
    ```bash
    python scripts/{script_name}.py --arg1 <value>
    ```

## 3. Bundled Resources
- `assets/example_resource.md`: [Description]
- `references/example_ref.md`: [Description]

## 4. Examples (Few-Shot)

### Example 1: Standard Case
**User:** "[User Input Example]"
**Agent Action:**
1.  Analyzed intent...
2.  Ran script...
3.  Output: "[Expected Output Summary]"

## 5. Constraints & Ethics
*   [Constraint 1: e.g., Do not access PII without consent]
*   [Constraint 2: e.g., Max execution time 30s]
## Tool Permissions & Safety Boundary
This skill is explicitly authorized to use the following tools:
- `run_shell_command`
- `shell`
- `write_file`
- `read_file`
- `read_many_files`
- `replace`
- `edit`
- `list_files`
- `ls`
- `search_file_content`
- `grep`
- `find_files`
- `glob`
- `web_fetch`
- `web_search`
- `save_memory`
- `query_memory`
