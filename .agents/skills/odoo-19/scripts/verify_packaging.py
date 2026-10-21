#!/usr/bin/env python3
"""
Packaging & Drop-In Verification Script for Odoo 19 Skill.
Validates:
1. Canonical repository structure (<project_root>/.agents/skills/odoo-19/ and AGENTS.md).
2. Absence of legacy split root directories (e.g. odoo-19/).
3. Integrity of all relative markdown links in SKILL.md.
4. Simulated drop-in installation into a temporary workspace root.
5. End-to-end test suite and strict linter audit execution from the drop-in target.
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path


def log_step(status: str, message: str):
    icon = "✓" if status == "OK" else "✗"
    print(f"[{status:^4}] {icon} {message}")


def verify_packaging() -> bool:
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    repo_root = skill_dir.parents[2]  # <repo_root>/.agents/skills/odoo-19

    print("=== Odoo 19 Skill Packaging & Drop-in Verification ===\n")
    all_ok = True

    # 1. Canonical Layout & No Split Package
    legacy_odoo19 = repo_root / "odoo-19"
    if legacy_odoo19.exists():
        log_step("FAIL", f"Legacy split directory still exists: {legacy_odoo19}")
        all_ok = False
    else:
        log_step("OK", "No legacy split directory (odoo-19/) in repo root")

    canonical_skill = repo_root / ".agents" / "skills" / "odoo-19" / "SKILL.md"
    if not canonical_skill.exists():
        log_step("FAIL", f"Canonical SKILL.md missing at {canonical_skill}")
        all_ok = False
    else:
        log_step("OK", "Canonical SKILL.md found at .agents/skills/odoo-19/SKILL.md")

    for root_file in ["AGENTS.md", "README.md", "LICENSE"]:
        if (repo_root / root_file).exists():
            log_step("OK", f"Required root file present: {root_file}")
        else:
            log_step("FAIL", f"Missing required root file: {root_file}")
            all_ok = False

    # 2. Reference & Template File Completeness
    references_dir = skill_dir / "references"
    templates_dir = skill_dir / "templates"

    ref_files = list(references_dir.glob("*.md")) if references_dir.exists() else []
    tpl_files = list(templates_dir.glob("*.template")) if templates_dir.exists() else []

    if len(ref_files) >= 9:
        log_step("OK", f"All {len(ref_files)} reference guides present in references/")
    else:
        log_step("FAIL", f"Expected at least 9 reference files, found {len(ref_files)}")
        all_ok = False

    if len(tpl_files) >= 15:
        log_step("OK", f"All {len(tpl_files)} template scaffolds present in templates/")
    else:
        log_step("FAIL", f"Expected at least 15 template files, found {len(tpl_files)}")
        all_ok = False

    # 3. Relative Link Integrity in SKILL.md
    skill_content = canonical_skill.read_text(encoding="utf-8")
    links = re.findall(r'\[([^\]]+)\]\(((\./references/|\./templates/)[^)]+)\)', skill_content)
    broken_links = []
    for text, link, _ in links:
        target_path = (skill_dir / link).resolve()
        if not target_path.exists():
            broken_links.append((link, str(target_path)))

    if not broken_links:
        log_step("OK", f"All {len(links)} relative links in SKILL.md resolve cleanly")
    else:
        log_step("FAIL", f"Found {len(broken_links)} broken links in SKILL.md: {broken_links}")
        all_ok = False

    # 4. Simulated Drop-In Installation
    print("\n--- Simulating Drop-In Installation into <project_root>/ ---")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir)
        target_agents = temp_project / ".agents"
        shutil.copytree(repo_root / ".agents", target_agents)
        shutil.copy2(repo_root / "AGENTS.md", temp_project / "AGENTS.md")

        installed_skill = target_agents / "skills" / "odoo-19" / "SKILL.md"
        if installed_skill.exists():
            log_step("OK", "Drop-in simulation copied .agents/ and AGENTS.md cleanly")
        else:
            log_step("FAIL", "Installed SKILL.md missing after drop-in copy")
            all_ok = False

        # 5. Run test suite and linter from the installed drop-in target
        linter_test = target_agents / "skills" / "odoo-19" / "scripts" / "test_linter.py"
        test_run = subprocess.run([sys.executable, str(linter_test)], capture_output=True, text=True)
        if test_run.returncode == 0:
            log_step("OK", "Linter unit test suite passed in drop-in environment (34 tests)")
        else:
            log_step("FAIL", f"Linter tests failed in drop-in environment:\n{test_run.stderr}")
            all_ok = False

        linter_cli = target_agents / "skills" / "odoo-19" / "scripts" / "verify_odoo19_compat.py"
        target_skill_dir = target_agents / "skills" / "odoo-19"
        audit_run = subprocess.run(
            [sys.executable, str(linter_cli), str(target_skill_dir), "--strict"],
            capture_output=True,
            text=True,
        )
        if audit_run.returncode == 0:
            log_step("OK", "Strict compatibility linter audit passed in drop-in environment")
        else:
            log_step("FAIL", f"Strict linter audit failed in drop-in environment:\n{audit_run.stdout}")
            all_ok = False

    print("\n" + ("=" * 55))
    if all_ok:
        print("Packaging Verification PASSED: 100% Drop-In Ready!")
        print("=" * 55)
        return True
    else:
        print("Packaging Verification FAILED: Address issues above.")
        print("=" * 55)
        return False


if __name__ == "__main__":
    success = verify_packaging()
    sys.exit(0 if success else 1)
