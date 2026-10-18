#!/usr/bin/env python3
"""
Unit Test Suite for Odoo 19 Compatibility Linter (Safeguard 2)
Tests every linter rule with:
- At least one positive example that MUST trigger the rule.
- At least one negative (valid) example that MUST NOT trigger the rule.
- Documents static analysis limitations for each rule.
"""

import sys
import unittest
from pathlib import Path

# Add script directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from verify_odoo19_compat import check_xml_lines, check_python_lines, Issue


class TestOdoo19LinterRules(unittest.TestCase):
    """Test suite verifying each rule has positive trigger and negative pass tests."""

    # ==================== XML RULES ====================

    def test_rule_xml_tree_view(self):
        """Rule: XML_TREE_VIEW (ERROR)
        Limitation: Static regex checks tag syntax; dynamic XML generation via Python string concatenation cannot be detected.
        """
        # Positive trigger
        bad_lines = ['<record id="v1" model="ir.ui.view">', '    <tree string="Items">', '    </tree>', '</record>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_TREE_VIEW" and i.severity == "ERROR" for i in issues))

        # Negative valid case
        good_lines = ['<record id="v1" model="ir.ui.view">', '    <list string="Items">', '    </list>', '</record>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_TREE_VIEW" for i in issues))

    def test_rule_xml_attrs_deprecated(self):
        """Rule: XML_ATTRS_DEPRECATED (ERROR)
        Limitation: Detects attrs= in XML files; dynamic DOM alterations in JS are outside static scope.
        """
        # Positive trigger
        bad_lines = ['<field name="amount" attrs="{\'invisible\': [(\'state\', \'=\', \'draft\')]}"/>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_ATTRS_DEPRECATED" and i.severity == "ERROR" for i in issues))

        # Negative valid case
        good_lines = ['<field name="amount" invisible="state == \'draft\'"/>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_ATTRS_DEPRECATED" for i in issues))

    def test_rule_xml_states_deprecated(self):
        """Rule: XML_STATES_DEPRECATED (ERROR)
        Limitation: Only inspects XML tag attributes.
        """
        # Positive trigger
        bad_lines = ['<button name="action_confirm" states="draft,confirmed"/>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_STATES_DEPRECATED" and i.severity == "ERROR" for i in issues))

        # Negative valid case
        good_lines = ['<button name="action_confirm" invisible="state not in (\'draft\', \'confirmed\')"/>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_STATES_DEPRECATED" for i in issues))

    def test_rule_xml_view_mode_tree(self):
        """Rule: XML_VIEW_MODE_TREE (WARNING)
        Limitation: Only catches 'tree' in XML view_mode fields; dynamic view_mode set in act_window python code is handled separately.
        """
        # Positive trigger
        bad_lines = ['<field name="view_mode">tree,form</field>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_VIEW_MODE_TREE" and i.severity == "WARNING" for i in issues))

        # Negative valid case
        good_lines = ['<field name="view_mode">list,form</field>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_VIEW_MODE_TREE" for i in issues))

    def test_rule_xml_t_esc_deprecated(self):
        """Rule: XML_T_ESC_DEPRECATED (ERROR)
        Limitation: Scans QWeb XML templates. Does not scan inline client JS template strings without XML tags.
        """
        # Positive trigger
        bad_esc = ['<h3 t-esc="props.title"/>']
        bad_raw = ['<div t-raw="raw_content"/>']
        self.assertTrue(any(i.code == "XML_T_ESC_DEPRECATED" for i in check_xml_lines(bad_esc)))
        self.assertTrue(any(i.code == "XML_T_ESC_DEPRECATED" for i in check_xml_lines(bad_raw)))

        # Negative valid case
        good_lines = ['<h3 t-out="props.title"/>']
        self.assertFalse(any(i.code == "XML_T_ESC_DEPRECATED" for i in check_xml_lines(good_lines)))

    def test_rule_xml_legacy_chatter(self):
        """Rule: XML_LEGACY_CHATTER (WARNING)
        Limitation: Matches class="...oe_chatter...".
        """
        # Positive trigger
        bad_lines = ['<div class="oe_chatter">', '    <field name="message_ids"/>', '</div>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_LEGACY_CHATTER" for i in issues))

        # Negative valid case
        good_lines = ['<chatter/>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_LEGACY_CHATTER" for i in issues))

    def test_rule_xml_list_column_invisible(self):
        """Rule: XML_LIST_COLUMN_INVISIBLE (WARNING)
        Limitation: Scans field tags within list tags.
        """
        # Positive trigger
        bad_lines = ['<list>', '    <field name="code" invisible="1"/>', '</list>']
        issues = check_xml_lines(bad_lines)
        self.assertTrue(any(i.code == "XML_LIST_COLUMN_INVISIBLE" for i in issues))

        # Negative valid case
        good_lines = ['<list>', '    <field name="code" column_invisible="True"/>', '</list>']
        issues = check_xml_lines(good_lines)
        self.assertFalse(any(i.code == "XML_LIST_COLUMN_INVISIBLE" for i in issues))

    # ==================== PYTHON RULES ====================

    def test_rule_py_deprecated_cr_uid_context(self):
        """Rules: PY_DEPRECATED_CR, PY_DEPRECATED_UID, PY_DEPRECATED_CONTEXT (ERROR)
        Limitation: Detects direct record attribute access; does not resolve dynamic getattr(self, '_cr').
        """
        # Positive triggers
        self.assertTrue(any(i.code == "PY_DEPRECATED_CR" for i in check_python_lines(["self._cr.execute('SELECT 1')"])))
        self.assertTrue(any(i.code == "PY_DEPRECATED_UID" for i in check_python_lines(["user_id = self._uid"])))
        self.assertTrue(any(i.code == "PY_DEPRECATED_CONTEXT" for i in check_python_lines(["c = self._context.get('lang')"])))

        # Negative valid cases
        self.assertFalse(any(i.code == "PY_DEPRECATED_CR" for i in check_python_lines(["self.env.cr.execute('SELECT 1')"])))
        self.assertFalse(any(i.code == "PY_DEPRECATED_UID" for i in check_python_lines(["user_id = self.env.uid"])))
        self.assertFalse(any(i.code == "PY_DEPRECATED_CONTEXT" for i in check_python_lines(["c = self.env.context.get('lang')"])))

    def test_rule_py_deprecated_osv(self):
        """Rule: PY_DEPRECATED_OSV (ERROR)
        Limitation: Flags direct import statements.
        """
        bad = ["from odoo.osv import osv", "import odoo.osv"]
        for line in bad:
            self.assertTrue(any(i.code == "PY_DEPRECATED_OSV" for i in check_python_lines([line])))

        good = ["from odoo import models, fields, api"]
        self.assertFalse(any(i.code == "PY_DEPRECATED_OSV" for i in check_python_lines(good)))

    def test_rule_py_route_type_json(self):
        """Rule: PY_ROUTE_TYPE_JSON (ERROR)
        Limitation: Detects route decorators specifying type='json'.
        """
        bad = ["@http.route('/api/test', type='json', auth='user')"]
        self.assertTrue(any(i.code == "PY_ROUTE_TYPE_JSON" and i.severity == "ERROR" for i in check_python_lines(bad)))

        good = ["@http.route('/api/test', type='jsonrpc', auth='user')"]
        self.assertFalse(any(i.code == "PY_ROUTE_TYPE_JSON" for i in check_python_lines(good)))

    def test_rule_py_deprecated_name_get(self):
        """Rule: PY_DEPRECATED_NAME_GET (WARNING)
        Limitation: Flags method definition 'def name_get'.
        """
        bad = ["    def name_get(self):", "        return [(r.id, r.name) for r in self]"]
        self.assertTrue(any(i.code == "PY_DEPRECATED_NAME_GET" for i in check_python_lines(bad)))

        good = ["    @api.depends('name')", "    def _compute_display_name(self):", "        for r in self: r.display_name = r.name"]
        self.assertFalse(any(i.code == "PY_DEPRECATED_NAME_GET" for i in check_python_lines(good)))

    def test_rule_py_hook_signature(self):
        """Rule: PY_DEPRECATED_HOOK_SIGNATURE (ERROR)
        Limitation: Detects 2-arg hook functions (cr, registry).
        """
        bad = ["def post_init_hook(cr, registry):", "    pass"]
        self.assertTrue(any(i.code == "PY_DEPRECATED_HOOK_SIGNATURE" for i in check_python_lines(bad)))

        good = ["def post_init_hook(env):", "    pass"]
        self.assertFalse(any(i.code == "PY_DEPRECATED_HOOK_SIGNATURE" for i in check_python_lines(good)))

    def test_rule_py_unsafe_sql(self):
        """Rule: PY_UNSAFE_SQL (WARNING)
        Limitation: Detects string interpolation '%' in cr.execute calls. Dynamic SQL strings built beforehand cannot be verified.
        """
        bad = ['self.env.cr.execute("SELECT * FROM property WHERE id = %s" % record_id)']
        self.assertTrue(any(i.code == "PY_UNSAFE_SQL" for i in check_python_lines(bad)))

        good = ['self.env.cr.execute(SQL("SELECT * FROM property WHERE id = %s", record_id))']
        self.assertFalse(any(i.code == "PY_UNSAFE_SQL" for i in check_python_lines(good)))

    def test_rule_py_sql_constraints_deprecated(self):
        """Rule: PY_SQL_CONSTRAINTS_DEPRECATED (WARNING)
        Limitation: Detects class-level _sql_constraints assignments.
        """
        bad = ["    _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique.')]"]
        self.assertTrue(any(i.code == "PY_SQL_CONSTRAINTS_DEPRECATED" for i in check_python_lines(bad)))

        good = ["    _code_uniq = models.UniqueIndex('(code) WHERE code IS NOT NULL', 'Code must be unique.')"]
        self.assertFalse(any(i.code == "PY_SQL_CONSTRAINTS_DEPRECATED" for i in check_python_lines(good)))

    def test_rule_py_table_object_underscore(self):
        """Rule: PY_TABLE_OBJECT_UNDERSCORE (ERROR)
        Limitation: Matches models.Constraint, models.Index, models.UniqueIndex missing leading underscore.
        """
        bad = ["    positive_amount = models.Constraint('CHECK(amount > 0)', 'Must be positive.')"]
        self.assertTrue(any(i.code == "PY_TABLE_OBJECT_UNDERSCORE" for i in check_python_lines(bad)))

        good = ["    _positive_amount = models.Constraint('CHECK(amount > 0)', 'Must be positive.')"]
        self.assertFalse(any(i.code == "PY_TABLE_OBJECT_UNDERSCORE" for i in check_python_lines(good)))

    def test_rule_py_create_missing_decorator(self):
        """Rule: PY_CREATE_MISSING_MODEL_CREATE_MULTI (WARNING)
        Limitation: Inspects preceding 3 lines for @api.model_create_multi.
        """
        bad = ["    def create(self, vals_list):", "        return super().create(vals_list)"]
        self.assertTrue(any(i.code == "PY_CREATE_MISSING_MODEL_CREATE_MULTI" for i in check_python_lines(bad)))

        good = ["    @api.model_create_multi", "    def create(self, vals_list):", "        return super().create(vals_list)"]
        self.assertFalse(any(i.code == "PY_CREATE_MISSING_MODEL_CREATE_MULTI" for i in check_python_lines(good)))

    def test_rule_py_group_operator_deprecated(self):
        """Rule: PY_GROUP_OPERATOR_DEPRECATED (WARNING)
        Limitation: Checks for group_operator= parameter in fields.
        """
        bad = ["    total = fields.Monetary(string='Total', group_operator='sum')"]
        self.assertTrue(any(i.code == "PY_GROUP_OPERATOR_DEPRECATED" for i in check_python_lines(bad)))

        good = ["    total = fields.Monetary(string='Total', aggregator='sum')"]
        self.assertFalse(any(i.code == "PY_GROUP_OPERATOR_DEPRECATED" for i in check_python_lines(good)))

    def test_rule_py_request_deprecated_attr(self):
        """Rule: PY_REQUEST_DEPRECATED_ATTR (ERROR)
        Limitation: Flags request.cr, request.uid, request.context.
        """
        bad = ["    cr = request.cr", "    uid = request.uid", "    ctx = request.context"]
        for line in bad:
            self.assertTrue(any(i.code == "PY_REQUEST_DEPRECATED_ATTR" for i in check_python_lines([line])))

        good = ["    cr = request.env.cr", "    uid = request.env.uid", "    ctx = request.env.context"]
        for line in good:
            self.assertFalse(any(i.code == "PY_REQUEST_DEPRECATED_ATTR" for i in check_python_lines([line])))

    def test_rule_py_force_company_deprecated(self):
        """Rule: PY_FORCE_COMPANY_DEPRECATED (ERROR)
        Limitation: Flags force_company in context dicts or with_context. Does NOT flag legitimate 'company' keys.
        """
        bad1 = ["    res = self.with_context(force_company=c.id)"]
        bad2 = ["    ctx = {'force_company': c.id}"]
        self.assertTrue(any(i.code == "PY_FORCE_COMPANY_DEPRECATED" for i in check_python_lines(bad1)))
        self.assertTrue(any(i.code == "PY_FORCE_COMPANY_DEPRECATED" for i in check_python_lines(bad2)))

        # Legitimate company context key must NOT be flagged
        good1 = ["    res = self.with_company(c)"]
        good2 = ["    c_id = self.env.context.get('company')"]
        good3 = ["    ctx = {'company': c.id}"]
        self.assertFalse(any(i.code == "PY_FORCE_COMPANY_DEPRECATED" for i in check_python_lines(good1)))
        self.assertFalse(any(i.code == "PY_FORCE_COMPANY_DEPRECATED" for i in check_python_lines(good2)))
        self.assertFalse(any(i.code == "PY_FORCE_COMPANY_DEPRECATED" for i in check_python_lines(good3)))

    def test_rule_py_ormcache_context_deprecated(self):
        """Rule: PY_ORMCACHE_CONTEXT_DEPRECATED (WARNING)
        Limitation: Detects @ormcache_context decorator.
        """
        bad = ["    @ormcache_context('key')", "    def _get_val(self): pass"]
        self.assertTrue(any(i.code == "PY_ORMCACHE_CONTEXT_DEPRECATED" for i in check_python_lines(bad)))

        good = ["    @tools.ormcache()", "    def _get_val(self): pass"]
        self.assertFalse(any(i.code == "PY_ORMCACHE_CONTEXT_DEPRECATED" for i in check_python_lines(good)))

    def test_rule_py_domain_uppercase_operator(self):
        """Rule: PY_DOMAIN_UPPERCASE_OPERATOR (WARNING)
        Limitation: Detects static domain tuples with uppercase operators like 'LIKE', 'IN'.
        """
        bad = ["    domain = [('state', 'IN', ['draft', 'done'])]"]
        self.assertTrue(any(i.code == "PY_DOMAIN_UPPERCASE_OPERATOR" for i in check_python_lines(bad)))

        good = ["    domain = [('state', 'in', ['draft', 'done'])]"]
        self.assertFalse(any(i.code == "PY_DOMAIN_UPPERCASE_OPERATOR" for i in check_python_lines(good)))

    # ==================== INFO RULES ====================

    def test_rule_py_manual_cr_commit(self):
        """Rule: PY_MANUAL_CR_COMMIT (INFO)
        Limitation: Flags cr.commit() for architectural awareness. Does not inspect cron job idempotency without AST.
        """
        info_lines = ["    self.env.cr.commit()"]
        issues = check_python_lines(info_lines)
        self.assertTrue(any(i.code == "PY_MANUAL_CR_COMMIT" and i.severity == "INFO" for i in issues))

        clean_lines = ["    with self.env.cr.savepoint():", "        partner.action_sync()"]
        issues = check_python_lines(clean_lines)
        self.assertFalse(any(i.code == "PY_MANUAL_CR_COMMIT" for i in issues))

    def test_rule_py_precompute_notice(self):
        """Rule: PY_PRECOMPUTE_NOTICE (INFO)
        Limitation: Flags precompute=True for architectural notice without evaluating whether model is One2many child line.
        """
        info_lines = ["    total = fields.Monetary(compute='_comp', store=True, precompute=True)"]
        issues = check_python_lines(info_lines)
        self.assertTrue(any(i.code == "PY_PRECOMPUTE_NOTICE" and i.severity == "INFO" for i in issues))

        clean_lines = ["    total = fields.Monetary(compute='_comp', store=True)"]
        issues = check_python_lines(clean_lines)
        self.assertFalse(any(i.code == "PY_PRECOMPUTE_NOTICE" for i in issues))


if __name__ == "__main__":
    unittest.main(verbosity=2)
