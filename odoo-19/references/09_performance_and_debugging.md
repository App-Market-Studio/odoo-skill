# Odoo 19.0: Performance & Debugging Playbook

This reference provides a battle-tested debugging workflow, common error diagnostics, and performance optimization rules for Odoo 19 developers.

---

## 1. Structured 9-Step Debugging Workflow

When encountering an error, traceback, or unexpected behavior, follow this exact sequence:

1. **Read the Full Traceback**:
   - Identify the exact exception class (`UserError`, `ValidationError`, `AccessError`, `MissingError`, `psycopg2.IntegrityError`, etc.) and error message.
2. **Identify the Root Cause**:
   - Trace through the stack frames down to the specific model, method, and line number where the failure occurs.
3. **Explain the Root Cause in Plain Terms**:
   - Before editing any code, clearly formulate what condition caused the failure (e.g. "recordset expected a singleton but contained 3 records").
4. **Locate the Files**:
   - Search the local codebase or environment addons for the relevant models, methods, or views.
5. **Apply a Minimal, Targeted Fix**:
   - Choose the smallest correct change over rewriting broad blocks of logic.
6. **Verify the Fix**:
   - Confirm that the exception is resolved and explain why the solution works.
7. **Check for Regressions**:
   - Does this fix alter method signatures or break existing dependent workflows?
8. **Check Performance**:
   - Does this fix introduce N+1 database queries, unindexed searches, or slow loops?
9. **Check Security**:
   - Does this bypass access controls (`sudo()`) improperly?

---

## 2. Common Odoo Errors Diagnostic Table

| Error | Common Cause | Recommended Remediation |
| :--- | :--- | :--- |
| `Expected singleton: model(id1, id2)` | Method called on multi-record set when expecting one. | Add `self.ensure_one()` or iterate with `for record in self:` |
| `AccessError: You are not allowed to...` | Missing ACL in `ir.model.access.csv` or failing record rule (`ir.rule`). | Verify group memberships, check `domain_force` evaluation, or verify `company_id`. |
| `ValidationError: ...` | Python `@api.constrains` method triggered. | Inspect constraint logic and check user input against validation rules. |
| `MissingError: Record does not exist...` | Record was deleted or unlinked from DB. | Verify if concurrent transactions removed it or if `exists()` check is needed. |
| `KeyError: 'external_id'` in XML | External ID referenced before declaration, typo, or missing dependency in `__manifest__.py`. | Verify manifest `'depends'`, check loading order in `'data'`, verify XML ID spelling. |
| `ParseError` while parsing XML | Malformed XML, unescaped characters (`&` instead of `&amp;`), or unclosed tag. | Validate XML syntax and ensure proper entity escaping. |
| `RecursionError` in compute | Circular `@api.depends` dependency chain. | Untangle computed field dependencies. Never depend on computed fields that depend back on you. |
| `psycopg2.IntegrityError: null value in column...` | Field marked `required=True` not populated on INSERT. | Set `default=...` on field or pass value in `vals_list` during `create()`. |
| `psycopg2.IntegrityError: duplicate key value...` | Violation of `models.UniqueIndex` or SQL unique constraint. | Ensure uniqueness logic or add random seed / sequence generator. |
| `CacheMiss` | Internal cache miss on deleted or invalidated record attribute. | Check for manual cursor flushes or concurrent worker cache invalidation. |

---

## 3. Performance Engineering Rules

### 1. Eliminating True N+1 Queries & Maximizing Prefetching

Odoo's ORM includes an intelligent **prefetching engine**: when you iterate over a recordset and read a field on the first record (`for rec in records: print(rec.name)`), Odoo automatically prefetches that field for all records in the recordset in a single SQL query. Reading fields in a recordset loop is normal and efficient.

However, you must eliminate **true N+1 query anti-patterns**:

#### A. Nested Searches in Loops (Critical N+1 Anti-Pattern)
```python
# ❌ BAD: Issues N database SELECT queries (one per record)
for partner in partners:
    orders = self.env['sale.order'].search([('partner_id', '=', partner.id)])

# ✅ GOOD: Issues exactly 1 database query for all records combined
orders = self.env['sale.order'].search([('partner_id', 'in', partners.ids)])
```

