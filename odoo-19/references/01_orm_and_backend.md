# Odoo 19.0: ORM & Backend Reference

This guide covers modern backend development in Odoo 19.0, including model declarations, SQL table objects, field types, decorators, safe SQL execution, dynamic domains, and recordset operations.

---

## 1. Mandatory 5-Step Native-First Gate

Before implementing custom models, methods, or business logic—especially in complex ERP domains like real estate (properties, tenancies, reservations, payments, and revenue distributions)—you MUST execute this 5-step gate in order:

1. **Identify Relevant Native Models & Mixins**:
   - Check native chatter and activities (`mail.thread`, `mail.activity.mixin`).
   - Check financial and transactional base models (`account.move`, `account.move.line`, `res.partner`, `product.template`).
   - Check analytics and tracking (`analytic.mixin`, `utm.mixin`).
2. **Inspect Implementation & Call Sites in Source**:
   - Search the available Odoo 19 source tree in your environment to examine how core modules implement similar requirements. If source code is not locally accessible, consult the bundled reference guides and official documentation, and state in your plan that source inspection was unavailable.
3. **Reuse Native Functionality When It Satisfies the Requirement**:
   - Integrate with native accounting, partner management, and company switching rather than inventing redundant custom data structures.
4. **Introduce Custom Behavior Only When a Genuine Gap Exists**:
   - Inherit cleanly using `_inherit = '...'` and override via `super()`, or create dedicated custom models that link cleanly to native models without duplicating core logic.
5. **Test & Verify Against the Target Version**:
   - Ensure overrides preserve signature compatibility and respect native lifecycle hooks.

---

## 2. ORM Architecture & Package Restructure

Odoo 19 reorganized the monolithic `models.py` and `fields.py` into a modular package under `odoo/orm/`:
- `odoo/orm/models.py`: `BaseModel`, `Model`, `AbstractModel`
- `odoo/orm/models_transient.py`: `TransientModel`
- `odoo/orm/table_objects.py`: `Constraint`, `Index`, `UniqueIndex`
- `odoo/orm/fields.py`, `fields_relational.py`, `fields_numeric.py`, etc.
- `odoo/orm/commands.py`: `Command` enum
- `odoo/orm/domains.py`: `Domain` class
- `odoo/orm/decorators.py`: `@api.*` decorators
- `odoo/orm/environments.py`: `Environment`

### Standard Module Developer Imports:
```python
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError, AccessError, MissingError
from odoo.fields import Domain
from odoo.tools import SQL, ormcache
```

---

## 2. Standard Module Directory Structure & Import Chain

Follow this standardized directory structure (modeled on Odoo core apps like `sale`, `crm`, `project`):

```text
my_module/
├── __init__.py              # Root imports: controllers, models, report, wizard
├── __manifest__.py          # Module metadata, dependencies, and loading order
├── controllers/
│   ├── __init__.py
│   └── main.py              # HTTP & JSONRPC (@http.route) endpoints
├── data/
│   ├── ir_cron.xml          # Scheduled actions (noupdate="1")
│   ├── ir_sequence_data.xml # Automated numbering sequences (noupdate="1")
│   └── mail_template_data.xml
├── models/
│   ├── __init__.py          # One import per model file
│   └── my_model.py          # Model with SQL table objects, fields, and logic
├── report/
│   ├── __init__.py
│   ├── ir_actions_report.xml# Report action definition
│   └── report_templates.xml # QWeb PDF report using t-out
├── security/
│   ├── res_groups.xml       # User & Manager security groups
│   ├── ir.model.access.csv  # Model-level ACL rules
│   └── ir_rules.xml         # Multi-company and personal record rules (noupdate="1")
├── static/
│   ├── description/
│   │   └── icon.png         # Addon app icon (128x128 PNG)
│   └── src/
│       ├── js/              # OWL 2 components & services
│       ├── xml/             # OWL QWeb component templates
│       └── scss/            # Backend SCSS stylesheets
├── tests/
│   ├── __init__.py          # Must import all test suites
│   ├── test_my_model.py     # Backend TransactionCase / HttpCase
│   └── test_frontend.test.js# Modern Hoot unit tests
├── views/
│   ├── my_model_views.xml   # <list>, <form>, <search>, stat buttons, <chatter/>
│   └── menu.xml             # Main root & category menus (loaded LAST in data)
└── wizard/
    ├── __init__.py
    ├── my_wizard.py         # TransientModel wizard logic
    └── my_wizard_views.xml  # Modal form view with <footer> actions
```

