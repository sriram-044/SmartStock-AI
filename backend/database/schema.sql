-- ==============================================================================
-- Inventory Management AI: Relational Schema (SQLite3)
-- Comprehensive Schema supporting Indian Retail, GST, Audits, Transactions, & AI
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. USERS & ROLES
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'cashier')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. CATEGORIES
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    tamil_name TEXT,
    description TEXT
);

-- 3. PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE,
    name TEXT NOT NULL,
    tamil_name TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    subcategory TEXT,
    brand TEXT,
    unit TEXT NOT NULL DEFAULT 'Piece', -- Piece, Kg, Gram, Litre, Millilitre, Pack, Box, Bottle, Dozen
    pack_size TEXT,
    purchase_price REAL NOT NULL DEFAULT 0.0,
    selling_price REAL NOT NULL DEFAULT 0.0,
    mrp REAL NOT NULL DEFAULT 0.0,
    gst_rate REAL NOT NULL DEFAULT 5.0, -- 0, 5, 12, 18, 28
    min_stock INTEGER NOT NULL DEFAULT 10,
    max_stock INTEGER NOT NULL DEFAULT 100,
    reorder_level INTEGER NOT NULL DEFAULT 20,
    safety_stock INTEGER NOT NULL DEFAULT 10,
    preferred_supplier_id INTEGER,
    expiry_applicable INTEGER NOT NULL DEFAULT 0, -- 1 = Yes, 0 = No
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. SUPPLIERS
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    state TEXT DEFAULT 'Tamil Nadu',
    district TEXT DEFAULT 'Chennai',
    city TEXT,
    address TEXT,
    rating REAL DEFAULT 4.0,
    reliability_score REAL DEFAULT 95.0, -- Percentage 0-100
    avg_lead_time_days INTEGER DEFAULT 3,
    return_rate REAL DEFAULT 1.0, -- Defect/return percentage
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. SUPPLIER CATALOG & PRICING
CREATE TABLE IF NOT EXISTS supplier_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_price REAL NOT NULL,
    moq INTEGER NOT NULL DEFAULT 1, -- Minimum Order Quantity
    delivery_time_days INTEGER NOT NULL DEFAULT 3,
    UNIQUE(supplier_id, product_id)
);

-- 6. CURRENT INVENTORY
CREATE TABLE IF NOT EXISTS inventory (
    product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    current_stock REAL NOT NULL DEFAULT 0.0,
    reserved_stock REAL NOT NULL DEFAULT 0.0,
    last_audit_date DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. INVENTORY TRANSACTION LEDGER (Immutable)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    change_qty REAL NOT NULL, -- Positive for incoming, negative for outgoing
    balance_after REAL NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN (
        'OPENING', 'PURCHASE', 'SALE', 'CUSTOMER_RETURN', 
        'DAMAGE', 'EXPIRED', 'AUDIT_ADJUSTMENT'
    )),
    reference_id TEXT, -- Invoice #, PO #, Audit #
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. SALES INVOICES
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_name TEXT DEFAULT 'Walk-in Customer',
    customer_phone TEXT,
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    gst_amount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    payment_method TEXT NOT NULL DEFAULT 'CASH' CHECK(payment_method IN ('CASH', 'UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'CREDIT')),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 9. SALE LINE ITEMS
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    mrp REAL NOT NULL,
    gst_rate REAL NOT NULL,
    gst_amount REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0.0,
    total REAL NOT NULL
);

-- 10. PURCHASES & INWARD ORDERS
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'ORDERED' CHECK(status IN ('ORDERED', 'IN_TRANSIT', 'RECEIVED', 'CANCELLED')),
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expected_delivery DATETIME,
    actual_delivery DATETIME,
    subtotal REAL NOT NULL DEFAULT 0.0,
    gst_amount REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    invoice_number TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 11. PURCHASE LINE ITEMS
CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL,
    unit_cost REAL NOT NULL,
    gst_rate REAL NOT NULL,
    total_cost REAL NOT NULL
);

-- 12. CUSTOMER RETURNS
CREATE TABLE IF NOT EXISTS returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_number TEXT UNIQUE NOT NULL,
    sale_id INTEGER REFERENCES sales(id) ON DELETE SET NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL,
    refund_amount REAL NOT NULL,
    return_reason TEXT NOT NULL,
    customer_name TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 13. PRODUCT BATCHES (FEFO Expiry Tracking)
CREATE TABLE IF NOT EXISTS product_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    batch_number TEXT NOT NULL,
    mfg_date DATE,
    expiry_date DATE NOT NULL,
    quantity REAL NOT NULL,
    remaining_qty REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 14. PHYSICAL STOCK AUDITS
CREATE TABLE IF NOT EXISTS stock_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_number TEXT UNIQUE NOT NULL,
    audit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    conducted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'IN_PROGRESS' CHECK(status IN ('IN_PROGRESS', 'COMPLETED')),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 15. STOCK AUDIT ITEMS & DISCREPANCIES
