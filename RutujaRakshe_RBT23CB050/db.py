import sqlite3

SCHEMA = """
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0)
);

CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL
);

CREATE TABLE stock (
    product_id INTEGER NOT NULL REFERENCES products(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (product_id, warehouse_id)
);

CREATE VIEW product_stock AS
SELECT p.id AS product_id,
       p.sku,
       p.name AS product_name,
       c.name AS category,
       p.unit_price,
       p.reorder_level,
       COALESCE(SUM(s.quantity), 0) AS total_quantity
FROM products p
JOIN categories c ON c.id = p.category_id
LEFT JOIN stock s ON s.product_id = p.id
GROUP BY p.id;
"""

CATEGORIES = ["Electronics", "Grocery", "Stationery", "Furniture"]

WAREHOUSES = [
    (1, "Central Warehouse", "Mumbai"),
    (2, "East Depot", "Kolkata"),
    (3, "South Store", "Chennai"),
]

# sku, name, category, unit_price, reorder_level
PRODUCTS = [
    ("ELC-001", "USB-C Charger 65W", "Electronics", 1499.0, 20),
    ("ELC-002", "Wireless Mouse", "Electronics", 699.0, 15),
    ("ELC-003", "Bluetooth Headphones", "Electronics", 2499.0, 10),
    ("ELC-004", "27-inch Monitor", "Electronics", 14999.0, 5),
    ("GRO-001", "Basmati Rice 5kg", "Grocery", 620.0, 30),
    ("GRO-002", "Olive Oil 1L", "Grocery", 850.0, 12),
    ("GRO-003", "Green Tea 100 bags", "Grocery", 310.0, 25),
    ("STA-001", "A4 Paper Ream", "Stationery", 280.0, 40),
    ("STA-002", "Gel Pen Pack (10)", "Stationery", 150.0, 30),
    ("STA-003", "Spiral Notebook", "Stationery", 60.0, 50),
    ("FUR-001", "Ergonomic Chair", "Furniture", 8999.0, 4),
    ("FUR-002", "Standing Desk", "Furniture", 18999.0, 3),
]

# sku -> {warehouse_id: quantity}; a product with no entries has zero stock
STOCK = {
    "ELC-001": {1: 12, 2: 5},
    "ELC-002": {1: 40, 3: 22},
    "ELC-003": {1: 6, 2: 3},
    "ELC-004": {1: 4},
    "GRO-001": {1: 80, 2: 45, 3: 30},
    "GRO-002": {2: 0, 3: 7},
    "GRO-003": {1: 25, 3: 10},
    "STA-001": {1: 60, 2: 0},
    "STA-002": {3: 18},
    "STA-003": {1: 200, 2: 75, 3: 0},
    "FUR-001": {1: 2},
    "FUR-002": {},
}


def build_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)

    conn.executemany("INSERT INTO categories (name) VALUES (?)", [(c,) for c in CATEGORIES])
    conn.executemany(
        "INSERT INTO warehouses (id, name, location) VALUES (?, ?, ?)", WAREHOUSES
    )

    category_ids = dict(conn.execute("SELECT name, id FROM categories").fetchall())
    product_ids = {}
    for sku, name, category, unit_price, reorder_level in PRODUCTS:
        cursor = conn.execute(
            "INSERT INTO products (sku, name, category_id, unit_price, reorder_level) "
            "VALUES (?, ?, ?, ?, ?)",
            (sku, name, category_ids[category], unit_price, reorder_level),
        )
        product_ids[sku] = cursor.lastrowid

    for sku, by_warehouse in STOCK.items():
        for warehouse_id, quantity in by_warehouse.items():
            conn.execute(
                "INSERT INTO stock (product_id, warehouse_id, quantity) VALUES (?, ?, ?)",
                (product_ids[sku], warehouse_id, quantity),
            )

    conn.commit()
    # Agent queries run against a read-only connection
    conn.execute("PRAGMA query_only = ON")
    return conn
