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

### Standard Module Developer Imports (ASCIIbetically ordered):
```python
# 1 : external libraries / stdlib (sorted)
import base64
import re

# 2 : odoo submodules (ASCIIbetically ordered)
from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import SQL, ormcache

# 3 : imports from other odoo addons (only when strictly necessary)
# from odoo.addons.portal.controllers.portal import CustomerPortal
```

---

## 2. Standard Module Directory Structure & Import Chain

Follow this standardized directory structure (strictly adhering to official Odoo guidelines):

```text
my_module/
├── __init__.py              # Root imports: controllers, models, report, wizard
├── __manifest__.py          # Module metadata, dependencies, and loading order
├── controllers/
│   ├── __init__.py
│   └── my_module.py         # HTTP & JSONRPC endpoints (name matches module; 'main.py' is outdated)
├── data/
│   ├── ir_cron_data.xml     # Scheduled actions (noupdate="1")
│   ├── ir_sequence_data.xml # Automated numbering sequences (noupdate="1")
│   ├── my_model_data.xml    # Initial master data (<model>_data.xml)
│   └── my_model_demo.xml    # Demo data (<model>_demo.xml; demo files belong in data/)
├── models/
│   ├── __init__.py          # One import per model file
│   ├── my_model.py          # Main model definition (<main_model>.py)
│   └── res_partner.py       # Inherited model in dedicated file (<inherited_model>.py)
├── report/
│   ├── __init__.py
│   ├── my_model_report.py   # SQL view statistics model (<model>_report.py)
│   ├── my_model_reports.xml # Report action & paperformat (<model>_reports.xml)
│   └── my_model_templates.xml# QWeb PDF report templates (<model>_templates.xml)
├── security/
│   ├── ir.model.access.csv  # Model-level ACL rules
│   ├── my_module_groups.xml # Custom user & manager security groups (<module>_groups.xml)
│   └── my_model_security.xml# Record rules with noupdate="1" (<model>_security.xml)
├── static/
│   ├── description/
│   │   └── icon.png         # Addon app icon (128x128 PNG)
│   ├── lib/                 # Third-party unminified JS/CSS libraries
│   └── src/
│       ├── js/              # OWL 2 components & services
│       ├── xml/             # OWL QWeb component templates
│       └── scss/            # Backend SCSS stylesheets
├── tests/
│   ├── __init__.py          # Must import all test suites
│   ├── test_my_model.py     # Backend TransactionCase / HttpCase
│   └── test_frontend.test.js# Modern Hoot unit tests
├── views/
│   ├── my_model_views.xml   # <list>, <form>, <search>, stat buttons, <chatter/> (<model>_views.xml)
│   └── my_module_menus.xml  # Main menus & category menus (<module>_menus.xml)
└── wizard/
    ├── __init__.py
    ├── custom_item_batch.py # TransientModel (<transient>.py; avoid 'wizard' word)
    └── custom_item_batch_views.xml # Modal form view (<transient>_views.xml)
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
from . import res_partner
```

---

---

## 3. Official 10-Section Model Attribute Ordering

According to official Odoo guidelines, attributes and methods within a model class MUST follow this strict 10-section sequence:

1. **Private attributes**: `_name`, `_description`, `_inherit`, `_inherits`, `_order`, `_rec_name`, `_check_company_auto`.
2. **Default methods and `default_get`**: Methods returning defaults (e.g. `_default_<field>`).
3. **Field declarations**: Grouped by purpose; Many2one suffixed by `_id`, Many2many/One2many suffixed by `_ids`.
4. **SQL constraints and indexes**: Modern SQL Table Objects (`models.Constraint`, `models.Index`, `models.UniqueIndex` with leading `_`).
5. **Compute, inverse, and search methods**: In the **exact same order** as the field declarations above.
6. **Selection methods**: Dynamic methods returning choices for selection fields (`_selection_<field>`).
7. **Constrains and onchange methods**: Validation methods (`@api.constrains`) and interactive form helpers (`@api.onchange`).
8. **CRUD overrides**: ORM lifecycle overrides (`create`, `write`, `unlink`, `_search`, `name_search`).
9. **Action methods**: Business actions triggered by buttons (`action_*`), requiring `self.ensure_one()` for single-record operations.
10. **Business methods & private helpers**: Core domain calculations and internal methods (`@api.private`).

