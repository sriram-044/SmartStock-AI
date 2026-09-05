import unittest
from backend.services.pos_service import (
    calculate_cart_preview,
    create_sale_invoice,
    process_customer_return
)
from backend.services.inventory_service import get_current_stock, InsufficientStockError

class TestPOSBilling(unittest.TestCase):
    def test_cart_preview_and_gst_split(self):
        """Tests GST (CGST/SGST) split and pricing calculation."""
        # Product 1: Ponni Boiled Rice 25kg (0% GST)
        # Product 11: Madhur Sugar 1kg (5% GST)
        items = [
            {"product_id": 1, "quantity": 1.0, "discount": 0.0},
            {"product_id": 11, "quantity": 2.0, "discount": 5.0}
        ]
        preview = calculate_cart_preview(items)
        self.assertIn("total_amount", preview)
        self.assertIn("gst_amount", preview)
        self.assertIn("cgst_amount", preview)
        self.assertIn("sgst_amount", preview)
        self.assertEqual(preview["cgst_amount"], preview["sgst_amount"])
        self.assertTrue(preview["total_amount"] > 0)

    def test_checkout_reduces_inventory(self):
        """Tests that a checkout reduces inventory atomically."""
        prod_id = 10 # Tata Salt 1kg
        init_stock = float(get_current_stock(prod_id)["current_stock"])
        self.assertTrue(init_stock >= 2.0)

        invoice = create_sale_invoice(
            data={
                "items": [{"product_id": prod_id, "quantity": 2.0, "discount": 0.0}],
                "payment_method": "UPI",
                "customer_name": "Test Customer"
            },
            user_id=1
        )
        self.assertIsNotNone(invoice)
        self.assertIn("INV-", invoice["invoice_number"])
        self.assertEqual(invoice["payment_method"], "UPI")

        new_stock = float(get_current_stock(prod_id)["current_stock"])
        self.assertEqual(new_stock, round(init_stock - 2.0, 3))

    def test_customer_return_restores_inventory(self):
        """Tests that a customer return increases stock."""
        prod_id = 10
        init_stock = float(get_current_stock(prod_id)["current_stock"])

        res = process_customer_return(
            data={
                "product_id": prod_id,
                "quantity": 1.0,
                "refund_amount": 28.0,
                "return_reason": "Customer bought extra by mistake",
                "customer_name": "Test Returner"
            },
            user_id=1
        )
        self.assertEqual(res["status"], "SUCCESS")
        new_stock = float(get_current_stock(prod_id)["current_stock"])
        self.assertEqual(new_stock, round(init_stock + 1.0, 3))

if __name__ == "__main__":
    unittest.main()
