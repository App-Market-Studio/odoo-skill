# Odoo 19.0: OWL 2 & Frontend Framework Reference

The Odoo frontend is built on **OWL 2** (Odoo Web Library), a declarative component framework using QWeb templates and standard reactive primitives.

---

## 1. Native JavaScript Module System

All JavaScript code in Odoo 19 uses native ES6 modules. Files located under `/static/src/` are automatically transpiled into Odoo modules:

```javascript
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
```

- When creating files in custom addon subdirectories, add `/** @odoo-module **/` as the first line if outside `/static/src`.
- Relative imports work across files within the same addon (`import { helper } from "./utils";`).
- Cross-addon imports use `@addon_name/path/to/file` (e.g. `@web/core/registry`).

---

## 2. OWL 2 Component Structure

A standard Odoo 19 OWL component:

```javascript
/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PropertyDashboard extends Component {
    static template = "my_module.PropertyDashboard";
    static props = {
        title: { type: String, optional: true },
        limit: { type: Number, optional: true },
    };
    static defaultProps = {
        title: "Properties Overview",
        limit: 10,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            properties: [],
            isLoading: true,
            filterState: "all",
        });

        onWillStart(async () => {
            await this.loadProperties();
        });
    }

    async loadProperties() {
        this.state.isLoading = true;
        try {
            const domain = this.state.filterState === "all" ? [] : [["state", "=", this.state.filterState]];
            this.state.properties = await this.orm.searchRead(
                "estate.property",
                domain,
                ["id", "name", "price", "state"],
                { limit: this.props.limit, order: "id desc" }
            );
        } catch (error) {
            this.notification.add("Failed to load properties", { type: "danger" });
        } finally {
            this.state.isLoading = false;
        }
    }

    async openProperty(propertyId) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "estate.property",
            res_id: propertyId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async onFilterChange(ev) {
        this.state.filterState = ev.target.value;
        await this.loadProperties();
    }
}
```

---

## 3. QWeb XML Template

OWL component templates are defined in XML files loaded via `web.assets_backend`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="my_module.PropertyDashboard">
        <div class="o_property_dashboard p-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3 t-out="props.title"/>
                <div class="d-flex gap-2">
                    <select class="form-select form-select-sm" t-on-change="onFilterChange">
                        <option value="all">All</option>
                        <option value="draft">Draft</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="done">Sold</option>
                    </select>
                </div>
            </div>

            <div t-if="state.isLoading" class="text-center py-5">
                <i class="fa fa-circle-o-notch fa-spin fa-2x text-primary"/>
            </div>

            <div t-else="" class="row g-3">
                <t t-foreach="state.properties" t-as="property" t-key="property.id">
                    <div class="col-md-4">
                        <div class="card h-100 shadow-sm cursor-pointer"
                             t-on-click="() => this.openProperty(property.id)">
                            <div class="card-body">
                                <h5 class="card-title" t-out="property.name"/>
                                <p class="card-text text-muted">
                                    Price: <strong t-out="property.price"/>
                                </p>
                                <span class="badge bg-primary" t-out="property.state"/>
                            </div>
                        </div>
                    </div>
                </t>
            </div>
        </div>
    </t>
</templates>
```

---

## 4. Web Client Registries

Registries (`@web/core/registry`) are the main extension point for views, fields, client actions, and services.

### Registering a Client Action
```javascript
import { registry } from "@web/core/registry";
import { PropertyDashboard } from "./property_dashboard";

registry.category("actions").add("estate_property_dashboard", PropertyDashboard);
```

### Registering a Custom Field Component
```javascript
import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class RatingField extends Component {
    static template = xml`
        <span class="d-inline-flex gap-1">
            <t t-foreach="[1, 2, 3, 4, 5]" t-as="star" t-key="star">
                <i class="fa fa-star cursor-pointer"
                   t-att-class="star &lt;= props.record.data[props.name] ? 'text-warning' : 'text-muted'"
                   t-on-click="() => this.setRating(star)"/>
            </t>
        </span>
    `;
    static props = { ...standardFieldProps };

    setRating(val) {
        this.props.record.update({ [this.props.name]: val });
    }
}

export const ratingField = {
    component: RatingField,
    supportedTypes: ["integer"],
};

registry.category("fields").add("star_rating", ratingField);
```

---

## 5. Web Client Services

Services provide injectable dependencies and cross-cutting capabilities:

| Service | Hook | Usage |
| :--- | :--- | :--- |
| `orm` | `useService("orm")` | Execute ORM model calls: `searchRead`, `read`, `write`, `call`, `unlink` |
| `action` | `useService("action")` | Trigger window actions, client actions, notifications |
| `notification` | `useService("notification")` | Display toast alerts: `.add(message, { type: 'success' })` |
| `dialog` | `useService("dialog")` | Display modals and confirmation dialogs |
| `user` | `useService("user")` | User info: `userId`, `context`, `hasGroup` |
| `company` | `useService("company")` | Current company: `currentCompany`, `allowedCompanies` |

> [!IMPORTANT]
> **Calling Backend APIs: ORM Service vs `rpc` Function**:
> - **Model Methods (`models.Model`)**: Always use `this.orm = useService("orm")`:
>   ```javascript
>   const result = await this.orm.call("estate.property", "action_calculate_stats", [recordId]);
>   ```
> - **Controller Routes (`@http.route(type='jsonrpc')`)**: `useService("rpc")` does **NOT** exist. Import the `rpc` function directly from `@web/core/network/rpc`:
>   ```javascript
>   import { rpc } from "@web/core/network/rpc";
>
>   // Call custom controller route
>   const response = await rpc("/my/api/endpoint", { param1: value1 });
>   ```

### Custom Service Definition
```javascript
import { registry } from "@web/core/registry";

