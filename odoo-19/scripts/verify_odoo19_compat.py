#!/usr/bin/env python3
"""
Odoo 19 Compatibility Linter & Static Audit Tool
Scans Odoo addons, XML views, and Python files for deprecated antipatterns and breaking changes.
Supports 3 severity levels: ERROR, WARNING, INFO.
"""

import os
import sys
import re
import argparse
from pathlib import Path


# ANSI Color Codes
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_CYAN = "\033[96m"
COLOR_BLUE = "\033[94m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


class Issue:
    def __init__(self, file_path, line_no, severity, code, message, fix_hint, snippet):
        self.file_path = file_path
        self.line_no = line_no
        self.severity = severity  # 'ERROR', 'WARNING', or 'INFO'
        self.code = code
        self.message = message
        self.fix_hint = fix_hint
        self.snippet = snippet.strip()


def check_xml_lines(lines: list[str], file_path: str = "<memory>") -> list[Issue]:
    issues = []
    in_list_view = False

    for idx, line in enumerate(lines, start=1):
        # Track list context
        if "<list" in line:
            in_list_view = True
        if "</list>" in line:
            in_list_view = False

        # 1. <tree> view root tag
        if re.search(r"<\s*tree(\s+|>)", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "XML_TREE_VIEW",
                    "<tree> view tag is deprecated in Odoo 19.0. Use <list> instead.",
                    "Replace '<tree>' with '<list>' and '</tree>' with '</list>'",
                    line,
                )
            )

        # 2. attrs="..." attribute
        if re.search(r'\battrs\s*=\s*["\']', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "XML_ATTRS_DEPRECATED",
                    "Dynamic 'attrs' attribute is removed. Use direct Python expressions.",
                    "Use invisible=\"condition\", readonly=\"condition\", or required=\"condition\"",
                    line,
                )
            )

        # 3. states="..." attribute
        if re.search(r'\bstates\s*=\s*["\']', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "XML_STATES_DEPRECATED",
                    "'states' attribute is removed in modern Odoo.",
                    "Replace with invisible=\"state not in ('state1', 'state2')\"",
                    line,
                )
            )

        # 4. view_mode with tree
        if re.search(r'view_mode["\']\s*>\s*.*?\btree\b', line) or re.search(r'view_mode\s*=\s*["\'][^"\']*\btree\b', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "XML_VIEW_MODE_TREE",
                    "Action 'view_mode' contains 'tree'. In Odoo 19, the view type is 'list'.",
                    "Change 'tree,form' to 'list,form'",
                    line,
                )
            )

        # 5. QWeb t-esc or t-raw
        if re.search(r'\bt-(esc|raw)\s*=\s*["\']', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "XML_T_ESC_DEPRECATED",
                    "'t-esc' and 't-raw' are deprecated in Odoo 19. Use 't-out' for HTML-escaped output.",
                    "Replace 't-esc' / 't-raw' with 't-out'",
                    line,
                )
            )

        # 6. Legacy chatter container div
        if re.search(r'<\s*div[^>]*class\s*=\s*["\'][^"\']*oe_chatter', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "XML_LEGACY_CHATTER",
                    "Legacy 'div.oe_chatter' structure. In Odoo 19, use the modern '<chatter/>' component tag.",
                    "Replace chatter container div with '<chatter/>'",
                    line,
                )
            )

        # 7. invisible used on column inside <list> instead of column_invisible
        if in_list_view and re.search(r'<\s*field[^>]+invisible\s*=', line) and not re.search(r'column_invisible\s*=', line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "XML_LIST_COLUMN_INVISIBLE",
                    "Field inside <list> uses 'invisible='. In list views, prefer 'column_invisible=' to properly toggle column presence.",
                    "Change 'invisible=\"...\"' to 'column_invisible=\"...\"'",
                    line,
                )
            )

    return issues