### `__init__.py` Import Chain
```python
# Root my_module/__init__.py
from . import controllers
from . import models
from . import report
from . import wizard

# my_module/models/__init__.py (one import per model file)
from . import my_model
from . import my_other_model
```

---

## 2. Model Declaration & Attributes

Odoo 19 models inherit from `odoo.models`:

```python
class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'     # REQUIRED on every model
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'
    _rec_name = 'name'
    _check_company_auto = True
```

### Core Model Types
- `models.Model`: Persistent database table.
- `models.TransientModel`: Temporary records (e.g. wizards, dialogs), periodically cleared by vacuum.
- `models.AbstractModel`: Abstract base class with no database table (e.g. mixins like `mail.thread`).

### Key Model Attributes
- `_name`: Technical identifier (e.g. `'sale.order'`).
- `_description`: Human-readable label (required to avoid warnings).
- `_inherit`: Model inheritance (`'res.partner'` to extend, or list of mixins).
- `_inherits`: Delegation inheritance (e.g. `{'res.partner': 'partner_id'}`).
- `_order`: Default ordering clause (e.g. `'sequence, date desc, id desc'`).
- `_rec_name`: Field to use for record display name (defaults to `'name'`).
- `_check_company_auto = True`: Enforces multi-company consistency checks across relational fields.

---

## 3. SQL Table Objects (New in Odoo 19)

Instead of the legacy `_sql_constraints = [...]` tuple list, declare SQL constraints, indexes, and unique indexes directly as model attributes.

> [!IMPORTANT]
> **Naming Rule**: Attribute names for SQL table objects **MUST begin with an underscore `_`** to prevent collisions with field names.

```python
class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    name = fields.Char(required=True)
    price = fields.Float()
    code = fields.Char()
    partner_id = fields.Many2one('res.partner')
    date_order = fields.Date()

    # 1. SQL CHECK Constraint
    _positive_price = models.Constraint(
        "CHECK(price >= 0)",
        "The property price must be positive or zero.",
    )

    # 2. Composite Database Index
    _partner_date_idx = models.Index("(partner_id, date_order desc)")

    # 3. Unique Index with Partial WHERE clause & Custom Error Message
    _unique_code = models.UniqueIndex(
        "(code) WHERE code IS NOT NULL",
        "Property reference code must be unique.",
    )
```

---

## 4. Field Types & Options

Import fields from `odoo.fields`:

```python
# Basic types
name = fields.Char(string="Property Name", required=True, translate=True, index=True)
description = fields.Text(string="Description")
body_html = fields.Html(string="HTML Content", sanitize=True)
sequence = fields.Integer(string="Sequence", default=10)
price = fields.Float(string="Price", digits=(16, 2))
company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
total_amount = fields.Monetary(string="Total Amount", currency_field='currency_id')
active = fields.Boolean(string="Active", default=True)
date_deadline = fields.Date(string="Deadline", default=fields.Date.context_today)
create_date = fields.Datetime(string="Created On", readonly=True)
document = fields.Binary(string="Attachment")

# Selection
state = fields.Selection(
    selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ],
    string="Status",
    default='draft',
    required=True,
    copy=False,
    tracking=True,
    index=True,
)

# Relational Fields
partner_id = fields.Many2one('res.partner', string="Customer", ondelete='restrict', check_company=True)
line_ids = fields.One2many('estate.property.line', 'property_id', string="Lines", copy=True)
tag_ids = fields.Many2many('estate.tag', 'property_tag_rel', 'property_id', 'tag_id', string="Tags")

# Modern Structured Types
extra_data = fields.Json(string="Structured Attributes")
properties = fields.Properties(string="Dynamic Properties", definition='property_type_id.property_definitions')
```

### Essential Field Attributes:
- `tracking=True`: Chatter audit log (requires `mail.thread` mixin).
- `check_company=True`: Company consistency validation (requires `_check_company_auto = True`).
- `aggregator="sum"`: Aggregate function in pivot/graph/list views (`'sum'`, `'avg'`, `'min'`, `'max'`, `'bool_and'`, `'bool_or'`, `'count'`). Note: `group_operator` is deprecated since Odoo 18.0.
- `copy=False`: Exclude from duplicate record actions.
- `index=True` or `index='btree_not_null'` or `index='trigram'`.
- `precompute=True`: Compute before INSERT (with `store=True`), avoiding post-creation UPDATEs. Ideal on child lines of `One2many` created in batch (e.g. lease schedule lines, invoice lines). Avoid as a default on standalone parent models where records are created one-by-one, as it bypasses ORM prefetching and incurs single-record compute overhead.
- `compute_sudo=True`: Compute bypassing field access rights.
- `store=True, readonly=False`: Editable computed field pattern.
- `ondelete='restrict'|'cascade'|'set null'`: Foreign key deletion behavior.

