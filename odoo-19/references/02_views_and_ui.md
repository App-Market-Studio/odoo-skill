# Odoo 19.0: Views & User Interface Reference

In Odoo 19, the UI architecture requires **`<list>`** views instead of legacy `<tree>` tags, direct Python expressions for dynamic attributes instead of `attrs="..."`, and `<chatter/>` components for messaging integration.

---

## 1. List Views (`<list>`)

In Odoo 19, tabular views are declared using `<list>`:

```xml
<record id="estate_property_view_list" model="ir.ui.view">
    <field name="name">estate.property.view.list</field>
    <field name="model">estate.property</field>
    <field name="arch" type="xml">
        <list string="Properties"
              decoration-success="state == 'done'"
              decoration-info="state == 'confirmed'"
              decoration-muted="state == 'cancel'"
              sample="1">
            <field name="sequence" widget="handle"/>
            <field name="name" decoration-bf="1"/>
            <field name="partner_id"/>
            <field name="expected_price" sum="Total Expected"/>
            <field name="selling_price"/>
            <field name="date_deadline" optional="show"/>
            <field name="state"
                   widget="badge"
                   decoration-success="state == 'done'"
                   decoration-info="state == 'confirmed'"/>
            <!-- Column visibility must use column_invisible in list views -->
            <field name="company_id" groups="base.group_multi_company" optional="hide"/>
        </list>
    </field>
</record>
```

### Key List View Attributes
- `editable="bottom"` or `editable="top"`: Enables inline row editing.
- `decoration-*="python_expression"`: Dynamically applies color styles to rows (`decoration-danger`, `decoration-success`, `decoration-warning`, `decoration-info`, `decoration-muted`, `decoration-bf`, `decoration-it`).
- `sample="1"`: Displays mock records when the table is empty to onboard users.
- `optional="show"` or `optional="hide"`: Allows users to toggle column visibility from the column selector dropdown.
- `column_invisible="python_expression"`: Hides an entire column dynamically based on parent/context conditions.

---

## 2. Dynamic Attribute Syntax (No `attrs` or `states`)

Odoo 19 does **NOT** support `attrs="{'invisible': ...}"` or `states="..."`.
All conditions are expressed as direct Python expressions:

```xml
<!-- Invisible condition based on field value -->
<button name="action_confirm"
        type="object"
        string="Confirm"
        class="btn-primary"
        invisible="state != 'draft'"/>

<!-- Multiple fields condition with context check -->
<field name="partner_id"
       readonly="state in ('done', 'cancel')"
       required="price > 0 and not context.get('skip_partner')"/>

<!-- Column invisible in list view lines -->
<field name="discount"
       column_invisible="parent.state == 'done'"/>

<!-- Widget modifiers -->
<field name="email"
       invisible="not partner_id"/>
```

---

## 3. Form Views (`<form>`)

