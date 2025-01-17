from odoo.tests import TransactionCase


class TestProductTemplate(TransactionCase):
    def test_is_system_multi_lang(self):
        """
        Test case to check if the is_system_multi_lang field is
        set correctly based on the system's language count.
        """
        product_template = self.env["product.template"].create(
            {
                "name": "Test Product",
            }
        )

        lang_count = self.env["res.lang"].search_count([])

        # Ensure only one language exists, unlink others
        if lang_count > 1:
            langs = self.env["res.lang"].search([("code", "!=", "en_US")])
            langs.unlink()

        product_template._compute_is_system_multi_lang()

        # Check if the computed value is correct based on language count
        if lang_count == 1:
            self.assertFalse(
                product_template.is_system_multi_lang,
                "The is_system_multi_lang field should be False "
                "when only one language exists.",
            )
        else:
            self.assertTrue(
                product_template.is_system_multi_lang,
                "The is_system_multi_lang field should be True "
                "when multiple languages exist.",
            )

    def test_prepare_variant_values(self):
        """
        Test case to check if the description is included when preparing variant values.
        """
        product_template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "description": "Product template description",
            }
        )

        # Using correct model
        combination = self.env["product.attribute.value"].browse([])

        variant_values = product_template._prepare_variant_values(combination)

        self.assertEqual(
            variant_values.get("description"),
            product_template.description,
            "The description should be included in the prepared variant values.",
        )
