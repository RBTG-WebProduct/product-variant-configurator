# Copyright 2016 ACSONE SA/NV
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.base.tests.common import BaseCommon


class TestPurchaseOrder(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # ENVIRONMENTS
        cls.product_attribute = cls.env["product.attribute"]
        cls.product_attribute_value = cls.env["product.attribute.value"]
        cls.product_template = cls.env["product.template"].with_context(
            check_variant_creation=True
        )
        cls.purchase_order = cls.env["purchase.order"]
        cls.product_product = cls.env["product.product"]
        cls.purchase_order_line = cls.env["purchase.order.line"]
        cls.res_partner = cls.env["res.partner"]
        cls.product_category = cls.env["product.category"]

        # Instances: product category
        cls.category1 = cls.product_category.create(
            {"name": "No create variants category"}
        )

        # Instances: product attribute
        cls.attribute1 = cls.product_attribute.create({"name": "Test Attribute 1"})

        # Instances: product attribute value
        cls.value1 = cls.product_attribute_value.create(
            {"name": "Value 1", "attribute_id": cls.attribute1.id}
        )
        cls.value2 = cls.product_attribute_value.create(
            {"name": "Value 2", "attribute_id": cls.attribute1.id}
        )

        # Instances: supplier
        cls.supplier = cls.res_partner.create(
            {"name": "Supplier 1", "is_company": True}
        )
        # Instances: product template
        cls.product_template_yes = cls.product_template.create(
            {
                "name": "Product template 1",
                "description_purchase": "Purchase Description",
                "no_create_variants": "yes",
                "categ_id": cls.category1.id,
                "standard_price": 100,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.attribute1.id,
                            "value_ids": [(6, 0, [cls.value1.id, cls.value2.id])],
                        },
                    )
                ],
            }
        )
        cls.supplier_pricelist = cls.env["product.supplierinfo"].create(
            {
                "product_tmpl_id": cls.product_template_yes.id,
                "partner_id": cls.supplier.id,
                "min_qty": 11,
                "price": 90,
            }
        )
        cls.product_template_no = cls.product_template.create(
            {
                "name": "Product template 2",
                "categ_id": cls.category1.id,
                "no_create_variants": "no",
                "description_purchase": "Purchase Description",
            }
        )
        cls.env.user.groups_id += cls.env.ref("uom.group_uom")

    def test_onchange_product_tmpl_id_01(self):
        line1 = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_yes.id,
                "price_unit": 100,
                "product_uom": self.product_template_yes.uom_id.id,
                "product_qty": 1,
                "name": "Line 1",
                "date_planned": "2016-01-01",
            }
        )
        expected_domain = [("product_tmpl_id", "=", self.product_template_yes.id)]
        self.assertEqual(line1.product_id_configurator_domain, expected_domain)
        line2 = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_no.id,
                "product_uom": self.product_template_no.uom_id.id,
                "product_qty": 1,
                "price_unit": 200,
                "name": "Line 2",
                "date_planned": "2016-01-01",
            }
        )
        line2._onchange_product_tmpl_id_configurator()
        line2._onchange_product_id_configurator()
        line2.onchange_product_id()
        self.assertEqual(line2.product_id, self.product_template_no.product_variant_ids)
        self.assertEqual(
            line2.name,
            f"{self.product_template_no.name}\n{self.product_template_no.description_purchase}",
        )

    def test_can_create_product_variant(self):
        line = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_yes.id,
                "price_unit": 100,
                "name": "Line 1",
                "product_qty": 1,
                "date_planned": "2016-01-01",
                "product_uom": self.product_template_yes.uom_id.id,
            }
        )
        self.assertFalse(line.can_create_product)
        attributes = self.env["product.configurator.attribute"].create(
            {
                "product_tmpl_id": self.product_template_yes.id,
                "attribute_id": self.attribute1.id,
                "value_id": self.value1.id,
                "owner_model": "purchase.order.line",
                "owner_id": line.id,
            }
        )
        line.product_attribute_ids = attributes
        line._onchange_product_attribute_ids_configurator()
        self.assertTrue(line.can_create_product)
        line.create_product_variant = True
        line._onchange_create_product_variant()
        self.assertTrue(line.product_id)
        self.assertFalse(line.create_product_variant)

    def test_button_confirm_01(self):
        order = self.purchase_order.create({"partner_id": self.supplier.id})
        line_1 = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_yes.id,
                "price_unit": 100,
                "name": "Line 1",
                "product_qty": 1,
                "date_planned": "2016-01-01",
                "product_uom": self.product_template_yes.uom_id.id,
                "product_attribute_ids": [
                    (
                        0,
                        0,
                        {
                            "product_tmpl_id": self.product_template_yes.id,
                            "attribute_id": self.attribute1.id,
                            "value_id": self.value1.id,
                            "owner_model": "purchase.order.line",
                        },
                    )
                ],
                "create_product_variant": True,
            }
        )
        line_2 = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_no.id,
                "product_uom": self.product_template_no.uom_id.id,
                "product_qty": 1,
                "price_unit": 200,
                "name": "Line 2",
                "date_planned": "2016-01-01",
                "create_product_variant": True,
            }
        )
        for line in (line_1, line_2):
            line._onchange_product_tmpl_id_configurator()
            line._onchange_product_id_configurator()
            line.onchange_product_id()
            line._onchange_product_attribute_ids_configurator()
            if line.can_create_product:
                line.create_variant_if_needed()
                line.create_product_variant = True
                line._onchange_create_product_variant()
        order.write({"order_line": [(4, line_1.id), (4, line_2.id)]})
        order.button_confirm()
        order.flush_recordset()
        order.invalidate_recordset()
        order_line_without_product = order.order_line.filtered(
            lambda x: not x.product_id
        )
        self.assertEqual(
            len(order_line_without_product),
            0,
            "All purchase lines must have a product",
        )

    def test_compute_product_id_is_required(self):
        # Set the company configuration to True
        self.env.company.po_confirm_create_variant = True
        line = self.purchase_order_line.new(
            {
                "product_tmpl_id": self.product_template_yes.id,
                "product_uom": self.product_template_yes.uom_id.id,
                "product_qty": 5,
                "company_id": self.env.company.id,  # Explicitly set the company
            }
        )
        line._compute_product_id_is_required()
        self.assertFalse(
            line.product_id_is_required,
            "Product ID should not be required when po_confirm_create_variant is True.",
        )

        # Set the company configuration to False
        self.env.company.po_confirm_create_variant = False
        line._compute_product_id_is_required()
        self.assertTrue(
            line.product_id_is_required,
            "Product ID should be required when po_confirm_create_variant is False.",
        )

    def test_create_purchase_order_line_with_variant_creation(self):
        # Create a purchase order in 'purchase' state
        order = self.purchase_order.create({"partner_id": self.supplier.id})
        order.button_confirm()  # Move the order to 'purchase' state

        # Create a line without a product but with a product template
        line_vals = {
            "order_id": order.id,
            "product_tmpl_id": self.product_template_yes.id,
            "product_uom": self.product_template_yes.uom_id.id,
            "product_qty": 1,
            "name": "Line with variant creation",
            "date_planned": "2024-01-01",
        }
        line = self.purchase_order_line.create([line_vals])

        # Ensure a product was created
        self.assertTrue(
            line.product_id, "Product variant should be created for the line."
        )