export const propertyAnalyticsService = {
    dependencies: ["orm", "notification"],
    start(env, { orm, notification }) {
        return {
            async trackMetric(metricName, value) {
                await orm.call("estate.analytics", "record_metric", [metricName, value]);
                notification.add(`Metric ${metricName} recorded.`, { type: "info" });
            },
        };
    },
};

registry.category("services").add("propertyAnalytics", propertyAnalyticsService);
```

---

## 6. Patching Existing Components

Modify existing core components cleanly using `patch`:

```javascript
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    setup() {
        super.setup();
        // Custom setup logic
    },
    async onRecordSaved(record) {
        await super.onRecordSaved(...arguments);
        // Custom post-save handler
    },
});
```

---

---

## 7. Static Files & Web Assets Organization

Standard Odoo module web assets follow a strict folder and file structure:

```text
static/
├── description/
│   └── icon.png             # Module app icon (128x128 PNG)
├── img/                     # Static images (do NOT link to external URLs; copy into codebase)
├── lib/                     # Third-party libraries (NEVER add minified JS; unminified source only)
├── src/
│   ├── js/                  # OWL 2 components, hooks, services
│   │   └── tours/           # User tutorial tours (not test tours)
│   ├── scss/                # SCSS stylesheets
│   └── xml/                 # QWeb component templates
└── tests/
    ├── tours/               # Automated tour test suites
    └── *.test.js            # Modern Hoot unit tests (@odoo/hoot)
```

> [!IMPORTANT]
> **Static Asset Rules**:
> - File names MUST only contain lowercase alphanumerics and underscores: `^[a-z0-9_]+$`.
> - Correct permissions: directory `755`, file `644`.
> - Never add minified JavaScript libraries (`*.min.js`). Always keep readable, unminified sources for auditability and diff review.
> - Never hotlink external web assets: copy images, fonts, and libraries directly into `static/`.

---

## 8. CSS & SCSS Coding Guidelines

Odoo enforces strict styling guidelines for SCSS and CSS:

### 1. Syntax & Formatting
- **Indentation**: Exactly 4 spaces, no tabs.
- **Line Width**: Max 80 characters per line.
- **Braces**: Opening brace `{` preceded by a single space; closing brace `}` on its own new line.
- **Declarations**: Exactly one CSS declaration per line.

### 2. Properties Order ("Outside-In")
Order CSS properties from the outermost box-model/positioning elements to inner decorative rules:
1. `position`, `top`, `right`, `bottom`, `left`, `z-index`, `@include o-position-absolute(...)`
2. `display`, `flex`, `grid`, `align-items`, `justify-content`
3. `margin`, `margin-*`
4. `width`, `height`, `min-width`, `max-width`
5. `border`, `border-*`, `border-radius`
6. `padding`, `padding-*`
7. `background`, `background-*`, `color`
8. `font`, `font-size`, `font-weight`, `line-height`, `text-align`
9. `box-shadow`, `opacity`, `transform`, `transition`, `filter`

### 3. Variables Placement
Scoped SCSS variables (`$-var`) and CSS custom properties (`--var`) MUST be placed at the very top of the declaration block, separated from CSS rules by a blank line:

```scss
.o_custom_item {
    // 1. Scoped SCSS and contextual CSS variables at the very top
    $-inner-gap: 1rem;
    --CustomItem-bg: #{$o-view-background-color};
    --CustomItem__title-color: #{$o-main-text-color};

    // 2. Position -> Display -> Margin -> Size -> Border -> Padding -> Background -> Font -> Filter
    position: relative;
    display: flex;
    margin-bottom: $-inner-gap;
    width: 100%;
    border: 1px solid $o-gray-300;
    padding: $-inner-gap;
    background-color: var(--CustomItem-bg);
    font-size: $font-size-base;
    box-shadow: $box-shadow-sm;
}
```

### 4. Naming Conventions
- **No ID selectors**: Avoid `#id` selectors in CSS/SCSS.
- **Class Prefix**: Prefix all component and view classes with `.o_<module_name>` (web client core uses `.o_`).
- **Grandchild Class Naming**: Avoid deep chaining like `.o_element_wrapper_entries_entry_link`. Use the Grandchild pattern:
  ```html
  <!-- Good: Grandchild Pattern -->
  <div class="o_custom_item">
      <div class="o_custom_item_entries">
          <span class="o_custom_item_entry">
              <a class="o_custom_item_link">Link</a>
          </span>
      </div>
  </div>
  ```
- **SCSS Variables**: `$o-[root]-[element]-[property]-[modifier]` (defines design system tokens).
- **Scoped SCSS Variables**: `$-[variable-name]` (accessible only inside the enclosing block).
- **SCSS Mixins & Functions**: `o-[name]`, imperative verb for functions (`o-invert-color`), optional parameters `$-[arg]`.
- **CSS Variables (BEM)**: `--[root]__[element]-[property]--[modifier]`.
- **Strict Role Separation**:
  - **SCSS Variables**: Define the compile-time design system tokens.
  - **CSS Variables**: Strictly for runtime, DOM-related **contextual adaptation** (e.g. adapting a component when rendered inside a form view or modal).
  - **No `:root`**: Never declare UI variables on `:root` in Odoo modules.

---

## 9. Assets Declaration in Manifest

Declare assets bundles inside `__manifest__.py`:

```python
'assets': {
    'web.assets_backend': [
        'my_module/static/src/js/**/*.js',
        'my_module/static/src/xml/**/*.xml',
        'my_module/static/src/scss/**/*.scss',
    ],
    'web.assets_unit_tests': [
        'my_module/static/tests/**/*.test.js',
    ],
},
```
