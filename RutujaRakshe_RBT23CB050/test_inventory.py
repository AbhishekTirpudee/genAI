import sqlite3
import unittest

from db import build_database
from sql_tool import MAX_ROWS, run_readonly_query


class InventoryDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = build_database()

    def test_product_total_sums_all_warehouses(self):
        result = run_readonly_query(
            self.conn, "SELECT sku, total_quantity FROM product_stock WHERE sku = 'ELC-001'"
        )
        self.assertEqual(result["rows"], [["ELC-001", 17]])

    def test_low_stock_products(self):
        result = run_readonly_query(
            self.conn,
            "SELECT sku FROM product_stock WHERE total_quantity < reorder_level ORDER BY sku",
        )
        self.assertEqual(
            [row[0] for row in result["rows"]],
            ["ELC-001", "ELC-003", "ELC-004", "FUR-001", "FUR-002", "GRO-002", "STA-002"],
        )

    def test_out_of_stock_product_with_no_stock_rows(self):
        result = run_readonly_query(
            self.conn, "SELECT sku, total_quantity FROM product_stock WHERE total_quantity = 0"
        )
        self.assertEqual(result["rows"], [["FUR-002", 0]])


class ReadOnlySqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = build_database()

    def test_select_returns_columns_and_rows(self):
        result = run_readonly_query(self.conn, "SELECT sku, reorder_level FROM products WHERE sku = 'GRO-001';")
        self.assertEqual(
            result,
            {"columns": ["sku", "reorder_level"], "rows": [["GRO-001", 30]], "row_count": 1, "truncated": False},
        )

    def test_bad_sql_returns_error(self):
        result = run_readonly_query(self.conn, "SELECT * FROM missing_table")
        self.assertIn("error", result)

    def test_write_statements_are_rejected(self):
        blocked = [
            "DELETE FROM stock",
            "UPDATE products SET unit_price = 0",
            "DROP TABLE stock",
            "SELECT 1; DROP TABLE stock",
            "PRAGMA table_info(stock)",
            "WITH x AS (SELECT 1) DELETE FROM stock",
            "   ",
        ]
        for sql in blocked:
            with self.subTest(sql=sql):
                self.assertIn("error", run_readonly_query(self.conn, sql))

    def test_connection_itself_is_read_only(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.conn.execute("DELETE FROM stock")

    def test_large_result_is_truncated(self):
        sql = (
            "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM n WHERE x < 150) "
            "SELECT x FROM n"
        )
        result = run_readonly_query(self.conn, sql)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["row_count"], MAX_ROWS)


if __name__ == "__main__":
    unittest.main()
