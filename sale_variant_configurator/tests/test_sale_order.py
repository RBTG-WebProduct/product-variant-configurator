# Copyright 2017 David Vidal
# Copyright 2024 Carolina Fernandez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.tests import Form, TransactionCase


class TestSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Environments
        cls.product_attribute = cls.env["product.attribute"]
        cls.product_attribute_value = cls.env["product.attribute.value"]
        cls.product_template = cls.env["product.template"].with_context(
            check_variant_creation=True
        )
        cls.sale_order = cls.env["sale.order"]
        cls.product_product = cls.env["product.product"]
        cls.sale_order_line = cls.env["sale.order.line"]
        cls.res_partner = cls.env["res.partner"]
        cls.product_category = cls.env["product.category"]

        # Instances
        cls.category1 = cls.product_category.create(
            {"name": "No create variants category"}
        )
        cls.attribute1 = cls.product_attribute.create(
            {"name": "Color (sale_variante_configurator)"}
        )
        cls.value1 = cls.product_attribute_value.create(
            {"name": "Red", "attribute_id": cls.attribute1.id}
        )
        cls.value2 = cls.product_attribute_value.create(
            {"name": "Green", "attribute_id": cls.attribute1.id}
        )
        cls.product_template_yes = cls.product_template.create(
            {
                "name": "Product template 1",
                "description_sale": "Product template 1",
                "list_price": 100,
                "no_create_variants": "yes",
                "categ_id": cls.category1.id,
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
        cls.product_template_no = cls.product_template.create(
            {
                "name": "Product template 2",
                "list_price": 100,
                "categ_id": cls.category1.id,
                "no_create_variants": "no",
                "description_sale": "Template description",
            }
        )
        cls.attr_lines = cls.product_template_yes.attribute_line_ids
        cls.ptav_1 = cls.attr_lines.product_template_value_ids.filtered(
            lambda x: x.product_attribute_value_id == cls.value1[0]
        )
        cls.ptav_1.price_extra = 10
        cls.customer = cls.res_partner.create({"name": "Customer 1"})

    def test_sale_order_line_attribute_ids(self):
        """
        Test that product attributes and price adjustments are correctly applied.
        """
        product = self.product_product.create(
            {
                "name": self.product_template_yes.name,
                "list_price": 100,
                "product_tmpl_id": self.product_template_yes.id,
                "product_attribute_ids": [
                    (
                        0,
                        0,
                        {
                            "product_tmpl_id": self.product_template_yes.id,
                            "attribute_id": self.attribute1.id,
                            "value_id": self.value1.id,
                            "owner_model": "sale.order.line",
                        },
                    )
                ],
            }
        )
        order_form = Form(self.sale_order)
        order_form.partner_id = self.customer
        with order_form.order_line.new() as line_form:
            line_form.product_tmpl_id = self.product_template_yes
            with line_form.product_attribute_ids.edit(0) as attribute_line_form:
                attribute_line_form.value_id = self.value1
        sale = order_form.save()
        line = sale.order_line
        self.assertEqual(line.price_unit, 110)
        self.assertEqual(line.price_extra, 10)
        self.assertEqual(line.product_id, product)

    def test_create_product_variant_on_line_creation(self):
        """
        Test dynamic creation of product variant when adding a line to confirmed orders.
        """
        sale = self.sale_order.create({"partner_id": self.customer.id})
        line_vals = {
            "order_id": sale.id,
            "product_tmpl_id": self.product_template_yes.id,
            "price_unit": 100,
            "name": "Line 1",
            "product_uom_qty": 1,
            "product_uom": self.product_template_yes.uom_id.id,
        }
        line = self.sale_order_line.create(line_vals)
        line.create_variant_if_needed()
        self.assertTrue(line.product_id)
        self.assertEqual(line.product_id.product_tmpl_id, self.product_template_yes)
        sale.action_confirm()
        line = sale.order_line[0]
        self.assertTrue(line.product_id)
