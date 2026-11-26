import sys
import os
import unittest
from app import app
from database import get_db

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_dashboard(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Periodic Assessment', resp.data)
        self.assertIn(b'Crescent Islamic High School', resp.data)
        print("✓ GET / (Dashboard) passed: 200 OK")

    def test_02_settings(self):
        resp = self.client.get('/settings')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Examination Settings', resp.data)

        # POST settings
        post_data = {
            'exam_title': 'Periodic Assessment – 2',
            'academic_year': '2026-27',
            'first_exam_date': '16/11/2026',
            'class_print_order': 'Section first',
            'date_1': '16/11/2026', 'day_1': 'Monday',
            'date_2': '17/11/2026', 'day_2': 'Tuesday',
            'date_3': '18/11/2026', 'day_3': 'Wednesday',
            'date_4': '19/11/2026', 'day_4': 'Thursday',
            'date_5': '20/11/2026', 'day_5': 'Friday',
            'date_6': '21/11/2026', 'day_6': 'Saturday',
            'date_7': '23/11/2026', 'day_7': 'Monday',
            'date_8': '24/11/2026', 'day_8': 'Tuesday',
        }
        resp = self.client.post('/settings', data=post_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Exam settings and attendance dates saved', resp.data)
        print("✓ GET & POST /settings passed: 200 OK")

    def test_03_students_crud(self):
        resp = self.client.get('/students')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Students Directory', resp.data)

        # Add temp student
        resp = self.client.post('/students/add', data={
            'adm_no': 'TEST9999',
            'name': 'Test Student Z',
            'class_name': '6A',
            'gender': 'M',
            'block': 'Boys Block'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'TEST9999', resp.data)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE adm_no = 'TEST9999'")
        st_row = c.fetchone()
        st_id = st_row[0]
        conn.close()

        # Edit temp student
        resp = self.client.post(f'/students/edit/{st_id}', data={
            'name': 'Test Student Z Edited',
            'class_name': '6A',
            'gender': 'F',
            'block': 'Girls Block',
            'roll_in_class': 99,
            'roll_in_group': 99
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Delete temp student
        resp = self.client.post(f'/students/delete/{st_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        print("✓ Students CRUD (/students, /students/add, /students/edit, /students/delete) passed")

    def test_04_rooms_crud(self):
        resp = self.client.get('/rooms')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Examination Rooms', resp.data)

        # Add temp room
        resp = self.client.post('/rooms/add', data={
            'name': 'TEST_ROOM_99',
            'block': 'Girls Block',
            'benches': 10,
            'floor': '1st Floor'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM rooms WHERE name = 'TEST_ROOM_99'")
        rm_row = c.fetchone()
        rm_id = rm_row[0]
        conn.close()

        # Edit temp room
        resp = self.client.post(f'/rooms/edit/{rm_id}', data={
            'name': 'TEST_ROOM_99_EDIT',
            'block': 'Boys Block',
            'benches': 12,
            'print_order': 99,
            'floor': '2nd Floor'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Delete temp room
        resp = self.client.post(f'/rooms/delete/{rm_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        print("✓ Rooms CRUD (/rooms, /rooms/add, /rooms/edit, /rooms/delete) passed")

    def test_05_arrangements_crud(self):
        resp = self.client.get('/arrangement')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Room Seating Arrangement Grid', resp.data)

        # Add temp arrangement block
        resp = self.client.post('/arrangement/add', data={
            'room_name': '6A',
            'row_side': 'L',
            'class_or_group': '6A',
            'from_roll': 90,
            'to_roll': 95
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM arrangements WHERE from_roll = 90 AND to_roll = 95")
        arr_row = c.fetchone()
        arr_id = arr_row[0]
        conn.close()

        # Edit temp arrangement block
        resp = self.client.post(f'/arrangement/edit/{arr_id}', data={
            'room_name': '6A',
            'row_side': 'R',
            'class_or_group': '6A',
            'from_roll': 91,
            'to_roll': 96
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Delete temp arrangement block
        resp = self.client.post(f'/arrangement/delete/{arr_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        print("✓ Arrangement CRUD (/arrangement, /arrangement/add, /arrangement/edit, /arrangement/delete) passed")

    def test_06_print_previews(self):
        for path in ['/preview/class-plan', '/preview/room-list', '/preview/attendance', '/preview/master-summary', '/preview/consolidated-sheet']:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"Failed on {path}")
            self.assertIn(b'Crescent Islamic High School', resp.data, f"Header missing in {path}")
            print(f"✓ Print Preview {path} passed: 200 OK")

    def test_07_downloads(self):
        endpoints = [
            ('/export/class-plan.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('/export/room-list.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('/export/attendance.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('/export/master-summary.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('/export/master-excel.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('/export/consolidated-sheet.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('/export/consolidated-sheet.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ]
        for path, mime in endpoints:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"Failed download {path}")
            self.assertGreater(len(resp.data), 1000, f"File too small for {path}")
            print(f"✓ Download {path} passed: 200 OK ({len(resp.data)} bytes)")

    def test_08_import_dynamic_report(self):
        from paths import get_uploads_dir
        dyn_path = os.path.join(get_uploads_dir(), 'Dynamic_Report.xlsx')
        if os.path.exists(dyn_path):
            with open(dyn_path, 'rb') as f:
                data = {
                    'excel_file': (f, 'Dynamic_Report.xlsx'),
                    'mode': 'replace'
                }
                resp = self.client.post('/students/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(b'Successfully processed 480 students', resp.data)
                print("✓ Upload /students/upload Dynamic_Report.xlsx passed: 480 students processed")

if __name__ == '__main__':
    unittest.main()
