import sqlite3
import uuid
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "hospilot.db")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Read and execute schema
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # 1. Departments
    depts = [
        ("dept-1", "ICU", "Critical Care", 30, 85),
        ("dept-2", "General Ward", "Inpatient", 19, 75),
        ("dept-3", "Semi-Private Ward", "Inpatient", 6, 70),
        ("dept-4", "Private Ward", "Inpatient", 8, 70),
        ("dept-5", "Emergency", "Emergency", 13, 80),
        ("dept-6", "Cardiology", "Specialty", 8, 75),
        ("dept-7", "Orthopedics", "Specialty", 8, 75),
        ("dept-8", "Pediatrics", "Specialty", 8, 75)
    ]
    cursor.executemany("INSERT INTO departments VALUES (?,?,?,?,?)", depts)

    # 2. Beds Data (matching typical hospital distribution and assessment examples)
    # ICU: 30 beds total (6 Available, 17 Occupied, 3 Reserved, 4 Dirty) -> 6 Available right now
    beds = []
    
    # ICU Beds
    for i in range(1, 7):
        beds.append((f"bed-icu-{i}", "branch-1", "ICU", f"ICU-{100+i}", "ICU Bed", "Available", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "East"))
    for i in range(7, 24):
        beds.append((f"bed-icu-{i}", "branch-1", "ICU", f"ICU-{100+i}", "ICU Bed", "Occupied", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "East"))
    for i in range(24, 27):
        beds.append((f"bed-icu-{i}", "branch-1", "ICU", f"ICU-{100+i}", "ICU Bed", "Reserved", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "East"))
    for i in range(27, 31):
        beds.append((f"bed-icu-{i}", "branch-1", "ICU", f"ICU-{100+i}", "ICU Bed", "Dirty", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "East"))

    # General Ward: 19 beds total (4 Available, 6 Occupied, 9 Reserved) -> 31.6% occupancy
    for i in range(1, 5):
        beds.append((f"bed-gw-{i}", "branch-1", "General Ward", f"GW-{200+i}", "General", "Available", 1, "2026-08-13 08:00:00", "No", "Shared", 2, "North"))
    for i in range(5, 11):
        beds.append((f"bed-gw-{i}", "branch-1", "General Ward", f"GW-{200+i}", "General", "Occupied", 1, "2026-08-13 08:00:00", "No", "Shared", 2, "North"))
    for i in range(11, 20):
        beds.append((f"bed-gw-{i}", "branch-1", "General Ward", f"GW-{200+i}", "General", "Reserved", 1, "2026-08-13 08:00:00", "No", "Shared", 2, "North"))

    # Semi-Private: 6 beds total (1 Available, 3 Occupied, 2 Reserved) -> 50.0% occupancy
    for i in range(1, 2):
        beds.append((f"bed-sp-{i}", "branch-1", "Semi-Private Ward", f"SP-{300+i}", "Semi-Private", "Available", 1, "2026-08-13 08:00:00", "No", "Twin", 3, "West"))
    for i in range(2, 5):
        beds.append((f"bed-sp-{i}", "branch-1", "Semi-Private Ward", f"SP-{300+i}", "Semi-Private", "Occupied", 1, "2026-08-13 08:00:00", "No", "Twin", 3, "West"))
    for i in range(5, 7):
        beds.append((f"bed-sp-{i}", "branch-1", "Semi-Private Ward", f"SP-{300+i}", "Semi-Private", "Reserved", 1, "2026-08-13 08:00:00", "No", "Twin", 3, "West"))

    # Private Ward: 8 beds total (2 Available, 2 Occupied, 4 Reserved) -> 25.0% occupancy
    for i in range(1, 3):
        beds.append((f"bed-pv-{i}", "branch-1", "Private Ward", f"PV-{400+i}", "Private", "Available", 1, "2026-08-13 08:00:00", "No", "Single", 4, "South"))
    for i in range(3, 5):
        beds.append((f"bed-pv-{i}", "branch-1", "Private Ward", f"PV-{400+i}", "Private", "Occupied", 1, "2026-08-13 08:00:00", "No", "Single", 4, "South"))
    for i in range(5, 9):
        beds.append((f"bed-pv-{i}", "branch-1", "Private Ward", f"PV-{400+i}", "Private", "Reserved", 1, "2026-08-13 08:00:00", "No", "Single", 4, "South"))

    # Emergency: 13 beds total (4 Available, 3 Occupied, 6 Reserved)
    for i in range(1, 5):
        beds.append((f"bed-er-{i}", "branch-1", "Emergency", f"ER-{500+i}", "Emergency", "Available", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "North"))
    for i in range(5, 8):
        beds.append((f"bed-er-{i}", "branch-1", "Emergency", f"ER-{500+i}", "Emergency", "Occupied", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "North"))
    for i in range(8, 14):
        beds.append((f"bed-er-{i}", "branch-1", "Emergency", f"ER-{500+i}", "Emergency", "Reserved", 1, "2026-08-13 08:00:00", "Yes", "Single", 1, "North"))

    # Cardiology: 8 beds (2 Available, 2 Occupied, 4 Reserved)
    for i in range(1, 3): beds.append((f"bed-card-{i}", "branch-1", "Cardiology", f"CARD-{600+i}", "Specialty", "Available", 1, "2026-08-13 08:00:00", "No", "Single", 2, "East"))
    for i in range(3, 5): beds.append((f"bed-card-{i}", "branch-1", "Cardiology", f"CARD-{600+i}", "Specialty", "Occupied", 1, "2026-08-13 08:00:00", "No", "Single", 2, "East"))
    for i in range(5, 9): beds.append((f"bed-card-{i}", "branch-1", "Cardiology", f"CARD-{600+i}", "Specialty", "Reserved", 1, "2026-08-13 08:00:00", "No", "Single", 2, "East"))

    # Orthopedics: 8 beds (1 Available, 1 Occupied, 6 Reserved)
    for i in range(1, 2): beds.append((f"bed-ortho-{i}", "branch-1", "Orthopedics", f"ORTHO-{700+i}", "Specialty", "Available", 1, "2026-08-13 08:00:00", "No", "Shared", 3, "West"))
    for i in range(2, 3): beds.append((f"bed-ortho-{i}", "branch-1", "Orthopedics", f"ORTHO-{700+i}", "Specialty", "Occupied", 1, "2026-08-13 08:00:00", "No", "Shared", 3, "West"))
    for i in range(3, 9): beds.append((f"bed-ortho-{i}", "branch-1", "Orthopedics", f"ORTHO-{700+i}", "Specialty", "Reserved", 1, "2026-08-13 08:00:00", "No", "Shared", 3, "West"))

    # Pediatrics: 8 beds (2 Available, 2 Occupied, 4 Reserved)
    for i in range(1, 3): beds.append((f"bed-peds-{i}", "branch-1", "Pediatrics", f"PEDS-{800+i}", "Specialty", "Available", 1, "2026-08-13 08:00:00", "No", "Shared", 4, "South"))
    for i in range(3, 5): beds.append((f"bed-peds-{i}", "branch-1", "Pediatrics", f"PEDS-{800+i}", "Specialty", "Occupied", 1, "2026-08-13 08:00:00", "No", "Shared", 4, "South"))
    for i in range(5, 9): beds.append((f"bed-peds-{i}", "branch-1", "Pediatrics", f"PEDS-{800+i}", "Specialty", "Reserved", 1, "2026-08-13 08:00:00", "No", "Shared", 4, "South"))

    cursor.executemany("INSERT INTO beds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", beds)

    # 3. IPD Admissions (Active admissions mapped to occupied beds)
    admissions = []
    adm_count = 1
    for b in beds:
        bed_id, branch, ward, bnum, rtype, status, is_act, sync, vent, rshare, flr, wing = b
        if status == 'Occupied':
            admissions.append((
                f"adm-{adm_count}",
                f"TOKEN-{10000+adm_count}",
                bed_id,
                "dept-1" if "ICU" in ward else "dept-2",
                "2026-08-12 10:00:00",
                "2026-08-15 12:00:00",
                "admitted",
                0,
                0
            ))
            adm_count += 1
    cursor.executemany("INSERT INTO ipd_admissions VALUES (?,?,?,?,?,?,?,?,?)", admissions)

    # 4. Staff Roster (for staffing questions)
    roster = [
        ("rost-1", "ICU", "Intensive Care Unit", "Nurse", "Night", 8, 12, 1),
        ("rost-2", "ICU", "Intensive Care Unit", "Doctor", "Night", 2, 4, 1),
        ("rost-3", "General Ward", "General Ward", "Nurse", "Night", 5, 10, 1),
        ("rost-4", "Emergency", "Emergency Room", "Nurse", "Night", 4, 9, 1),
        ("rost-5", "Operating Theatre", "OT", "Surgeon", "Night", 3, 3, 1),
    ]
    cursor.executemany("INSERT INTO staff_roster VALUES (?,?,?,?,?,?,?,?)", roster)

    # 5. Vitals (Sample critical and non-critical vitals)
    vitals_data = [
        ("vit-1", "TOKEN-10001", "adm-1", "2026-08-13 09:00:00", 38.5, 110, 145, 92, 94, 22, 1),
        ("vit-2", "TOKEN-10002", "adm-2", "2026-08-13 09:15:00", 36.8, 72, 120, 80, 99, 16, 0),
        ("vit-3", "TOKEN-10003", "adm-3", "2026-08-13 09:30:00", 37.1, 78, 125, 82, 98, 18, 0)
    ]
    cursor.executemany("INSERT INTO vitals VALUES (?,?,?,?,?,?,?,?,?,?,?)", vitals_data)

    conn.commit()
    conn.close()
    print(f"Database initialized and seeded successfully at {DB_FILE}")

if __name__ == "__main__":
    init_db()