```xml
<record id="estate_property_view_form" model="ir.ui.view">
    <field name="name">estate.property.view.form</field>
    <field name="model">estate.property</field>
    <field name="arch" type="xml">
        <form string="Property">
            <header>
                <button name="action_confirm"
                        type="object"
                        string="Confirm"
                        class="btn-primary"
                        invisible="state != 'draft'"/>
                <button name="action_cancel"
                        type="object"
                        string="Cancel"
                        invisible="state not in ('draft', 'confirmed')"/>
                <button name="action_draft"
                        type="object"
                        string="Reset to Draft"
                        invisible="state != 'cancel'"/>
                <!-- Statusbar widget -->
                <field name="state"
                       widget="statusbar"
                       statusbar_visible="draft,confirmed,done"/>
            </header>
            <sheet>
                <!-- Button Box with Stat Buttons -->
                <div class="oe_button_box" name="button_box">
                    <button name="action_view_offers"
                            type="object"
                            class="oe_stat_button"
                            icon="fa-money"
                            invisible="offer_count == 0">
                        <field name="offer_count" widget="statinfo" string="Offers"/>
                    </button>
                </div>
                <widget name="web_ribbon" title="Sold" bg_color="text-bg-success" invisible="state != 'done'"/>
                <widget name="web_ribbon" title="Archived" bg_color="text-bg-danger" invisible="active"/>
                <div class="oe_title">
                    <label for="name"/>
                    <h1>
                        <field name="name" placeholder="e.g. Sunny Suburban Villa"/>
                    </h1>
                </div>
                <group>
                    <group name="left">
                        <field name="partner_id"/>
                        <field name="property_type_id"/>
                        <field name="date_deadline"/>
                    </group>
                    <group name="right">
                        <field name="expected_price"/>
                        <field name="selling_price" readonly="1"/>
                        <field name="active" invisible="1"/>
                        <field name="company_id" groups="base.group_multi_company"/>
                    </group>
                </group>
                <notebook>
                    <page string="Property Lines" name="lines">
                        <field name="line_ids">
                            <list editable="bottom">
                                <field name="name"/>
                                <field name="amount"/>
                            </list>
                        </field>
                    </page>
                    <page string="Internal Notes" name="description">
                        <field name="description" placeholder="Additional details..."/>
                    </page>
                </notebook>
            </sheet>
            <!-- Chatter Integration -->
            <chatter reload_on_post="True"/>
        </form>
    </field>
</record>
```

### Chatter Element (`<chatter/>`)
Replaces the legacy `div.oe_chatter` construct. Supported attributes:
- `open_attachments="True"`: Displays attachment drawer opened by default.
- `reload_on_attachment="True"`: Reloads form when attachments are altered.
- `reload_on_follower="True"`: Reloads form when followers change.
- `reload_on_post="True"`: Reloads form view when messages are sent.

---

## 4. Search Views (`<search>`)

```xml
<record id="estate_property_view_search" model="ir.ui.view">
    <field name="name">estate.property.view.search</field>
    <field name="model">estate.property</field>
    <field name="arch" type="xml">
        <search string="Search Properties">
            <field name="name" string="Property" filter_domain="['|', ('name', 'ilike', self), ('description', 'ilike', self)]"/>
            <field name="partner_id"/>
            <field name="expected_price"/>

            <filter string="Available" name="available" domain="[('state', 'in', ('draft', 'confirmed'))]"/>
            <filter string="Sold" name="sold" domain="[('state', '=', 'done')]"/>
            <separator/>
            <filter string="Archived" name="inactive" domain="[('active', '=', False)]"/>

            <group expand="0" string="Group By">
                <filter string="Buyer / Partner" name="group_partner" context="{'group_by': 'partner_id'}"/>
                <filter string="Status" name="group_status" context="{'group_by': 'state'}"/>
            </group>
        </search>
    </field>
</record>
```

---

## 5. Window Actions & Menu Hierarchy

Window action `view_mode` must use **`list,form`**:

```xml
<!-- Window Action -->
<record id="estate_property_action" model="ir.actions.act_window">
    <field name="name">Properties</field>
    <field name="res_model">estate.property</field>
    <field name="view_mode">list,form,kanban</field>
    <field name="search_view_id" ref="estate_property_view_search"/>
    <field name="context">{'search_default_available': 1}</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">
            Create your first estate property!
        </p>
    </field>
</record>

<!-- Menu Structure: Root -> Category -> Action -->
<menuitem id="estate_menu_root"
          name="Real Estate"
          sequence="10"
          web_icon="my_module,static/description/icon.png"/>

<menuitem id="estate_menu_main"
          name="Operations"
          parent="estate_menu_root"
          sequence="10"/>

<menuitem id="estate_menu_properties"
          name="Properties"
          parent="estate_menu_main"
          action="estate_property_action"
          sequence="10"/>
```

---

## 6. Official XML IDs & Naming Patterns

Official Odoo guidelines enforce consistent XML ID and record name patterns:

