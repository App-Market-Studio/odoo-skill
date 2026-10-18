# Odoo 19.0: Breaking Changes & Migration Checklist

This document catalogs critical breaking changes, deprecations, and architectural evolutions in Odoo 19.0 (including relevant forward-ports from Odoo 18.x). Use this checklist whenever reviewing or porting modules.

---

## 1. Quick Migration Audit Table

| Area | Deprecated / Removed Syntax | Modern Odoo 19 Replacement | Severity |
| :--- | :--- | :--- | :--- |
| **Views** | `<tree string="...">` | `<list string="...">` | **BREAKING** |
| **Actions** | `view_mode="tree,form"` | `view_mode="list,form"` | **WARNING** |
| **View Modifiers** | `attrs="{'invisible': ...}"` | `invisible="expression"` | **BREAKING** |
| **View Modifiers** | `states="draft,open"` | `invisible="state not in ('draft', 'open')"` | **BREAKING** |
| **List Columns** | `invisible="1"` on list column | `column_invisible="expression"` | **BREAKING** |
| **Chatter** | `<div class="oe_chatter">` | `<chatter/>` tag | **WARNING** |
| **QWeb Directives** | `t-esc="..."`, `t-raw="..."` | `t-out="..."` | **DEPRECATED** |
| **SQL Constraints** | `_sql_constraints = [...]` | `models.Constraint`, `models.UniqueIndex` (must start with `_`) | **DEPRECATED** |
| **ORM Cursors** | `self._cr`, `record._cr` | `self.env.cr` | **DEPRECATED** |
| **ORM UIDs** | `self._uid`, `record._uid` | `self.env.uid` | **DEPRECATED** |
| **ORM Contexts** | `self._context`, `record._context` | `self.env.context` | **DEPRECATED** |
| **Legacy OSV** | `from odoo.osv import osv` | `from odoo import models` | **DEPRECATED** |
| **Controllers** | `@http.route(type='json')` | `@http.route(type='jsonrpc')` | **DEPRECATED** |
| **External API** | `/xmlrpc`, `/xmlrpc/2`, `/jsonrpc` | `POST /json/2/<model>/<method>` (JSON-2 API) | **DEPRECATED** |
| **Hooks** | `post_init_hook(cr, registry)` | `post_init_hook(env)` | **BREAKING** |
| **SQL Queries** | `cr.execute("... %s" % val)` | `cr.execute(SQL("... WHERE id = %s", val))` | **SECURITY** |
| **Grouping** | `read_group(...)` in backend | `_read_group(...)` | **DEPRECATED** |
| **Record Names** | `def name_get(self):` | Compute `display_name` field | **DEPRECATED** |
| **Field Aggregation**| `group_operator="sum"` | `aggregator="sum"` | **DEPRECATED** |
| **Company Context** | `context={'force_company': id}` | `record.with_company(company)` | **BREAKING** |
| **ORM Caching** | `@ormcache_context(keys=...)` | `@ormcache` directly | **DEPRECATED** |
| **Request Env** | `request.cr`, `request.uid`, `request.context` | `request.env.cr`, `request.env.uid`, `request.env.context` | **DEPRECATED** |
| **Domain Operators**| `'LIKE'`, `'IN'`, `'<>'`, `'=='` | Lowercase `'like'`, `'in'`, `'!='`, `'='` | **WARNING** |
| **Frontend Tests** | QUnit test suites | **Hoot** (`@odoo/hoot` in `web.assets_unit_tests`) | **BREAKING** |

---

## 2. In-Depth Breaking Changes & Remediation

### 1. View Root `<tree>` -> `<list>`
- In Odoo 18 and 19, the root tag for tabular data views is `<list>`, not `<tree>`.
- In window actions, update `view_mode` from `tree,form` to `list,form`.

### 2. View Dynamic Modifiers (`attrs` & `states` Removal)
- Modifiers must now be raw Python expressions evaluated against the active form/record.
- **Old**: `<field name="partner_id" attrs="{'invisible': [('state', '=', 'cancel')]}"/>`
- **New**: `<field name="partner_id" invisible="state == 'cancel'"/>`

### 3. Column Visibility in Lists (`column_invisible`)
- In `<list>` views, use `column_invisible="condition"` to toggle column visibility. Using `invisible` on a list field causes cell layout defects.

### 4. SQL Table Objects (`models.Constraint`, `models.Index`, `models.UniqueIndex`)
- Declare constraints and indexes as class attributes starting with `_`:
  ```python
  _check_qty = models.Constraint("CHECK(quantity > 0)", "Quantity must be positive.")
  _unique_code = models.UniqueIndex("(code) WHERE code IS NOT NULL", "Code must be unique.")
  ```

### 5. QWeb Directive `@t-out`
- Replace all legacy `t-esc` and `t-raw` output directives with `t-out`.

### 6. Record Attributes `_cr`, `_uid`, `_context` Deprecation
- Replace `self._cr`, `self._uid`, `self._context` with `self.env.cr`, `self.env.uid`, `self.env.context`.

### 7. Manifest Hook Signatures
- Module installation hooks accept a single argument: `env`.
  ```python
  def post_init_hook(env):
      env['res.partner'].search([])...
  ```

### 8. Controller Route Types
- JSON controllers must use `type='jsonrpc'`:
  ```python
  @http.route('/my/api/call', type='jsonrpc', auth='user')
  def api_call(self, **kwargs):
  ```

### 9. Safe SQL Composition (`odoo.tools.SQL`)
- Never use raw `%` formatting or string concatenation inside `cr.execute`. Wrap with `odoo.tools.SQL`.

### 10. Dynamic Dates in Domains
- Odoo 19 introduces native dynamic date parsing in domain conditions:
  ```python
  Domain('deadline', '<', 'now')
  Domain('deadline', '>=', 'today')
  Domain('deadline', '<', '-3d +1H')
  Domain('deadline', '>=', '=monday -1w')
  ```

### 11. Field Aggregation (`aggregator` replaces `group_operator`)
- In Odoo 19, use `aggregator="sum"` (or `'avg'`, `'min'`, `'max'`, `'bool_and'`, `'bool_or'`, `'count'`). Setting `group_operator=` triggers a `DeprecationWarning`.

### 12. Removal of `force_company` in Context
- Setting `'force_company'` in context raises a `DeprecationWarning` and has no effect. Always switch companies via `record.with_company(company)`.

### 13. Caching Decorator Simplification (`@ormcache`)
- `@ormcache_context` is deprecated. Use `@ormcache` directly; context keys can be accessed inside the cached method via `self.env.context.get(...)`.
- `skiparg` in `@ormcache` is deprecated.

### 14. Controller `request.env` Attributes
- Accessing `request.cr`, `request.uid`, or `request.context` triggers a `DeprecationWarning`. Use `request.env.cr`, `request.env.uid`, and `request.env.context`.

### 15. Frontend Testing: QUnit -> Hoot (`@odoo/hoot`)
- Odoo 19 completely replaces QUnit with Hoot. All unit tests for OWL components are authored as `*.test.js` using `@odoo/hoot` and bundled under `web.assets_unit_tests`.
