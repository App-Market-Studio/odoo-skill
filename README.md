# Odoo 19.0 Coding Agent Skill

A specialized, comprehensive coding agent skill package designed for **Odoo 19.0** custom module development, debugging, refactoring, and code migration.

Built directly from the official Odoo 19.0 documentation and source architecture, combined with senior architectural guardrails (the **Native-First Mandate**, 9-step debugging sequence, SQL table objects, and self-review checklist), this skill equips Antigravity (and compatible agentic coding assistants) with accurate, up-to-date conventions for any environment.

---

## Directory Structure

```text
odoo-skill/
├── README.md                          # Setup & usage documentation
└── odoo-19/                           # The Skill package
    ├── SKILL.md                       # Main agent entrypoint with YAML frontmatter
    ├── scripts/
    │   ├── verify_odoo19_compat.py    # Python CLI linter detecting Odoo 19 antipatterns
    │   └── test_linter.py             # Regression test suite for linter
    ├── templates/                     # Production-ready Odoo 19 boilerplate files
    │   ├── __manifest__.py.template   # Manifest with strict data loading order
    │   ├── model.py.template          # Model with SQL table objects, precompute, and safe SQL
    │   ├── views.xml.template         # <list>, <form>, <search>, stat buttons, <chatter/>
    │   ├── wizard.py.template         # TransientModel wizard for batch actions
    │   ├── wizard_views.xml.template  # Wizard modal form with <footer> actions
    │   ├── security_groups.xml.template # Category, User, and Manager groups
    │   ├── ir.model.access.csv.template # Model-level ACL rules
    │   ├── ir_rules.xml.template      # Multi-company and personal record rules
    │   ├── ir_sequence_data.xml.template # Automated sequence definition
    │   ├── ir_cron_data.xml.template  # Scheduled background action
    │   ├── ir_actions_report.xml.template # QWeb PDF report action binding
    │   ├── report_templates.xml.template  # QWeb PDF report using t-out
    │   ├── controller.py.template     # Controllers with type='jsonrpc' & Bearer tokens
    │   ├── owl_component.js.template  # Modern OWL 2 component
    │   ├── test_model.py.template     # TransactionCase test suite
    │   └── hoot_test.js.template      # Frontend unit test using @odoo/hoot
    └── references/                    # Deep-dive modular technical reference guides
        ├── 01_orm_and_backend.md      # Models, fields, table objects, SQL wrapper, dynamic domains
        ├── 02_views_and_ui.md         # <list> views, forms, search, conditional expressions, chatter
        ├── 03_owl_and_frontend.md     # OWL 2 components, registries, services, native JS modules
        ├── 04_security_and_access.md  # ir.model.access.csv, ir.rule, groups, sudo() discipline
        ├── 05_external_api_json2.md   # External JSON-2 API (/json/2/...) & Bearer authentication
        ├── 06_testing_and_cli.md      # TransactionCase, HttpCase, test tags, Hoot testing, odoo-bin CLI
        ├── 07_breaking_changes_19.md  # Odoo 19 migration rules & common antipatterns
        ├── 08_wizards_reports_and_automation.md # Wizards, PDF Reports, Crons, Sequences
        └── 09_performance_and_debugging.md     # 9-step debugging sequence, error diagnosis, N+1 rules
```

---

## How to Install and Activate the Skill

First, clone the repository:

```bash
git clone https://github.com/App-Market-Studio/odoo-skill.git
```

Depending on your workflow, you can install this skill either **per-project** or **globally**.

### Option 1: Install in a Specific Project (Recommended)

Link or copy the `odoo-19` directory into your project's `.agents/skills/` folder:

```bash
# From your target Odoo project root:
mkdir -p .agents/skills

# Symlink (recommended so git pull keeps the skill updated):
ln -s /path/to/odoo-skill/odoo-19 .agents/skills/odoo-19

# Or copy if you prefer a standalone copy:
cp -r /path/to/odoo-skill/odoo-19 .agents/skills/
```

Antigravity will automatically discover `.agents/skills/odoo-19/SKILL.md` when working in that workspace.

### Option 2: Install Globally (Available across all workspaces)

Link or copy the `odoo-19` folder into your global configuration root:

```bash
mkdir -p ~/.gemini/config/skills

# Symlink:
ln -s /path/to/odoo-skill/odoo-19 ~/.gemini/config/skills/odoo-19

# Or copy:
cp -r /path/to/odoo-skill/odoo-19 ~/.gemini/config/skills/
```

---

## Using the Linter Tool

This package includes a standalone CLI script to audit Odoo addons for compliance with Odoo 19 standards:

```bash
# Run from within the repository root:
python3 odoo-19/scripts/verify_odoo19_compat.py /path/to/your/custom_addon
```

The tool scans XML and Python files for:
- Outdated `<tree>` view tags (must be `<list>`)
- Deprecated `attrs="..."` and `states="..."` (must be direct Python expressions `invisible=`, `readonly=`, `required=`)
- Deprecated `t-esc` and `t-raw` in QWeb templates (must be `t-out`)
- Deprecated `_sql_constraints` lists (must be `models.Constraint` or `models.UniqueIndex`)
- SQL table object attributes missing a leading underscore `_`
- Deprecated `record._cr`, `record._uid`, `record._context` (must be `record.env.cr`, etc.)
- Deprecated `request.cr`, `request.uid`, `request.context` (must be `request.env.cr`, etc.)
- Deprecated `odoo.osv` imports
- Deprecated route type `type='json'` in controllers (must be `type='jsonrpc'`)
- Deprecated module manifest hook signatures `(cr, registry)` (must be `(env)`)
- Legacy SQL string formatting instead of `odoo.tools.SQL`
- List column visibility using `invisible=` instead of `column_invisible=`
- Deprecated `group_operator=` on fields (must be `aggregator=`)
- Deprecated `'force_company'` in context (must be `.with_company(company)`)
- Deprecated `@ormcache_context` (must be `@ormcache`)
- Uppercase domain operators (`'LIKE'`, `'IN'`)