def check_xml_file(path: Path) -> list[Issue]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return [Issue(str(path), 0, "ERROR", "READ_FAIL", f"Failed to read file: {e}", "", "")]
    return check_xml_lines(lines, str(path))


def check_python_lines(lines: list[str], file_path: str = "<memory>") -> list[Issue]:
    issues = []

    for idx, line in enumerate(lines, start=1):
        # Skip pure comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # 1. self._cr, record._cr deprecation
        if re.search(r"\b(self|record|rec)\._cr\b", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_DEPRECATED_CR",
                    "Record attribute '._cr' is deprecated in Odoo 19.0.",
                    "Use 'self.env.cr' instead of 'self._cr'",
                    line,
                )
            )

        # 2. self._uid, record._uid deprecation
        if re.search(r"\b(self|record|rec)\._uid\b", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_DEPRECATED_UID",
                    "Record attribute '._uid' is deprecated in Odoo 19.0.",
                    "Use 'self.env.uid' instead of 'self._uid'",
                    line,
                )
            )

        # 3. self._context, record._context deprecation
        if re.search(r"\b(self|record|rec)\._context\b", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_DEPRECATED_CONTEXT",
                    "Record attribute '._context' is deprecated in Odoo 19.0.",
                    "Use 'self.env.context' instead of 'self._context'",
                    line,
                )
            )

        # 4. odoo.osv deprecation
        if re.search(r"\b(from\s+odoo\.osv\b|import\s+odoo\.osv\b)", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_DEPRECATED_OSV",
                    "'odoo.osv' is completely deprecated in Odoo 19.0.",
                    "Use standard 'odoo.models.Model' or remove legacy osv imports.",
                    line,
                )
            )

        # 5. Controller route type='json'
        if re.search(r"@http\.route\(.*?type\s*=\s*['\"]json['\"]", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_ROUTE_TYPE_JSON",
                    "Controller route type='json' is removed in Odoo 19. Use type='jsonrpc'.",
                    "Replace 'type=\"json\"' with 'type=\"jsonrpc\"'",
                    line,
                )
            )

        # 6. Legacy name_get
        if re.search(r"def\s+name_get\s*\(", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_DEPRECATED_NAME_GET",
                    "'name_get' method is deprecated.",
                    "Implement compute method for 'display_name' instead.",
                    line,
                )
            )

        # 7. Manifest hook signature (cr, registry)
        if re.search(r"def\s+(pre_init_hook|post_init_hook|uninstall_hook)\s*\(\s*(cr|cursor)\s*,", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_DEPRECATED_HOOK_SIGNATURE",
                    "Module manifest hooks in modern Odoo accept a single 'env' parameter.",
                    "Change signature to 'def hook_name(env):'",
                    line,
                )
            )

        # 8. Unsafe SQL string interpolation in execute
        if re.search(r"\.cr\.execute\s*\(\s*[\"'].*?%s.*?[\"']\s*%", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_UNSAFE_SQL",
                    "Unsafe string formatting inside cr.execute.",
                    "Use 'odoo.tools.SQL' wrapper: self.env.cr.execute(SQL('...', val))",
                    line,
                )
            )

        # 9. Legacy _sql_constraints list
        if re.search(r"^\s*_sql_constraints\s*=", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_SQL_CONSTRAINTS_DEPRECATED",
                    "'_sql_constraints' list is deprecated in Odoo 19. Declare SQL Table Objects instead.",
                    "Use '_name = models.Constraint(...)' or '_unique = models.UniqueIndex(...)'",
                    line,
                )
            )

        # 10. SQL Table Object missing leading underscore
        table_obj_match = re.search(r"^\s*([a-zA-Z0-9_]+)\s*=\s*models\.(Constraint|Index|UniqueIndex)\(", line)
        if table_obj_match and not table_obj_match.group(1).startswith("_"):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_TABLE_OBJECT_UNDERSCORE",
                    f"SQL table object attribute '{table_obj_match.group(1)}' MUST begin with an underscore '_'.",
                    f"Rename to '_{table_obj_match.group(1)}'",
                    line,
                )
            )

        # 11. create override missing @api.model_create_multi
        if re.search(r"def\s+create\s*\(\s*self\s*,\s*vals_list\s*\)\s*:", line):
            prev_lines = "".join(lines[max(0, idx - 4):idx - 1])
            if "@api.model_create_multi" not in prev_lines:
                issues.append(
                    Issue(
                        file_path,
                        idx,
                        "WARNING",
                        "PY_CREATE_MISSING_MODEL_CREATE_MULTI",
                        "'def create(self, vals_list)' should be decorated with '@api.model_create_multi'.",
                        "Add '@api.model_create_multi' above the create method",
                        line,
                    )
                )

        # 12. Deprecated group_operator (replaced by aggregator since 18.0)
        if re.search(r"\bgroup_operator\s*=", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_GROUP_OPERATOR_DEPRECATED",
                    "'group_operator' is deprecated. Use 'aggregator' instead.",
                    "Replace 'group_operator=\"...\"' with 'aggregator=\"...\"'",
                    line,
                )
            )

        # 13. Deprecated request.cr / request.uid / request.context (must use request.env.*)
        req_match = re.search(r"\brequest\.(cr|uid|context)\b", line)
        if req_match:
            attr = req_match.group(1)
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_REQUEST_DEPRECATED_ATTR",
                    f"'request.{attr}' is deprecated in Odoo 19. Use 'request.env.{attr}' directly.",
                    f"Replace 'request.{attr}' with 'request.env.{attr}'",
                    line,
                )
            )

        # 14. Deprecated force_company in context
        if re.search(r"['\"]force_company['\"]\s*:", line) or re.search(r"\bforce_company\s*=", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "ERROR",
                    "PY_FORCE_COMPANY_DEPRECATED",
                    "Context key 'force_company' is no longer supported in Odoo 19.",
                    "Use 'record.with_company(company)' instead",
                    line,
                )
            )

        # 15. Deprecated @ormcache_context
        if re.search(r"@\w*ormcache_context\b", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_ORMCACHE_CONTEXT_DEPRECATED",
                    "'@ormcache_context' is deprecated in Odoo 19. Use '@ormcache' directly.",
                    "Replace '@ormcache_context' with '@ormcache' and access context keys via self.env.context.get()",
                    line,
                )
            )

        # 16. Uppercase domain operators
        domain_match = re.search(r"\(\s*['\"][a-zA-Z0-9_\.]+['\"]\s*,\s*['\"]([A-Z\s]+)['\"]", line)
        if domain_match and domain_match.group(1) in ("LIKE", "ILIKE", "IN", "NOT IN", "NOT LIKE", "NOT ILIKE"):
            op = domain_match.group(1)
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "WARNING",
                    "PY_DOMAIN_UPPERCASE_OPERATOR",
                    f"Domain operator '{op}' should be lowercase in Odoo 19.",
                    f"Replace '{op}' with '{op.lower()}'",
                    line,
                )
            )

        # 17. INFO: Manual cr.commit()
        if re.search(r"\b(self\.env\.cr|cr)\.commit\(\)", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "INFO",
                    "PY_MANUAL_CR_COMMIT",
                    "Manual cr.commit() detected. Normal operations rely on Odoo's automatic transaction lifecycle.",
                    "Verify explicit justification, idempotency, and recovery design for chunked batch cron jobs.",
                    line,
                )
            )

        # 18. INFO: Stored computed field with precompute=True on parent
        if re.search(r"\bprecompute\s*=\s*True\b", line):
            issues.append(
                Issue(
                    file_path,
                    idx,
                    "INFO",
                    "PY_PRECOMPUTE_NOTICE",
                    "Field declared with precompute=True.",
                    "Verify this is on batch-created One2many child lines. Avoid on standalone parent models where it adds single-insert overhead.",
                    line,
                )
            )

    return issues


