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

## 7. Assets Declaration in Manifest

Declare assets bundles inside `__manifest__.py`:

```python
'assets': {
    'web.assets_backend': [
        'my_module/static/src/components/**/*.js',
        'my_module/static/src/components/**/*.xml',
        'my_module/static/src/scss/**/*.scss',
    ],
},
```