#### B. Repeated Writes with Identical Values
```python
# ❌ BAD: Issues N database UPDATE queries
for rec in records:
    rec.write({'status': 'processed'})

# ✅ GOOD: Issues a single batched UPDATE query for the entire recordset
records.write({'status': 'processed'})
```

#### C. When Per-Record Loop Processing IS Valid & Necessary
Loops over recordsets are valid and expected in these scenarios:
1. **Individual State Transitions**: When business logic requires checking and executing distinct per-record validations (`rec.action_confirm()`, `rec._check_can_approve()`).
2. **Heterogeneous Value Writes**: When each line receives a distinct calculated value that cannot be computed via a stored computed field or batch update.
3. **External Services**: When making single-item external API calls (e.g., payment gateways, tax calculation engines).

### 2. Recordset Filtering & Sorting

Use built-in recordset methods rather than Python list comprehensions:
- Use `records.filtered(lambda r: r.amount > 100)` or `records.filtered('active')`.
- Use `records.sorted(key='date_order', reverse=True)`.
- Use `records.mapped('field_name')`.

### 3. Record Counting

Never load all records into memory just to count them:

```python
# ❌ BAD: Fetches all IDs and instantiates recordset
total = len(self.env['sale.order'].search([('state', '=', 'draft')]))

# ✅ GOOD: Emits SELECT COUNT(id) directly at the database level
total = self.env['sale.order'].search_count([('state', '=', 'draft')])
```

### 4. Database Aggregation (`_read_group`)

Use `_read_group()` for grouped sums, averages, and counts rather than computing them in Python:

```python
# ✅ GOOD: Optimized PostgreSQL GROUP BY aggregation
result = self.env['sale.order.line']._read_group(
    domain=[('order_id', 'in', orders.ids)],
    groupby=['product_id'],
    aggregates=['price_subtotal:sum', 'product_uom_qty:sum'],
)
for product, subtotal_sum, qty_sum in result:
    ...
```

### 5. PostgreSQL Indexing with `models.Index`

For fields used heavily in domains, search filters, or `_order` clauses:
- Use `index=True` or `index='btree_not_null'` on the field declaration.
- For composite indexes or expressions, declare class table objects:
  ```python
  _partner_date_idx = models.Index("(partner_id, date_order desc)")
  ```

### 6. INSERT Optimization & Nuance with `precompute=True`

For stored computed fields whose dependencies are known at creation time:
- **Child Lines of `One2many`**: Use `precompute=True` (e.g. invoice lines, lease payment schedules created together with parent records). This eliminates a subsequent `UPDATE` query per line.
- **Standalone Parent Records**: Avoid `precompute=True` as a default on parent headers. It bypasses ORM prefetching and adds overhead on single-record inserts.

```python
# Child line model (ideal for precompute)
class PropertyLeaseLine(models.Model):
    _name = 'property.lease.line'

    subtotal = fields.Monetary(
        compute='_compute_subtotal',
        store=True,
        precompute=True,  # Computed before batch INSERT on parent write/create
    )
```

### 7. Discipline with `sudo()` in Loops

Avoid calling `sudo()` inside loops:

```python
# ❌ BAD: Swapping environment context on each iteration
for rec in records:
    rec.sudo().write(...)

# ✅ GOOD: Elevate privileges once for the entire batch
records.sudo().write(...)
```

---

## 4. Transaction Boundaries & Atomicity

> [!IMPORTANT]
> **Transaction Safety Principles**:
> 1. **Framework Lifecycle**: Standard business logic must rely on Odoo's automatic request/cron transaction lifecycle.
> 2. **Rollback Boundaries (`savepoint`)**: When a recoverable operation inside a loop or external integration might fail, use `with self.env.cr.savepoint():` to establish a safe rollback boundary without aborting the entire process. Do not require savepoints dogmatically around every loop.
> 3. **Manual `cr.commit()` Restriction**: Treat manual `cr.commit()` as strictly exceptional. Require explicit justification, idempotency, and recovery design for chunked batch cron jobs. Never commit inside normal controller or UI actions.

```python
# Recoverable operation boundary (e.g. external sync or optional task)
for partner in partners:
    try:
        with self.env.cr.savepoint():
            partner.sync_with_external_crm()
    except Exception as e:
        _logger.warning("CRM sync failed for partner %s: %s", partner.id, e)
        # Outer transaction continues safely; failed sub-operation is rolled back
```
