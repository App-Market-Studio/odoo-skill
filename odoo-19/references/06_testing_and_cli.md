# Odoo 19.0: Testing & CLI Tools Reference

Testing is an integral part of Odoo development. Odoo provides a custom test runner built on Python's standard `unittest` framework with automated database rollback and transaction management.

---

## 1. Test Directory Structure

Tests must be placed in a `tests/` sub-package inside your addon:

```text
my_module/
├── __init__.py
├── __manifest__.py
├── models/
├── tests/
│   ├── __init__.py          # Must import all test modules!
│   ├── test_property.py     # Unit tests for models
│   └── test_ui.py           # Integration / Tour / Http tests
```

> [!WARNING]
> Test files will **not** be executed if they are not explicitly imported in `tests/__init__.py`:
> ```python
> # tests/__init__.py
> from . import test_property
> from . import test_ui
> ```

---

## 2. Writing Python Unit Tests (`TransactionCase`)

In a `TransactionCase`, each test method runs in its own database transaction and is automatically rolled back upon completion:

```python
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install', 'estate')
class TestEstateProperty(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create common fixtures once for all test methods
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Buyer',
            'email': 'buyer@example.com',
        })
        cls.property = cls.env['estate.property'].create({
            'name': 'Test Villa',
            'partner_id': cls.partner.id,
            'expected_price': 250000.0,
            'state': 'draft',
        })

    def test_property_initial_state(self):
        """Test initial state of a newly created property."""
        self.assertEqual(self.property.state, 'draft')
        self.assertTrue(self.property.active)

    def test_action_confirm(self):
        """Test transitioning from draft to confirmed."""
        self.property.action_confirm()
        self.assertEqual(self.property.state, 'confirmed')

    def test_negative_price_raises_validation_error(self):
        """Test that negative prices are rejected by constrains."""
        with self.assertRaises(ValidationError):
            self.env['estate.property'].create({
                'name': 'Invalid Property',
                'expected_price': -100.0,
            })
```

---

## 3. Writing Web / HTTP Tests (`HttpCase`)

`HttpCase` provides an HTTP client and can launch a headless Chrome instance to test tours and endpoints:

```python
from odoo.tests import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestEstateHttp(HttpCase):

    def test_public_endpoint(self):
        response = self.url_open('/estate/properties')
        self.assertEqual(response.status_code, 200)

    def test_ui_tour(self):
        self.start_tour("/web", "estate_property_tour", login="admin")
```

---

## 4. Test Tags (`@tagged`)

The `@tagged` decorator specifies when tests should run:
- `'post_install'`: Runs after all modules are installed (recommended for most tests).
- `'-at_install'`: Prevents running during initial module installation (saves time when dependencies are still initializing).
- Custom tags (e.g. `'estate'`): Allows running a targeted subset of tests via `--test-tags`.

---

## 5. Running Tests from the Command Line

Run tests using `odoo-bin` with `--test-enable` and `--stop-after-init`:

```bash
# Run tests for a specific module
odoo-bin -c odoo.conf -d test_db --test-enable --stop-after-init -i my_module --test-tags my_module

# Run only post-install tests for a custom tag
odoo-bin -c odoo.conf -d test_db --test-enable --stop-after-init --test-tags .estate

# Run tests with debug log output
odoo-bin -c odoo.conf -d test_db --test-enable --stop-after-init --log-level=test --test-tags my_module
```

---

## 6. Daily Developer CLI Flags

Boost development productivity with hot-reloading:

```bash
# Auto-reload python code and XML view definitions without restarting
odoo-bin -c odoo.conf -d dev_db --dev=all

# Targeted dev flags
odoo-bin -c odoo.conf -d dev_db --dev=xml,reload,qweb
```

---

## 7. Automated Code Upgrade Tool

Odoo provides a built-in AST rewriter to assist with version migrations:

```bash
# Preview changes for Odoo 18.0 -> 19.0 migration without modifying files
odoo-bin upgrade_code --from 18.0 --to 19.0 --addons-path=/path/to/addons --dry-run

# Apply code migrations
odoo-bin upgrade_code --from 18.0 --to 19.0 --addons-path=/path/to/addons
```

---

## 8. Modern Frontend & OWL Unit Testing with Hoot (`@odoo/hoot`)

In Odoo 18 and 19, legacy QUnit has been completely replaced by **Hoot** (`@odoo/hoot`), a fast, modern test runner and assertion framework for OWL 2 components and web client services.

### Directory Structure & Manifest Setup
Place frontend tests in `static/tests/` and load them in `web.assets_unit_tests`:

```python
# __manifest__.py
'assets': {
    'web.assets_backend': [
        'my_module/static/src/**/*',
    ],
    'web.assets_unit_tests': [
        'my_module/static/tests/**/*.test.js',
    ],
},
```

### Writing a Component Test (`static/tests/my_component.test.js`)
```javascript
/** @odoo-module **/

import { describe, expect, test } from "@odoo/hoot";
import { queryFirst } from "@odoo/hoot-dom";
import { mountWithCleanup } from "@web/../tests/_framework/component_test_helpers";
import { defineModels, fields, models } from "@web/../tests/_framework/mock_server";
import { PropertyDashboard } from "@my_module/components/property_dashboard";

// Define mock models for frontend testing
class Property extends models.Model {
    _name = "estate.property";
    name = fields.Char();
    price = fields.Float();
    state = fields.Selection({
        selection: [["draft", "Draft"], ["confirmed", "Confirmed"]],
    });

    _records = [
        { id: 1, name: "Beachside Villa", price: 500000.0, state: "confirmed" },
    ];
}

describe("PropertyDashboard Component", () => {
    test("renders property list and responds to clicks", async () => {
        defineModels([Property]);

        await mountWithCleanup(PropertyDashboard);

        expect(".property-card").toHaveCount(1);
        expect(queryFirst(".property-title")).toHaveText("Beachside Villa");
    });
});
```

### Running Hoot Frontend Tests
1. **In Browser**: Navigate to `http://localhost:8069/web/tests?mod=my_module` to run the interactive test suite with DOM inspector.
2. **From CLI**: Run via `odoo-bin --test-enable` targeting tours and HttpCases.
