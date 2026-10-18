# Odoo 19.0: Security & Access Control Reference

Odoo enforces security via two primary mechanisms:
1. **Access Control Lists (`ir.model.access`)**: Coarse-grained model-level permissions (CRUD).
2. **Record Rules (`ir.rule`)**: Fine-grained row-level filters evaluated during SQL generation.

---

## 1. Access Control Lists (`ir.model.access.csv`)

Stored in `security/ir.model.access.csv` and loaded via the `'data'` list in `__manifest__.py`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_estate_property_user,estate.property.user,model_estate_property,my_module.group_estate_user,1,1,1,0
access_estate_property_manager,estate.property.manager,model_estate_property,my_module.group_estate_manager,1,1,1,1
access_estate_property_line_user,estate.property.line.user,model_estate_property_line,my_module.group_estate_user,1,1,1,0
access_estate_property_line_manager,estate.property.line.manager,model_estate_property_line,my_module.group_estate_manager,1,1,1,1
```

### Conventions & Rules:
- `id`: Unique external ID for the access rule (`access_<model>_<group>`).
- `name`: Descriptive identifier (`<model_name>.<group_name>`).
- `model_id:id`: Reference to the model XML ID, prefixed with `model_` and dots replaced by underscores (e.g. `estate.property` -> `model_estate_property`).
- `group_id:id`: Reference to the group XML ID (e.g. `base.group_user`, or your module's group `my_module.group_estate_user`). Leave empty for public access.
- `perm_read`, `perm_write`, `perm_create`, `perm_unlink`: `1` (granted) or `0` (denied).
- **Explicit Security Design**: Require an explicit security design for each custom model. A model intentionally inaccessible to ordinary users (e.g. internal financial audit logs, system-level ledgers) should not be given broad user access merely to satisfy a generic checklist.
- **Role Scoping**: Standard operational users typically get read/write/create, but **not unlink**. Only managers receive unlink permissions.

---

## 2. Inherited Model Security (Safeguard 1)

> [!IMPORTANT]
> **Do not recreate native security rules blindly.**
> For inherited models such as `res.partner`, `product.template`, or `account.move`, always inspect Odoo's existing ACLs and record rules first in `/home/ams/odoo_skill/19.0/19 source code/odoo-19.0/addons/`. Extend or adjust them only when the business requirements specifically justify it. Overriding native security definitions without inspection can break core workflows, create privilege escalations, or cause unexpected `AccessError` exceptions during standard ERP operations.

---

## 3. Security Groups (`res.groups`)

Declare security groups in `security/res_groups.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Module Category -->
    <record id="module_category_estate" model="ir.module.category">
        <field name="name">Real Estate</field>
        <field name="description">Manage properties, offers, and contracts.</field>
        <field name="sequence">20</field>
    </record>

    <!-- Standard User Group -->
    <record id="group_estate_user" model="res.groups">
        <field name="name">Agent / User</field>
        <field name="category_id" ref="module_category_estate"/>
        <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <!-- Manager Group (inherits User group) -->
    <record id="group_estate_manager" model="res.groups">
        <field name="name">Manager / Administrator</field>
        <field name="category_id" ref="module_category_estate"/>
        <field name="implied_ids" eval="[(4, ref('group_estate_user'))]"/>
        <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    </record>
</odoo>
```

---

## 4. Record Rules (`ir.rule`)

Declare record rules in `security/ir_rules.xml` wrapped inside `<odoo noupdate="1">`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">

    <!-- 1. Multi-Company Rule: Applied according to model ownership design -->
    <record id="rule_estate_property_multicompany" model="ir.rule">
        <field name="name">Estate Property: Multi-Company</field>
        <field name="model_id" ref="model_estate_property"/>
        <field name="domain_force">['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]</field>
    </record>

    <!-- 2. Personal Records Rule: Users see their own assigned records -->
    <record id="rule_estate_property_personal" model="ir.rule">
        <field name="name">Estate Property: Personal Records</field>
        <field name="model_id" ref="model_estate_property"/>
        <field name="domain_force">['|', ('user_id', '=', user.id), ('user_id', '=', False)]</field>
        <field name="groups" eval="[(4, ref('my_module.group_estate_user'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="False"/>
    </record>

    <!-- 3. Manager Rule: Managers see all records -->
    <record id="rule_estate_property_manager_all" model="ir.rule">
        <field name="name">Estate Property: Manager All</field>
        <field name="model_id" ref="model_estate_property"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="groups" eval="[(4, ref('my_module.group_estate_manager'))]"/>
    </record>

</odoo>
```

---

## 5. `sudo()` Discipline

- **Never use `sudo()` for convenience**: Only elevate privileges when business logic strictly requires it (e.g. sequence generation, posting system logs, cross-company reads).
- **Narrow Scope**: Always re-scope to the minimal necessary recordset or field operation:
  ```python
  # ❌ BAD: Broad privilege elevation
  self.sudo().write({'state': 'confirmed', 'partner_id': 5})

  # ✅ GOOD: Narrow, explicit elevation
  next_seq = self.env['ir.sequence'].sudo().next_by_code('estate.property')
  ```
- **Document Rationale**: Always include an inline comment explaining why `sudo()` is safe and required.

---

## 6. Modern ORM Access Validation API

In Odoo 19, use the consolidated access methods:

```python
# Check access and raise an AccessError if denied
self.check_access('read')
self.check_access('write')
self.check_access('create')
self.check_access('unlink')

# Boolean test (returns True/False without raising)
can_edit = self.has_access('write')
can_delete = self.has_access('unlink')

# Filter recordset down to accessible records
accessible_records = self._filtered_access('read')
```

---

## 7. Multi-Company Architecture & Decision Matrix

> [!TIP]
> **Operational Rule**: *Determine company ownership, visibility, and relational consistency from the business requirements and native Odoo model behavior. Enforce company boundaries where required, while preserving intentional shared records.*

### Multi-Company Decision Matrix

| Model Classification | Native Framework Examples | `company_id` Declaration | `ir.rule` Domain Force | `check_company=True` Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Optionally Shared Models** | `res.partner` (contacts), `product.template` (catalog) | `fields.Many2one('res.company', string='Company')` *(Nullable)* | `['\|', ('company_id', '=', False), ('company_id', 'in', company_ids)]` | Apply only to relations that require company consistency, preserving shared partner references. |
| **Strictly Company-Dependent Models** | `account.move` (invoices), `sale.order`, property lease agreements | `fields.Many2one('res.company', required=True, default=lambda self: self.env.company)` | `[('company_id', 'in', company_ids)]` | Apply to journals, accounts, warehouses, and tax lines that must match parent company. |
| **Shared / Global Models** | `res.currency`, `res.country`, `uom.uom`, system parameters | **Do NOT define `company_id`** | None (Cross-company visible) | Never apply `check_company=True`. |

### Implementation Checklist:
1. **Auto-Consistency Enforcement**: Add `_check_company_auto = True` to models with company-dependent relationships.
2. **Relational Field Scoping**: Apply `check_company=True` strictly to relational fields that require company consistency (e.g. journal or account on an invoice), **not** blindly across every relationship.
3. **Current Company Access**: Use `self.env.company` (or `self.env.companies` for multi-selected active companies), never `self.env.user.company_id`.
4. **Company Switching (Odoo 19)**:
   - Use `record.with_company(target_company)`.
   - ⚠️ `context['force_company']` is completely obsolete and raises a `DeprecationWarning` in Odoo 19. Do not use it.