CREATE TABLE IF NOT EXISTS stock_audit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL REFERENCES stock_audits(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    system_stock REAL NOT NULL,
    physical_stock REAL NOT NULL,
    variance_qty REAL NOT NULL,
    ai_likely_cause TEXT,
    action_taken TEXT
);

-- 16. AI RECOMMENDATIONS & DECISION GATEWAY
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    risk_level TEXT NOT NULL CHECK(risk_level IN ('SAFE', 'MONITOR', 'REORDER_SOON', 'REORDER_NOW', 'CRITICAL')),
    recommended_action TEXT NOT NULL,
    recommended_qty REAL NOT NULL,
    suggested_supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    rationale TEXT NOT NULL,
    transparent_formula_json TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'MODIFIED')),
    approved_qty REAL,
    user_decision_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    decision_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 17. AI FEEDBACK & OUTCOME EVALUATION LOG
CREATE TABLE IF NOT EXISTS ai_feedback_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id INTEGER REFERENCES ai_recommendations(id) ON DELETE SET NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    predicted_demand REAL NOT NULL,
    actual_sales_period REAL NOT NULL,
    forecast_error REAL NOT NULL,
    outcome_notes TEXT,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 18. NOTIFICATIONS & ALERTS
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK(level IN ('INFO', 'WARNING', 'CRITICAL')),
    title TEXT NOT NULL,
    tamil_title TEXT,
    message TEXT NOT NULL,
    tamil_message TEXT,
    link_url TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 19. FESTIVALS & SEASONAL EVENTS
CREATE TABLE IF NOT EXISTS festivals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tamil_name TEXT,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 3,
    affected_categories TEXT, -- JSON array of category names
    demand_multiplier REAL NOT NULL DEFAULT 1.5,
    notes TEXT
);

-- 20. SHOP SETTINGS
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL DEFAULT 'Sri Murugan Super Store',
    tamil_shop_name TEXT DEFAULT 'ஸ்ரீ முருகன் சூப்பர் ஸ்டோர்',
    gstin TEXT DEFAULT '33AAAAA0000A1Z5',
    state TEXT DEFAULT 'Tamil Nadu',
    district TEXT DEFAULT 'Chennai',
    city TEXT DEFAULT 'T. Nagar',
    address TEXT DEFAULT '124, Usman Road, T. Nagar, Chennai - 600017',
    phone TEXT DEFAULT '+91 98400 12345',
    currency TEXT DEFAULT 'INR',
    low_stock_threshold_percent REAL DEFAULT 20.0,
    default_lead_time_days INTEGER DEFAULT 4,
    ai_confidence_threshold REAL DEFAULT 85.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INDICES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_trans_product ON inventory_transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_trans_created ON inventory_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_batches_expiry ON product_batches(expiry_date);
CREATE INDEX IF NOT EXISTS idx_ai_recom_status ON ai_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_ai_recom_risk ON ai_recommendations(risk_level);

-- ==============================================================================
-- 21. AGENTIC AI TASK PERSISTENCE, EXECUTION TRACES & HUMAN-IN-THE-LOOP APPROVAL
-- ==============================================================================

CREATE TABLE IF NOT EXISTS agent_tasks (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'PLANNING', 'RUNNING', 'WAITING_FOR_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')),
    constraints_json TEXT,
    plan_json TEXT,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    result_summary TEXT,
    final_output_json TEXT,
    approval_status TEXT DEFAULT 'NOT_REQUIRED' CHECK(approval_status IN ('NOT_REQUIRED', 'PENDING', 'APPROVED', 'REJECTED')),
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE TABLE IF NOT EXISTS agent_task_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    tool_name TEXT,
    tool_input_json TEXT,
    tool_output_json TEXT,
    step_status TEXT NOT NULL CHECK(step_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED')),
    reflection TEXT,
    duration_ms INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_task_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    action_name TEXT NOT NULL,
    proposed_payload_json TEXT NOT NULL,
    justification TEXT,
    estimated_cost REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
    requested_by_agent TEXT NOT NULL,
    decided_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    decision_reason TEXT,
    decided_at DATETIME,
    execution_result_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES agent_tasks(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    agent_name TEXT,
    details_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_user ON agent_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_steps_task ON agent_task_steps(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_approvals_task ON agent_task_approvals(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_approvals_status ON agent_task_approvals(status);
CREATE INDEX IF NOT EXISTS idx_agent_audit_task ON agent_audit_logs(task_id);

-- ==============================================================================
-- 22. CONVERSATIONS & MULTI-TURN CHAT MEMORY
-- ==============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tamil_summary TEXT,
    provider TEXT,
    model TEXT,
    tool_name TEXT,
    tool_args_json TEXT,
    tool_result_json TEXT,
    execution_mode TEXT DEFAULT 'llm',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_execution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    tool_name TEXT NOT NULL,
    tool_args_json TEXT,
    execution_status TEXT NOT NULL CHECK(execution_status IN ('SUCCESS', 'FAILED')),
    sanitized_result_summary TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_session ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_history_session ON tool_execution_history(session_id);