---

## 5. Computed Fields & Onchange

### Computed Fields
Use `@api.depends` for dependencies:

```python
area = fields.Float(string="Area (sqm)")
price_per_sqm = fields.Float(
    string="Price / sqm",
    compute='_compute_price_per_sqm',
    store=True,
)

@api.depends('area', 'price')
def _compute_price_per_sqm(self):
    for record in self:
        if record.area:
            record.price_per_sqm = record.price / record.area
        else:
            record.price_per_sqm = 0.0
```

### Inverse & Search Methods
```python
buyer_id = fields.Many2one(
    'res.partner',
    string="Buyer",
    compute='_compute_buyer',
    inverse='_inverse_buyer',
    search='_search_buyer',
)
```

### Onchange
Use `@api.onchange` exclusively for client-side suggestions in interactive form views:
```python
@api.onchange('partner_id')
def _onchange_partner_id(self):
    if self.partner_id:
        self.price = self.partner_id.default_rate
```

---

## 6. Method Decorators

- `@api.depends(*field_paths)`: Recomputes field when specified paths change (dotted paths supported).
- `@api.depends_context(*keys)`: Recomputes field based on context keys (`'company'`, `'uid'`, `'bin_size'`).
- `@api.constrains(*field_names)`: Python validation during create/write. Simple field names only (no dotted paths).
- `@api.model`: Method operating without an active recordset. Auto-wraps `create()` with `model_create_multi`.
- `@api.model_create_multi`: Required for `create()` overrides to process `vals_list` batch creations efficiently.
- `@api.private`: Marks method as internal, preventing external RPC/JSON-2 invocation.
- `@api.readonly`: Indicates method can use a readonly cursor during RPC calls (routes queries to read-replicas).
- `@api.autovacuum`: Marks method to be called daily by the scheduled autovacuum cron job (must start with `_`).
- `@api.ondelete(at_uninstall=False)`: Validates conditions before unlinking records.
- `@tools.ormcache(...)`: In-memory LRU caching on models. In Odoo 19, `@ormcache_context` is deprecated in favor of `@ormcache` (context keys are accessible directly via `self.env.context.get(...)`). The `skiparg` parameter is also deprecated.

---

## 7. Exception Handling

Always import standard exceptions from `odoo.exceptions`:

```python
from odoo.exceptions import (
    UserError,         # Business logic errors displayed as warning modal to user
    ValidationError,   # Constraint violations
    AccessError,       # Access rights violations
    AccessDenied,      # Authentication failures (traceback suppressed)
    MissingError,      # Record not found / deleted
    RedirectWarning,   # Warning dialog offering an action button
    CacheMiss,         # Internal cache miss
)
```

---

## 8. Environment & Recordset Context

In Odoo 19, record attributes `_cr`, `_uid`, and `_context` are deprecated. Always access them through `self.env`:

```python
# Database cursor
cursor = self.env.cr

# User ID and record
user_id = self.env.uid
current_user = self.env.user

# Context
context_dict = self.env.context
lang = self.env.context.get('lang')

# Companies
current_company = self.env.company
allowed_companies = self.env.companies

# Environment switching
record_in_context = self.with_context(active_test=False, default_state='draft')
record_as_super = self.sudo()
record_in_company = self.with_company(other_company)

# ⚠️ Breaking Change in Odoo 19:
# Do NOT set 'force_company' in context: context key 'force_company' is no longer supported and raises DeprecationWarning.
# Always use self.with_company(company) instead.
# Setting 'company' in context is also discouraged due to conflict with @depends_context('company').
```

---

## 9. Relational Writes with `Command`

Avoid outdated integer triplets like `(0, 0, {...})` or `(6, 0, ids)`. Use `odoo.Command`:

```python
from odoo import Command

self.env['estate.property'].create({
    'name': 'Luxury Villa',
    'tag_ids': [Command.set(tag_ids)],                 # Replace tags with existing IDs
    'line_ids': [
        Command.create({'name': 'Roof Repair', 'amount': 1200.0}), # Create new child
        Command.create({'name': 'Painting', 'amount': 500.0}),
    ]
})

# Updating relational lines
property_rec.write({
    'line_ids': [
        Command.update(line_1.id, {'amount': 1300.0}),  # Update existing child
        Command.delete(line_2.id),                      # Delete child record from DB
        Command.unlink(tag_1.id),                      # Unlink Many2many (keep record)
        Command.link(tag_2.id),                        # Link existing Many2many
        Command.clear(),                               # Remove all relations
    ]
})
```

---

## 10. Domains & Dynamic Dates (Odoo 19)

Odoo 19 supports dynamic dates directly in domains and provides the `odoo.fields.Domain` builder:

### Dynamic Date Syntax
```python
from odoo.fields import Domain

# Current timestamp & today
d1 = Domain('date_deadline', '<', 'now')
d2 = Domain('date_deadline', '>=', 'today')

# Relative date arithmetic
d3 = Domain('date_deadline', '<', '-3d +1H')       # 3 days ago + 1 hour
d4 = Domain('date_deadline', '>=', '=monday -1w')   # Monday of previous week

# Specific components
d5 = Domain('create_date', '<', '=3H')             # Today at 03:00:00
d6 = Domain('date_deadline', '<', '=5d')           # 5th day of current month
d7 = Domain('birthday.month_number', '=', 2)        # Date component extraction
```

### Combining Domains & Operators
```python
# Bitwise combinations (Domain objects are immutable)
domain = Domain('state', '=', 'confirmed') & (
    Domain('amount', '>', 1000) | Domain('priority', '=', 'high')
)
negated_domain = ~Domain('active', '=', False)

# Static AND / OR helper
combined = Domain.AND([d1, d2, d3])
disjoined = Domain.OR([d1, d2])

# Relational 'any' operator
domain_with_any = Domain('line_ids', 'any', Domain('amount', '>', 500))

# Custom SQL leaf in domain (Odoo 19)
custom_domain = Domain.custom(
    to_sql=lambda model, alias, query: SQL("%s.amount > 0", SQL.identifier(alias))
)

# Search with Domain
records = self.env['estate.property'].search(domain)
```

> [!IMPORTANT]
> **Domain Operator Rules in Odoo 19**:
> 1. Domain operators **MUST be lowercase** (`'in'`, `'not in'`, `'like'`, `'ilike'`). Uppercase operators trigger `DeprecationWarning`.
> 2. Operators `'<>'` and `'=='` are deprecated in favor of `'!='` and `'='`.
> 3. Legacy `odoo.osv.expression` is deprecated; always use `odoo.fields.Domain`.

---

## 11. Safe SQL Execution with `odoo.tools.SQL`

> [!IMPORTANT]
> **ORM Preference & SQL Safety Standard**:
> Always **prefer the ORM for ordinary business operations**. Only use raw SQL when complex reporting aggregations or massive batch data migrations require it. When raw SQL is strictly necessary, require safe, parameterized SQL through Odoo's supported SQL utilities (`odoo.tools.SQL`). Never use raw Python string formatting (`%s` or `.format()`) directly in `cr.execute`. Remember that raw SQL bypasses multi-company record rules, field-level access checks, and ORM cache invalidation.

```python
from odoo.tools import SQL

def get_high_value_property_ids(self, min_price):
    query = SQL(
        """
        SELECT id, name, price
        FROM estate_property
        WHERE company_id = %s
          AND price >= %s
          AND active = TRUE
        ORDER BY price DESC
        """,
        self.env.company.id,
        min_price,
    )
    self.env.cr.execute(query)
    return self.env.cr.dictfetchall()
```

Composing SQL dynamically with identifiers and joins:
```python
# Safe table and column identifier escaping
table_sql = SQL.identifier(self._table)

clauses = [SQL("active = TRUE")]
if only_sold:
    clauses.append(SQL("state = %s", 'done'))

where_sql = SQL(" AND ").join(clauses)
query = SQL("SELECT id, name FROM %s WHERE %s", table_sql, where_sql)
self.env.cr.execute(query)

# Note: Deconstructing SQL objects as `code, params = sql` is deprecated in 19.0.
# Use sql.code and sql.params directly or pass SQL to cr.execute.
```
