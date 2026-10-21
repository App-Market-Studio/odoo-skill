# AGENTS.md — Odoo 19 Skill Repository

## Repository Purpose
This repository provides an open-standard, modular **Odoo 19.0 AI Coding Agent Skill** (`.agents/skills/odoo-19/`). It equips AI coding assistants (Antigravity, OpenCode, Claude Code, Cursor, Windsurf, Cline, GitHub Copilot, Aider, and more) with senior architectural guardrails, reference guides, boilerplate templates, and automated compatibility linters for custom Odoo 19 development.

---

## Directory Architecture

All paths in this repository are relative, modular, and portable across any OS or container:

```text
<project_root>/
├── .agents/
│   └── skills/
│       └── odoo-19/                       # The Skill package
│           ├── SKILL.md                   # Main agent entrypoint with YAML frontmatter
│           ├── scripts/
│           │   ├── verify_odoo19_compat.py # Standalone CLI linter detecting Odoo 19 antipatterns
│           │   ├── verify_packaging.py    # Packaging & drop-in installation validator
│           │   └── test_linter.py         # Regression unit test suite (standard library unittest)
│           ├── templates/                 # Reference scaffolds & starter templates (.template)
│           │   ├── __manifest__.py.template
│           │   ├── model.py.template
│           │   ├── views.xml.template
│           │   ├── wizard.py.template
│           │   ├── wizard_views.xml.template
│           │   ├── security_groups.xml.template
│           │   ├── ir.model.access.csv.template
│           │   ├── ir_rules.xml.template
│           │   ├── ir_sequence_data.xml.template
│           │   ├── ir_cron_data.xml.template
│           │   ├── ir_actions_report.xml.template
│           │   ├── report_templates.xml.template
│           │   ├── controller.py.template
│           │   ├── owl_component.js.template
│           │   ├── component.scss.template
│           │   ├── test_model.py.template
│           │   └── hoot_test.js.template
│           └── references/                # Deep-dive modular technical reference guides (.md)
│               ├── 01_orm_and_backend.md
│               ├── 02_views_and_ui.md
│               ├── 03_owl_and_frontend.md
│               ├── 04_security_and_access.md
│               ├── 05_external_api_json2.md
│               ├── 06_testing_and_cli.md
│               ├── 07_breaking_changes_19.md
│               ├── 08_wizards_reports_and_automation.md
│               └── 09_performance_and_debugging.md
├── AGENTS.md                              # Repository instructions for AI coding agents
├── LICENSE                                # MIT License
└── README.md                              # Human-facing setup & usage documentation
```

---

## Verification & Testing (Run Before Any Commit)

All test and audit tools use Python standard library only with zero external dependencies:

```bash
# 1. Run the linter unit test suite (regression testing)
python3 .agents/skills/odoo-19/scripts/test_linter.py

# 2. Audit all templates and references in strict mode
python3 .agents/skills/odoo-19/scripts/verify_odoo19_compat.py .agents/skills/odoo-19/templates .agents/skills/odoo-19/references --strict

# 3. Validate packaging layout, link integrity, and simulated drop-in installation
python3 .agents/skills/odoo-19/scripts/verify_packaging.py
```

---

## Architectural Guardrails for Agents Working in This Repo

When modifying or adding files to this skill package, strictly follow these rules:

1. **Portability & Zero Hardcoded Paths**:
   - Never write machine-specific paths (e.g. `/home/...`, `C:\...`, `/root/...`).
   - Use dynamic path discovery or relative project paths everywhere.

2. **Strict Odoo 19 Standard Compliance & Official Guidelines**:
   - Views: Use `<list>` instead of legacy `<tree>`. View mode must be `list,form`.
   - View XML IDs & Naming: `<model_name>_view_<type>`. `<field name="name">` MUST match XML ID with dots replacing underscores.
   - Inherited Views: Unique descriptive XML ID `<target_view_id>_inherit_<feature>`, with `.inherit.<details>` in the view name. (Reusing base ID is reserved for in-place data updates).
   - UI Expressions: Direct Python expressions (`invisible=`, `readonly=`, `required=`), never legacy `attrs="..."` or `states="..."`.
   - List Columns: Use `column_invisible=` when hiding an entire column; use `invisible=` for row-level cell hiding.
   - QWeb: Always use `t-out`, never `t-esc` or `t-raw`.
   - SQL Table Objects: Use `models.Constraint`, `models.Index`, and `models.UniqueIndex` (must start with a leading underscore `_`). Never use deprecated `_sql_constraints`.
   - Model Structure: Follow the recommended 10-section attribute ordering sequence. Single-record action methods must enforce `self.ensure_one()`; batch actions must preserve recordset iteration.
   - Transient Models: Name as `<related_base_model>.<action>` (e.g. `account.invoice.make`), strictly avoiding the word `wizard`.
   - Controllers: Single controller named `<module_name>.py` (deprecates `main.py`). HTTP routing for JSON-RPC must use `type='jsonrpc'`.
   - Translation `_()`: Literal strings only with `_('literal %s', arg)` or `_('literal %(k)s', k=v)`. Never format inside or outside `_()`.
   - SCSS/CSS: Outside-in properties order, scoped variables `$-var` and BEM contextual CSS variables `--var` at the top, `.o_<module_name>` class prefix.
   - Safe SQL & ORM: Prefer native ORM (`_read_group`, `search_count`). When raw SQL is justified, flush dirty cache (`flush_model()`), use `odoo.tools.SQL`, and manually enforce multi-company security.

3. **Non-Dogmatic Performance & Security Guidelines**:
   - Do not claim "zero ORM calls in loops" blindly; distinguish Odoo's prefetching cache from true N+1 queries.
   - Do not mandate record rules for models lacking `company_id` or user ownership concepts.

4. **Linter Severity Discipline**:
   - `ERROR`: Breaking changes that will crash Odoo 19 at boot or runtime.
   - `WARNING`: Deprecated patterns that still function but are discouraged.
   - `INFO`: Style recommendations, subtle context hints, or best-practice notices.

5. **Principle of Least Code (YAGNI) & Minimal Diffs**:
   - The best code is the code never written. Solve the entire task with the smallest correct change.
   - Do not add speculative wrappers, helpers, or unrequested abstractions.
   - Surgical, reviewable diffs beat broad rewrites.
   - End completions with a 1–2 line disclosure of what was skipped/deferred and any operational risks.
