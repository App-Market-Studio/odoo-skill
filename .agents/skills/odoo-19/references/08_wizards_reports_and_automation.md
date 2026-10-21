# Odoo 19.0: Wizards, Reports & Automation Reference

This guide details best practices for creating interactive dialogs (Wizards / TransientModels), QWeb PDF Reports, Scheduled Actions (Crons), and Number Sequences in Odoo 19.0.

---

## 1. Wizards & Dialogs (`models.TransientModel`)

Wizards are temporary data records stored in memory/database that are automatically vacuumed periodically. They are primarily used for multi-step workflows, bulk actions, and user confirmation forms.

### Python Pattern: `wizard/<transient>.py` (e.g. `wizard/estate_property_batch.py`)

> [!IMPORTANT]
> **Official Odoo Transient (Wizard) Naming Guidelines**:
> - Pattern: `<related_base_model>.<action>` (e.g. `estate.property.confirm.batch`, `account.invoice.make`).
> - **Avoid the word `wizard`** in `_name` and file naming.
> - File naming: `wizard/<transient>.py` and `wizard/<transient>_views.xml`.

```python
# -*- coding: utf-8 -*-
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EstatePropertyBatch(models.TransientModel):
    _name = 'estate.property.batch'
    _description = 'Batch Property Confirmation'

    # Grab active records from the context
    target_ids = fields.Many2many(
        'estate.property',
        string='Target Records',
        default=lambda self: self.env.context.get('active_ids'),
        required=True,
    )
    reason = fields.Text(string='Confirmation Reason', required=True)
    notify_partners = fields.Boolean(string='Notify Partners', default=True)

    def action_apply(self):
        """Execute the wizard logic and close the modal dialog."""
        self.ensure_one()
        if not self.target_ids:
            raise UserError(_("No records selected for processing."))

        # Perform batched operation
        for record in self.target_ids:
            record.action_confirm_with_reason(self.reason)

        if self.notify_partners:
            self.target_ids.mapped('partner_id')._notify_batch_update()

        # Close the dialog window in the web client
        return {'type': 'ir.actions.act_window_close'}
```

### XML View Pattern: `wizard/<transient>_views.xml` (e.g. `wizard/estate_property_batch_views.xml`)

Wizard forms must include a `<footer>` containing the submit button and a Cancel button with `special="cancel"`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- View XML ID: <model_name>_view_<type>, View name matches XML ID with dots -->
    <record id="estate_property_batch_view_form" model="ir.ui.view">
        <field name="name">estate.property.batch.view.form</field>
        <field name="model">estate.property.batch</field>
        <field name="arch" type="xml">
            <form string="Batch Confirmation">
                <sheet>
                    <group>
                        <field name="reason" placeholder="Explain why these items are confirmed..."/>
                        <field name="notify_partners"/>
                    </group>
                    <notebook>
                        <page string="Selected Records" name="records">
                            <field name="target_ids" readonly="1">
                                <list>
                                    <field name="name"/>
                                    <field name="partner_id"/>
                                    <field name="state"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>
                <footer>
                    <button name="action_apply"
                            string="Confirm &amp; Apply"
                            type="object"
                            class="btn-primary"/>
                    <button string="Cancel"
                            class="btn-secondary"
                            special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

    <!-- Window Action: <model_name>_action to launch wizard modal from list view -->
    <record id="estate_property_batch_action" model="ir.actions.act_window">
        <field name="name">Batch Confirmation</field>
        <field name="res_model">estate.property.batch</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
        <field name="binding_model_id" ref="model_estate_property"/>
        <field name="binding_view_types">list</field>
    </record>

</odoo>
```

---

## 2. QWeb PDF Reports (`ir.actions.report`)

Odoo 19 generates PDF reports via QWeb templates and `wkhtmltopdf`.

### Report Action Declaration: `report/<model>_reports.xml` (e.g. `report/estate_property_reports.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Action XML ID: <model_name>_action_report -->
    <record id="estate_property_action_report" model="ir.actions.report">
        <field name="name">Property Summary Report</field>
        <field name="model">estate.property</field>
        <field name="report_type">qweb-pdf</field>
        <field name="report_name">my_module.report_property_template</field>
        <field name="report_file">my_module.report_property_template</field>
        <field name="print_report_name">'Property_%s' % (object.name.replace('/', '_'))</field>
        <field name="binding_model_id" ref="model_estate_property"/>
        <field name="binding_type">report</field>
    </record>