def check_python_file(path: Path) -> list[Issue]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return [Issue(str(path), 0, "ERROR", "READ_FAIL", f"Failed to read file: {e}", "", "")]
    return check_python_lines(lines, str(path))


def scan_target(target_path: Path) -> list[Issue]:
    all_issues = []
    if target_path.is_file():
        if target_path.suffix == ".xml":
            all_issues.extend(check_xml_file(target_path))
        elif target_path.suffix in (".py", ".template"):
            if target_path.name.endswith(".xml.template"):
                all_issues.extend(check_xml_file(target_path))
            else:
                all_issues.extend(check_python_file(target_path))
        return all_issues

    for root, _, files in os.walk(target_path):
        # Ignore git, cache, and virtualenvs
        if any(ignored in root for ignored in [".git", "__pycache__", "venv", ".env", "node_modules"]):
            continue
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix == ".xml":
                all_issues.extend(check_xml_file(file_path))
            elif file_path.suffix in (".py", ".template"):
                if file.endswith(".xml.template"):
                    all_issues.extend(check_xml_file(file_path))
                else:
                    all_issues.extend(check_python_file(file_path))

    return all_issues


def main():
    parser = argparse.ArgumentParser(
        description="Verify Odoo 19.0 compatibility, detecting deprecated patterns and breaking changes."
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="*",
        default=["."],
        help="Directories or files to scan (defaults to current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit code 1 if warnings found)",
    )
    parser.add_argument(
        "--hide-info",
        action="store_true",
        help="Suppress INFO notices from output",
    )

    args = parser.parse_args()

    total_errors = 0
    total_warnings = 0
    total_info = 0
    scanned_count = 0

    print(f"\n{COLOR_BOLD}{COLOR_CYAN}=== Odoo 19.0 Compatibility Linter (3-Tier Severity) ==={COLOR_RESET}\n")

    for raw_path in args.paths:
        path = Path(raw_path).resolve()
        if not path.exists():
            print(f"{COLOR_RED}Error: Path '{raw_path}' does not exist.{COLOR_RESET}")
            continue

        issues = scan_target(path)
        scanned_count += 1

        for issue in issues:
            if issue.severity == "ERROR":
                total_errors += 1
                color = COLOR_RED
            elif issue.severity == "WARNING":
                total_warnings += 1
                color = COLOR_YELLOW
            else:
                total_info += 1
                color = COLOR_BLUE
                if args.hide_info:
                    continue

            print(f"{color}[{issue.severity}]{COLOR_RESET} {COLOR_BOLD}{issue.file_path}:{issue.line_no}{COLOR_RESET}")
            print(f"  {COLOR_BOLD}Code:{COLOR_RESET} {issue.code}")
            print(f"  {COLOR_BOLD}Issue:{COLOR_RESET} {issue.message}")
            if issue.snippet:
                print(f"  {COLOR_BOLD}Line:{COLOR_RESET}  {issue.snippet}")
            if issue.fix_hint:
                print(f"  {COLOR_GREEN}Fix:{COLOR_RESET}   {issue.fix_hint}")
            print()

    print(f"{COLOR_BOLD}--- Summary ---{COLOR_RESET}")
    print(f"Errors:   {COLOR_RED if total_errors else COLOR_GREEN}{total_errors}{COLOR_RESET}")
    print(f"Warnings: {COLOR_YELLOW if total_warnings else COLOR_GREEN}{total_warnings}{COLOR_RESET}")
    print(f"Notices:  {COLOR_BLUE if total_info else COLOR_GREEN}{total_info}{COLOR_RESET}")

    if total_errors > 0 or (args.strict and total_warnings > 0):
        print(f"\n{COLOR_RED}Audit FAILED: Please fix Odoo 19 compatibility issues listed above.{COLOR_RESET}\n")
        sys.exit(1)
    else:
        print(f"\n{COLOR_GREEN}Audit PASSED: All scanned files conform to Odoo 19 conventions!{COLOR_RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