```python
class EstateProperty(models.Model):
    # 1. Private attributes
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id desc'
    _rec_name = 'name'
    _check_company_auto = True

    # 2. Default methods
    def _default_date_deadline(self):
        return fields.Date.context_today(self)

    # 3. Field declarations
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    expected_price = fields.Float(string='Expected Price')
    selling_price = fields.Float(
        string='Selling Price',
        compute='_compute_selling_price',
        store=True,
    )
    property_type = fields.Selection(
        selection='_selection_property_type',
        string='Type',
    )
    date_deadline = fields.Date(string='Deadline', default=_default_date_deadline)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # 4. SQL table objects
    _positive_price = models.Constraint("CHECK(expected_price >= 0)", "Price must be positive.")

    # 5. Compute and inverse methods (in same order as fields)
    @api.depends('expected_price')
    def _compute_selling_price(self):
        for record in self:
            record.selling_price = record.expected_price * 0.95

    # 6. Selection methods
    @api.model
    def _selection_property_type(self):
        return [('residential', 'Residential'), ('commercial', 'Commercial')]

    # 7. Constrains and onchanges
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if record.selling_price > record.expected_price:
                raise ValidationError(_("Selling price cannot exceed expected price."))

    # 8. CRUD overrides
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    # 9. Action methods (prefixed action_*, ensure_one for single-record actions)
    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})

    # 10. Business methods
    def get_market_analysis(self):
        self.ensure_one()
        return self._fetch_area_statistics()
```

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

---

## 7. Exception Handling & Savepoints

Catch only specific exceptions and avoid overly broad exception handling. Limit the scope of `try-except` blocks.

```python
from odoo.exceptions import (
    UserError,         # Business logic errors displayed as warning modal to user
    ValidationError,   # Constraint violations
    AccessError,       # Access rights violations
    AccessDenied,      # Authentication failures (traceback suppressed)
    MissingError,      # Record not found / deleted
    RedirectWarning,   # Warning dialog offering an action button
)

# Recoverable operations with savepoint
try:
    with self.env.cr.savepoint():
        record.process_external_sync()
except UserError as err:
    _logger.warning("Recoverable sync error: %s", err)
```

> [!WARNING]
> **PostgreSQL Savepoints Performance Limit**:
> - Starting **more than 64 savepoints during a single database transaction** causes PostgreSQL query planning and snapshot management to slow down significantly.
> - If running on read-replicas, savepoints impose severe synchronization overhead.
> - When processing records in loops, do not place a savepoint around every iteration. Batch records or convert large sync operations into chunked scheduled actions.

---

## 8. Environment & Context Discipline

The context is an immutable `frozendict`. Modify it exclusively using `with_context()`:

```python
# Good: Replace or extend context
records_in_ctx = records.with_context(active_test=False)
records_with_extra = records.with_context(**extra_values)

# Modern Odoo 19 Company Switching:
record_in_company = records.with_company(target_company)
# ⚠️ NEVER set 'force_company' in context in Odoo 19 (raises DeprecationWarning).
```

> [!WARNING]
> **Context Side Effects & 'default_*' Propagation**:
> - Values placed in `context` propagate down the entire ORM call stack.
> - For example, calling `create()` with `default_my_field` in context sets the default for the main model, but if child records (such as `sale.order.line` during `sale.order` creation) happen to have a field with the same name, their default value will also be overridden unintentionally!
> - When adding custom context parameters, **always prefix keys with the module name** (e.g. `mail_create_nosubscribe`, `estate_skip_notification`).

---

## 9. Translation Function `_()` Discipline

Odoo uses `_()` (available via `from odoo import _` or `self.env._`) to mark translatable static strings at runtime.

### Strict Translation Rules:
1. **Static Literals Only**: Calls must be in the form `_('literal string')`. Dynamic string concatenation (`_(prefix + str)`) is strictly forbidden.
2. **No Formatting Inside or Outside**:
   - ❌ **FORBIDDEN**: `_('Record %s cannot be modified!' % record.name)` (breaks translation catalog extraction).
   - ❌ **FORBIDDEN**: `_('Record %s cannot be modified!') % record.name` (fails translation fallback).
   - ✅ **REQUIRED**: `_('Record %s cannot be modified!', record.name)`
3. **Prefer Named Placeholders for Multiple Variables**:
   - Single variable: `%s` positional parameter is acceptable.
   - Multiple variables: Prefer `%(varname)s` with keyword arguments to allow translators to reorder words:
     ```python
     _("Item %(title)s owned by %(partner)s has expired.", title=item.name, partner=item.partner_id.name)
     ```
4. **Never Wrap Field Values**:
   - Translatable model fields (`translate=True`) are translated automatically by the framework based on the user/partner language. Wrapping field values like `_(product.name)` is redundant and invalid.

---

## 10. Extendable Architecture (Think Extendable)

Avoid writing monolithic methods containing hardcoded business logic. Structure code so downstream submodules can extend functionality with minimal overrides:

- **Single Responsibility**: Split large methods as soon as they handle more than one task.
- **Hook Methods**: Extract search domains, default dictionaries, and value preparation into dedicated helper methods:
  ```python
  # Clean, extendable pattern
  def action_send(self):
      self.ensure_one()
      partners = self.env['res.partner'].search(self._get_recipient_domain())
      vals = self._prepare_message_vals(partners)
      self._dispatch_message(vals)

  def _get_recipient_domain(self):
      """Override in submodules to customize recipient selection."""
      return [('category_id', '=', self.category_id.id)]

  def _prepare_message_vals(self, partners):
      """Override in submodules to add extra payload fields."""
      return {'partner_ids': [Command.set(partners.ids)], 'body': self.notes}
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