| Record Type | XML ID Pattern | Name Field Pattern | Example |
| :--- | :--- | :--- | :--- |
| **View** | `<model_name>_view_<view_type>` | Identical to XML ID with dots replacing `_` | `id="estate_property_view_form"`<br>`<field name="name">estate.property.view.form</field>` |
| **Action** | `<model_name>_action` (or `_action_<detail>`) | Human-readable display label | `id="estate_property_action"`<br>`<field name="name">Properties</field>` |
| **Menu** | `<model_name>_menu` or `<model_name>_menu_<action>` | Human-readable menu title | `id="estate_property_menu_root"`<br>`<field name="name">Real Estate</field>` |
| **Security Group** | `<module_name>_group_<group_name>` | Human-readable role title | `id="my_module_group_user"`<br>`<field name="name">User</field>` |
| **Record Rule** | `<model_name>_rule_<concerned_group>` | Descriptive rule label | `id="estate_property_rule_company"` |

> [!IMPORTANT]
> **The `<data>` Tag Rule**:
> - The `<data>` tag is **ONLY used to declare non-updatable records** with `noupdate="1"`.
> - If an entire file contains only non-updatable records (e.g. sequences, rules), set `noupdate="1"` directly on the root `<odoo>` tag (`<odoo noupdate="1">`) and **do NOT use a `<data>` tag**.
> - Never wrap standard views or actions in a `<data>` tag without `noupdate`.
> - Syntactic sugar tags (`<menuitem>` and `<template>`) are preferred over the `<record>` notation.

---

## 7. View Inheritance with `<xpath>`

Customize standard views cleanly using XPath extensions:

```xml
<!-- Official Inheriting XML Rule:
     1. XML ID MUST be identical to the original record ID (module prefix prevents collisions).
     2. View name MUST have an '.inherit.<details>' suffix.
     3. Primary view overrides declare <field name="mode">primary</field> and use a new ID.
-->
<record id="view_partner_form" model="ir.ui.view">
    <field name="name">res.partner.view.form.inherit.estate</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <!-- Add a stat button in the button box -->
        <xpath expr="//div[@name='button_box']" position="inside">
            <button name="action_view_properties"
                    type="object"
                    class="oe_stat_button"
                    icon="fa-home">
                <field name="property_count" widget="statinfo" string="Properties"/>
            </button>
        </xpath>

        <!-- Insert a new page in notebook -->
        <xpath expr="//notebook" position="inside">
            <page string="Real Estate" name="real_estate">
                <field name="property_ids" readonly="1">
                    <list>
                        <field name="name"/>
                        <field name="expected_price"/>
                        <field name="state"/>
                    </list>
                </field>
            </page>
        </xpath>

        <!-- Modify an existing element's attributes -->
        <xpath expr="//field[@name='email']" position="attributes">
            <attribute name="required">1</attribute>
        </xpath>
    </field>
</record>
```

### XPath Architectural Rules
1. **Always name `<group>` and `<page>` elements** (`name="group_details"`, `name="page_lines"`). Unnamed elements force developers to use brittle positional XPaths like `//group[2]` or `//page[1]` which break upon core module upgrades.
2. **Anchor on named attributes**: Prefer `//field[@name='...']`, `//group[@name='...']`, or `//page[@name='...']`. Never use fragile tag-index paths (`//form/sheet/div[2]/group[1]`).
3. **Verify parent context**: When inheriting views, ensure the target `inherit_id` is loaded in your module's `depends` chain.

---

## 7. QWeb & Template Rules (Strictly Enforced)

1. **Absolute Ban on `@t-esc` and `@t-raw`**:
   - Never generate `<t t-esc="..." />` or `<t t-raw="..." />`.
   - Odoo 19 explicitly uses `@t-out` for variables, text expressions, and field content rendering.
   - *Example Syntax:*
     ```xml
     <span t-out="object.partner_id.name"/>
     <t t-out="user_id.name[:20] + '...' if len(user_id.name) > 20 else user_id.name"/>
     ```
2. **Inline Values**:
   - Avoid string output evaluation inside vanilla element bodies. Always rely on structural attributes using `t-out`.