</odoo>
```

### QWeb Template: `report/<model>_templates.xml` (e.g. `report/estate_property_templates.xml`)

> [!IMPORTANT]
> **Strict QWeb Rule**: Never use `<t t-esc="..." />` or `<t t-raw="..." />`. Always use `t-out`.

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <template id="report_item_template">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc">
                <t t-call="web.external_layout">
                    <div class="page">
                        <div class="oe_structure"/>
                        <h2 class="mt-4 mb-3">
                            <span>Item: </span>
                            <span t-out="doc.name"/>
                        </h2>

                        <div class="row mt-3 mb-4">
                            <div class="col-6">
                                <strong>Customer: </strong>
                                <span t-out="doc.partner_id.name"/><br/>
                                <strong>Date: </strong>
                                <span t-out="doc.date_deadline"/>
                            </div>
                            <div class="col-6 text-end">
                                <strong>Status: </strong>
                                <span t-out="doc.state"/><br/>
                                <strong>Total: </strong>
                                <span t-field="doc.total_amount"/>
                            </div>
                        </div>

                        <table class="table table-sm o_main_table table-striped mt-3">
                            <thead>
                                <tr>
                                    <th>Description</th>
                                    <th class="text-end">Quantity</th>
                                    <th class="text-end">Unit Price</th>
                                    <th class="text-end">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr t-foreach="doc.line_ids" t-as="line">
                                    <td><span t-out="line.description"/></td>
                                    <td class="text-end"><span t-out="line.quantity"/></td>
                                    <td class="text-end"><span t-out="line.price_unit"/></td>
                                    <td class="text-end"><span t-field="line.subtotal"/></td>
                                </tr>
                            </tbody>
                        </table>
                        <div class="oe_structure"/>
                    </div>
                </t>
            </t>
        </t>
    </template>

</odoo>
```

---

## 3. Scheduled Actions / Cron Jobs (`ir.cron`)

Cron jobs run background automated tasks on scheduled intervals.

### XML Declaration: `data/ir_cron.xml`

Always put scheduled actions under `<odoo noupdate="1">` so user-configured timing adjustments are not overwritten on module updates:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">

    <record id="ir_cron_daily_item_check" model="ir.cron">
        <field name="name">My Module: Daily Status Check</field>
        <field name="model_id" ref="model_my_module_item"/>
        <field name="state">code</field>
        <field name="code">model._cron_daily_check()</field>
        <field name="user_id" ref="base.user_root"/>
        <field name="interval_number">1</field>
        <field name="interval_type">days</field>
        <field name="active">True</field>
    </record>

</odoo>
```

### Python Method: `models/my_item.py`

- The cron method **must be private** (name starts with `_`).
- Always process in batches to prevent transaction timeouts and memory overflow.
- Use explicit commits (`self.env.cr.commit()`) only when processing independent chunks.

```python
@api.model
def _cron_daily_check(self):
    """Daily check for expired records."""
    expired_records = self.search([
        ('state', '=', 'draft'),
        ('date_deadline', '<', fields.Date.today()),
    ], limit=500)

    for record in expired_records:
        try:
            record.action_cancel()
        except Exception as e:
            _logger.error("Failed to auto-cancel record %s: %s", record.id, e)
```

---

## 4. Number Sequences (`ir.sequence`)

Sequences provide continuous, formatted identifiers (e.g. `INV/2026/00001`).

### XML Declaration: `data/ir_sequence_data.xml`

Always declare sequences in `data/ir_sequence_data.xml` with `noupdate="1"`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">

    <record id="seq_my_module_item" model="ir.sequence">
        <field name="name">Custom Item Sequence</field>
        <field name="code">my.module.item</field>
        <field name="prefix">ITM/%(year)s/</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>

</odoo>
```

### Consuming Sequences in Python:

Override `create()` with `@api.model_create_multi`:

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if not vals.get('name') or vals.get('name') == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('my.module.item') or _('New')
    return super().create(vals_list)
```
