# AGENTS.md — Odoo 19 Skill Repository

## Repository Purpose
This repository provides an open-standard, modular **Odoo 19.0 AI Coding Agent Skill** (`odoo-19/`). It equips AI coding assistants (Antigravity, OpenCode, Claude Code, Cursor, Windsurf, Cline, GitHub Copilot, Aider, and more) with senior architectural guardrails, reference guides, boilerplate templates, and automated compatibility linters for custom Odoo 19 development.

---

## Directory Architecture

All paths in this repository are relative, modular, and portable across any OS or container:

```text
odoo-skill/
├── AGENTS.md                          # Repository instructions for AI coding agents
├── LICENSE                            # MIT License
├── README.md                          # Human-facing setup & usage documentation
└── odoo-19/                           # The Skill package
    ├── SKILL.md                       # Main agent entrypoint with YAML frontmatter
    ├── scripts/
    │   ├── verify_odoo19_compat.py    # Standalone CLI linter detecting Odoo 19 antipatterns
    │   └── test_linter.py             # Regression unit test suite (standard library unittest)
    ├── templates/                     # Modular Odoo 19 boilerplate files (.template)
    │   ├── __manifest__.py.template
    │   ├── model.py.template
    │   ├── views.xml.template
    │   ├── wizard.py.template
    │   ├── wizard_views.xml.template
    │   ├── security_groups.xml.template
    │   ├── ir.model.access.csv.template
    │   ├── ir_rules.xml.template
    │   ├── ir_sequence_data.xml.template
    │   ├── ir_cron_data.xml.template
    │   ├── ir_actions_report.xml.template
    │   ├── report_templates.xml.template
    │   ├── controller.py.template
    │   ├── owl_component.js.template
    │   ├── test_model.py.template
    │   └── hoot_test.js.template
    └── references/                    # Deep-dive modular technical reference guides (.md)
        ├── 01_orm_and_backend.md
        ├── 02_views_and_ui.md
        ├── 03_owl_and_frontend.md
        ├── 04_security_and_access.md
        ├── 05_external_api_json2.md
        ├── 06_testing_and_cli.md
        ├── 07_breaking_changes_19.md
        ├── 08_wizards_reports_and_automation.md
        └── 09_performance_and_debugging.md
```

---

## Verification & Testing (Run Before Any Commit)

All test and audit tools use Python standard library only with zero external dependencies:

```bash
# 1. Run the linter unit test suite (regression testing)
python3 odoo-19/scripts/test_linter.py

# 2. Audit all templates and references in strict mode
python3 odoo-19/scripts/verify_odoo19_compat.py odoo-19/templates odoo-19/references --strict
```

---

## Architectural Guardrails for Agents Working in This Repo

When modifying or adding files to this skill package, strictly follow these rules:

1. **Portability & Zero Hardcoded Paths**:
   - Never write machine-specific paths (e.g. `/home/...`, `C:\...`, `/root/...`).
   - Use dynamic path discovery or relative project paths everywhere.

2. **Strict Odoo 19 Standard Compliance**:
   - Views: Use `<list>` instead of legacy `<tree>`. View mode must be `list,form`.
   - UI Expressions: Direct Python expressions (`invisible=`, `readonly=`, `required=`), never legacy `attrs="..."` or `states="..."`.
   - List Columns: Use `column_invisible=` when toggling an entire column.
   - QWeb: Always use `t-out`, never `t-esc` or `t-raw`.
   - SQL Table Objects: Use `models.Constraint`, `models.Index`, and `models.UniqueIndex` (must start with a leading underscore `_`). Never use deprecated `_sql_constraints`.
   - Controllers: HTTP routing for JSON-RPC must use `type='jsonrpc'`, never legacy `type='json'`.
   - Safe SQL: Always wrap raw SQL using `odoo.tools.SQL`.

3. **Non-Dogmatic Performance & Security Guidelines**:
   - Do not claim "zero ORM calls in loops" blindly; distinguish Odoo's prefetching cache from true N+1 queries.
   - Do not mandate record rules for models lacking `company_id` or user ownership concepts.

4. **Linter Severity Discipline**:
   - `ERROR`: Breaking changes that will crash Odoo 19 at boot or runtime.
   - `WARNING`: Deprecated patterns that still function but are discouraged.
   - `INFO`: Style recommendations, subtle context hints, or best-practice notices.
