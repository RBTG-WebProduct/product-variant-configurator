from odoo.tests.common import TransactionCase


class TestProductPricelist(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a sample pricelist for testing
        cls.product_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": cls.env.ref("base.USD").id,  # Using the USD currency
            }
        )

    def test_pricelist_creation(self):
        """Test that the pricelist is created successfully."""
        self.assertTrue(self.product_pricelist, "The pricelist should be created.")
        self.assertEqual(
            self.product_pricelist.name,
            "Test Pricelist",
            "The pricelist name should match.",
        )

    def test_pricelist_currency(self):
        """Test that the pricelist is associated with the correct currency."""
        currency = self.env.ref("base.USD")
        self.assertEqual(
            self.product_pricelist.currency_id,
            currency,
            "The pricelist should use the USD currency.",
        )

    def test_pricelist_deletion(self):
        """Test that the pricelist can be deleted without issues."""
        pricelist_id = self.product_pricelist.id
        self.product_pricelist.unlink()
        deleted_pricelist = self.env["product.pricelist"].browse(pricelist_id)
        self.assertFalse(
            deleted_pricelist.exists(), "The pricelist should be deleted successfully."
        )

    def test_select_seller_with_empty_product(self):
        """Test the `_select_seller` method when called on an empty recordset."""
        product = self.env["product.product"]  # Empty recordset

        # Call the _select_seller method
        selected_seller = product._select_seller(
            partner_id=False,
            quantity=0.0,
        )

        # Assert that the result is False for an empty recordset
        self.assertFalse(
            selected_seller,
            "The _select_seller method should return False for an empty recordset.",
        )
