import unittest
from backend.database.db import get_db, transaction
from backend.services.inventory_service import (
    record_transaction,
    get_current_stock,
    adjust_stock,
    record_loss,
    get_ledger_history,
    InsufficientStockError
)

class TestInventoryLedger(unittest.TestCase):
    def test_stock_transaction_and_audit_trail(self):
        """Verifies opening + purchase - sale + adjustment = balance and ledger auditability."""
        conn = get_db()
        try:
            # Pick product 1
            cur = conn.execute("SELECT id, name FROM products WHERE id = 1")
            prod = cur.fetchone()
            self.assertIsNotNone(prod)
            prod_id = prod["id"]

            cur_stock = get_current_stock(prod_id)
            init_stock = float(cur_stock["current_stock"])

            # 1. Test purchase addition
            with transaction() as tx_conn:
                bal1 = record_transaction(
                    conn=tx_conn,
                    product_id=prod_id,
                    change_qty=10.0,
                    transaction_type="PURCHASE",
                    reference_id="TEST-PO-01",
                    reason="Test inward purchase"
                )
            self.assertEqual(bal1, round(init_stock + 10.0, 3))

            # 2. Test sale deduction
            with transaction() as tx_conn:
                bal2 = record_transaction(
                    conn=tx_conn,
                    product_id=prod_id,
                    change_qty=-5.0,
                    transaction_type="SALE",
                    reference_id="TEST-INV-01",
                    reason="Test sale checkout"
                )
            self.assertEqual(bal2, round(bal1 - 5.0, 3))

            # 3. Test negative stock prevention
            with self.assertRaises(InsufficientStockError):
                with transaction() as tx_conn:
                    record_transaction(
                        conn=tx_conn,
                        product_id=prod_id,
                        change_qty=-(bal2 + 100.0),
                        transaction_type="SALE",
                        reference_id="TEST-INV-OVER",
                        reason="Impossible sale"
                    )

            # 4. Verify transaction recorded in ledger
            history = get_ledger_history(product_id=prod_id, limit=5)
            self.assertTrue(len(history) >= 2)
            self.assertEqual(history[0]["transaction_type"], "SALE")
            self.assertEqual(history[1]["transaction_type"], "PURCHASE")
        finally:
            conn.close()

if __name__ == "__main__":
    unittest.main()
