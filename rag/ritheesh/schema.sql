-- Hospilot SQLite Database Schema for RAG Service

CREATE TABLE IF NOT EXISTS beds (
    id TEXT PRIMARY KEY,
    branch_id TEXT,
    ward TEXT NOT NULL,
    bed_number TEXT NOT NULL,
    room_type TEXT,
    status TEXT NOT NULL, -- 'Available', 'Occupied', 'Reserved', 'Dirty'
    is_active INTEGER NOT NULL DEFAULT 1,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ventilation TEXT,
    room_sharing TEXT,
    floor INTEGER,
    wing TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    capacity INTEGER,
    target_occupancy_pct INTEGER
);

CREATE TABLE IF NOT EXISTS ipd_admissions (
    id TEXT PRIMARY KEY,
    patient_token TEXT,
    bed_id TEXT REFERENCES beds(id),
    department_id TEXT REFERENCES departments(id),
    admitted_at DATETIME,
    expected_discharge_at DATETIME,
    status TEXT NOT NULL, -- 'admitted', 'discharged', 'transfer_pending'
    discharge_ready INTEGER DEFAULT 0,
    transfer_pending INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    uhid TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS lab_orders (
    id TEXT PRIMARY KEY,
    visit_id TEXT,
    patient_token TEXT,
    ordered_by TEXT,
    status TEXT, -- 'pending', 'completed', 'in_progress'
    priority TEXT, -- 'routine', 'urgent', 'stat'
    ordered_at DATETIME,
    completed_at DATETIME
);

CREATE TABLE IF NOT EXISTS lab_results (
    id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES lab_orders(id),
    patient_token TEXT,
    test_name TEXT,
    test_code TEXT,
    result_value TEXT,
    flag TEXT,
    reference_range TEXT,
    unit TEXT,
    reported_at DATETIME
);

CREATE TABLE IF NOT EXISTS staff_roster (
    id TEXT PRIMARY KEY,
    area TEXT,
    area_label TEXT,
    role TEXT,
    shift TEXT,
    headcount INTEGER DEFAULT 0,
    assigned_load INTEGER DEFAULT 0,
    load_per_staff INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS vitals (
    id TEXT PRIMARY KEY,
    patient_token TEXT,
    admission_id TEXT REFERENCES ipd_admissions(id),
    recorded_at DATETIME NOT NULL,
    temperature REAL,
    pulse INTEGER,
    bp_systolic INTEGER,
    bp_diastolic INTEGER,
    spo2 INTEGER,
    respiratory_rate INTEGER,
    is_critical INTEGER DEFAULT 0
);
