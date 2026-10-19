# Odoo 19.0 Coding Agent Skill

A specialized, comprehensive coding agent skill package designed for **Odoo 19.0** custom module development, debugging, refactoring, and code migration.

Built directly from the official Odoo 19.0 documentation and source architecture, combined with senior architectural guardrails (the **Native-First Mandate**, 9-step debugging sequence, SQL table objects, and self-review checklist), this skill equips AI coding agents (Antigravity, OpenCode, Claude Code, Cursor, Windsurf, Cline, GitHub Copilot, Aider, and more) with accurate, production-grade Odoo 19 conventions for any development environment.

---

## Directory Structure

```text
odoo-skill/
├── AGENTS.md                          # Repository instructions for AI coding agents
├── LICENSE                            # MIT License
├── README.md                          # Human-facing setup & multi-agent usage documentation
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

## Installation & Agent Setup

First, clone this repository to your local machine:

```bash
git clone https://github.com/App-Market-Studio/odoo-skill.git
```

This skill is packaged using the open **Agent Skill Standard** (`SKILL.md` with YAML frontmatter, modular references, templates, and standalone audit scripts). You can activate it with any major AI coding assistant:

### 1. Antigravity & Gemini CLI
Antigravity automatically discovers skills in the workspace or global directory:

- **Per-project (Recommended):**
  ```bash
  mkdir -p .agents/skills
  ln -s /path/to/odoo-skill/odoo-19 .agents/skills/odoo-19
  # or: cp -r /path/to/odoo-skill/odoo-19 .agents/skills/
  ```
- **Globally (across all projects):**
  ```bash
  mkdir -p ~/.gemini/config/skills
  ln -s /path/to/odoo-skill/odoo-19 ~/.gemini/config/skills/odoo-19
  # or: cp -r /path/to/odoo-skill/odoo-19 ~/.gemini/config/skills/
  ```

### 2. OpenCode
OpenCode natively supports both **Agent Skills** (on-demand loading) and **`AGENTS.md`** (standing project instructions):

- **As an Agent Skill (Recommended):**
  ```bash
  # Per-project:
  mkdir -p .opencode/skills
  ln -s /path/to/odoo-skill/odoo-19 .opencode/skills/odoo-19
  # (Note: OpenCode also automatically discovers `.agents/skills/odoo-19`)

  # Globally (across all projects):
  mkdir -p ~/.config/opencode/skills
  ln -s /path/to/odoo-skill/odoo-19 ~/.config/opencode/skills/odoo-19
  ```

- **Via `AGENTS.md` (Always in context):**
  ```bash
  # Option A: Link SKILL.md as your project's AGENTS.md
  ln -s /path/to/odoo-skill/odoo-19/SKILL.md AGENTS.md

  # Option B: If you already have an AGENTS.md, append a reference:
  echo -e "\n## Odoo 19 Rules\nFollow Odoo 19 architectural guidelines in [.opencode/skills/odoo-19/SKILL.md](.opencode/skills/odoo-19/SKILL.md)." >> AGENTS.md
  ```

### 3. Claude Code (Anthropic)
Claude Code loads instructions from `CLAUDE.md` in the project root:

```bash
# Option A: Link SKILL.md as your project's CLAUDE.md
ln -s /path/to/odoo-skill/odoo-19/SKILL.md CLAUDE.md

# Option B: If you already have a CLAUDE.md, append a reference:
echo -e "\n## Odoo 19 Architecture & Rules\nRefer to [.agents/skills/odoo-19/SKILL.md](.agents/skills/odoo-19/SKILL.md) for strict Odoo 19 conventions." >> CLAUDE.md
```

### 4. Cursor
Cursor reads instructions from `.cursorrules` or `.cursor/rules/*.mdc`:

- **Option A (.cursorrules):**
  ```bash
  ln -s /path/to/odoo-skill/odoo-19/SKILL.md .cursorrules
  ```
- **Option B (MDC Rules):**
  ```bash
  mkdir -p .cursor/rules
  ln -s /path/to/odoo-skill/odoo-19/SKILL.md .cursor/rules/odoo-19.mdc
  ```

### 5. Windsurf (Codeium)
Windsurf Cascade loads workspace rules from `.windsurfrules`:

```bash
ln -s /path/to/odoo-skill/odoo-19/SKILL.md .windsurfrules
```

### 6. Cline / Roo Code (VS Code Extension)
Cline and Roo Code load system prompt instructions from `.clinerules`:

```bash
ln -s /path/to/odoo-skill/odoo-19/SKILL.md .clinerules
```

### 7. GitHub Copilot
GitHub Copilot reads repository-level custom instructions from `.github/copilot-instructions.md`:

```bash
mkdir -p .github
ln -s /path/to/odoo-skill/odoo-19/SKILL.md .github/copilot-instructions.md
```

### 8. Aider
Aider can load the skill via configuration file or command line:

- **Via `.aider.conf.yml`:**
  ```yaml
  read:
    - /path/to/odoo-skill/odoo-19/SKILL.md
  ```
- **Via CLI flag:**
  ```bash
  aider --read /path/to/odoo-skill/odoo-19/SKILL.md
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

---

## License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute these templates and skills in both open-source and proprietary Odoo modules.

