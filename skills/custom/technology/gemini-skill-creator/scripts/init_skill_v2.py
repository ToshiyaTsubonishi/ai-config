import os
import argparse
import sys

def create_structure(base_path):
    os.makedirs(f"{base_path}/scripts", exist_ok=True)
    os.makedirs(f"{base_path}/references", exist_ok=True)
    os.makedirs(f"{base_path}/tests", exist_ok=True)

def create_skill_md(base_path, name, description):
    content = f"""---
name: {name}
description: {description}
allowed-tools: [Execute, ReadFile, ListDirectory]
---

# {name}

## 概要
(Describe what this skill does clearly)

## 使用方法 (Trigger)
Use when:
- User wants to perform {name.split('-')[-1]} on {name.split('-')[0]}.
- Specifically triggered by keywords: ...

## 実行コマンド
このスキルは以下のスクリプトを実行します。
```bash
python {base_path}/scripts/main.py --target "value"
```
"""
    with open(f"{base_path}/SKILL.md", "w", encoding='utf-8') as f:
        f.write(content)

def create_main_script(base_path):
    # argparseを含んだ堅牢なテンプレート
    content = """import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Skill script")
    # 必要な引数をここに定義させる
    parser.add_argument("--target", help="Target file or directory", required=True)
    parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")

    args = parser.parse_args()

    # 実装部分
    print(f"Processing target: {args.target}")

    # ここにメインロジックを記述
    # 成功時は標準出力に結果を出し、システムに通知する

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
"""
    with open(f"{base_path}/scripts/main.py", "w", encoding='utf-8') as f:
        f.write(content)

def create_test_script(base_path, name):
    # 動作確認用のテストスクリプト
    content = f"""import os
import subprocess
import sys

def test_execution():
    # スクリプトがエラーなく走るか確認する簡易テスト
    script_path = os.path.join("skills", "{name}", "scripts", "main.py")
    if not os.path.exists(script_path):
        # Try relative to the test file if running from inside the folder
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "main.py")

    print(f"Testing script at: {{script_path}}")

    # テスト実行
    # ダミーの引数を渡して実行確認
    # python paths might need adjustment depending on where this is run from.
    # We assume running from project root.
    
    cmd = [sys.executable, script_path, "--target", "test_dummy_data"]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Test Passed: Script runs successfully.")
        print("Output:", result.stdout)
    else:
        print("❌ Test Failed.")
        print("Error:", result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_execution()
"""
    with open(f"{base_path}/tests/test_basic.py", "w", encoding='utf-8') as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--desc", required=True)
    args = parser.parse_args()

    # バリデーション: 名前がルール違反していないか
    if not args.name.replace("-", "").replace("_", "").isalnum():
        print("Error: Name should only contain letters, numbers, hyphens, and underscores.")
        sys.exit(1)

    base_path = f"skills/{args.name}"
    if os.path.exists(base_path):
        print(f"Error: Skill '{args.name}' already exists at {base_path}.")
        sys.exit(1)

    create_structure(base_path)
    create_skill_md(base_path, args.name, args.desc)
    create_main_script(base_path)
    create_test_script(base_path, args.name)

    print(f"✅ Skill '{args.name}' scaffolded successfully.")
    print(f"   - Config: {base_path}/SKILL.md")
    print(f"   - Script: {base_path}/scripts/main.py")
    print(f"   - Test:   {base_path}/tests/test_basic.py")
    print("")
    print(f"Next Step: Edit {base_path}/scripts/main.py and run the test.")

if __name__ == "__main__":
    main()
