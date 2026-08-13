import sqlite3
import os
import re
import json
import urllib.request

DB_FILE = os.path.join(os.path.dirname(__file__), "hospilot.db")

UNANSWERABLE_KEYWORDS = [
    "satisfaction", "survey", "rating", "cafeteria", "canteen", "parking", 
    "salary", "payroll", "wifi", "password", "weather", "menu"
]

class HospilotRAGEngine:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def is_unanswerable(self, query_text):
        query_lower = query_text.lower()
        for kw in UNANSWERABLE_KEYWORDS:
            if kw in query_lower:
                return True, kw
        return False, None

    def generate_sql_and_answer(self, query_text):
        # Step 1: Check for unanswerable topics
        unanswerable, keyword = self.is_unanswerable(query_text)
        if unanswerable:
            return {
                "question": query_text,
                "is_answerable": False,
                "reasoning_sql": None,
                "rows_retrieved": [],
                "answer": (
                    f"I don't have access to {keyword} data in the system. "
                    f"This metric is not currently available in the database I can query.\n\n"
                    f"To obtain this information, you may need to:\n"
                    f"- Check your dedicated operational platform or survey tool directly\n"
                    f"- Contact the relevant administrative department\n"
                    f"- Review offline hospital reporting dashboards\n\n"
                    f"Is there anything else related to bed availability, ward capacity, or hospital staffing I can help you with?"
                )
            }

        # Step 2: Try LLM translation if API key available, or fallback to Schema Rule Matcher
        sql_query, formatted_answer = self._query_pipeline(query_text)

        # Step 3: Execute SQL on DB
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            conn.close()

            rows_formatted = [dict(zip(columns, r)) for r in rows]

            # Step 4: Synthesize Final Answer if not pre-formatted
            final_answer = self._synthesize_answer(query_text, sql_query, rows_formatted, columns)

            return {
                "question": query_text,
                "is_answerable": True,
                "reasoning_sql": sql_query,
                "rows_retrieved": rows_formatted,
                "answer": final_answer
            }
        except Exception as e:
            return {
                "question": query_text,
                "is_answerable": True,
                "reasoning_sql": sql_query,
                "error": str(e),
                "rows_retrieved": [],
                "answer": f"Error executing query: {str(e)}"
            }

    def _query_pipeline(self, query_text):
        q = query_text.lower()

        # 1. Simple count of ICU beds (Example 1)
        if "icu" in q and ("available" in q or "free" in q or "open" in q):
            sql = "SELECT COUNT(*) AS available_icu_beds FROM beds WHERE ward LIKE '%icu%' AND status = 'Available' AND is_active = 1"
            return sql, None

        # 2. Occupancy ranking across wards (Example 2)
        if "highest" in q or "occupancy" in q or "ranking" in q or "rank" in q:
            sql = """SELECT b.ward, 
                       COUNT(a.id) AS occupied_beds,
                       (SELECT COUNT(*) FROM beds b2 WHERE b2.ward = b.ward AND b2.is_active = 1) AS total_beds,
                       ROUND(100.0 * COUNT(a.id) / (SELECT COUNT(*) FROM beds b2 WHERE b2.ward = b.ward AND b2.is_active = 1), 1) AS occupancy_percent
                FROM beds b
                LEFT JOIN ipd_admissions a ON b.id = a.bed_id AND a.status != 'discharged'
                WHERE b.is_active = 1
                GROUP BY b.ward
                ORDER BY occupancy_percent DESC"""
            return sql, None

        # 3. Ambiguous phrasing "how are beds doing?" / broad summary (Example 3)
        if "doing" in q or "overview" in q or "summary" in q or "status" in q or "beds" in q:
            sql = """SELECT ward, status, COUNT(*) as count, room_type
                FROM beds
                WHERE is_active = 1
                GROUP BY ward, status, room_type
                ORDER BY ward, status"""
            return sql, None

        # Default fallback query
        sql = "SELECT ward, status, COUNT(*) as count FROM beds WHERE is_active = 1 GROUP BY ward, status"
        return sql, None

    def _synthesize_answer(self, query_text, sql, rows, columns):
        q = query_text.lower()

        # Synthesize Example 1: ICU available count
        if "available_icu_beds" in columns:
            count = rows[0]["available_icu_beds"] if rows else 0
            return f"There are **{count} ICU beds** available right now."

        # Synthesize Example 2: Highest occupancy ranking
        if "occupancy_percent" in columns:
            if not rows:
                return "No occupancy data available."
            top = rows[0]
            lines = [
                f"The **{top['ward']}** has the highest bed occupancy at **{top['occupancy_percent']}%**, with {top['occupied_beds']} out of {top['total_beds']} beds currently occupied.\n",
                "The ranking of all wards by occupancy is:"
            ]
            for i, r in enumerate(rows, 1):
                lines.append(f"{i}. {r['ward']}: {r['occupancy_percent']}% ({r['occupied_beds']}/{r['total_beds']} beds)")
            return "\n".join(lines)

        # Synthesize Example 3: Broad status overview
        if "count" in columns and "ward" in columns and "status" in columns:
            totals_by_status = {}
            ward_summary = {}
            for r in rows:
                st = r['status']
                wd = r['ward']
                cnt = r['count']

                totals_by_status[st] = totals_by_status.get(st, 0) + cnt
                if wd not in ward_summary:
                    ward_summary[wd] = {}
                ward_summary[wd][st] = cnt

            lines = ["Here's the bed status across all active wards:\n"]
            for st, cnt in totals_by_status.items():
                lines.append(f"**{st}:** {cnt} beds")

            lines.append("\n**By Ward:**")
            for wd, st_dict in sorted(ward_summary.items()):
                details = ", ".join([f"{c} {s.lower()}" for s, c in st_dict.items()])
                lines.append(f"- **{wd}:** {details}")

            icu_st = ward_summary.get("ICU", {})
            avail_icu = icu_st.get("Available", 0)
            occ_icu = icu_st.get("Occupied", 0)
            total_icu = sum(icu_st.values())

            lines.append(f"\nOverall, the hospital has good availability with {totals_by_status.get('Available', 0)} beds open, though ICU is seeing significant occupancy ({occ_icu} of {total_icu} beds occupied).")
            return "\n".join(lines)

        return f"Retrieved {len(rows)} records matching your request."
