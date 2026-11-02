"""
Database seeder for College Result Analysis System.
Generates realistic departments, subjects, faculty, students, and marks data.
"""

import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'college_results.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

# Set random seed for reproducible realistic data
random.seed(42)

DEPARTMENTS = [
    ('CSE', 'Computer Science & Engineering', 'Dr. Neerajkumar Sathawane'),
    ('IT', 'Information Technology', 'Dr. Anita Shinde'),
    ('ECE', 'Electronics & Communication Engineering', 'Dr. Rajesh Kulkarni'),
    ('MECH', 'Mechanical Engineering', 'Dr. Sanjay Deshmukh')
]

FACULTY = [
    ('Dr. Neerajkumar Sathawane', 'Professor & HOD', 'n.sathawane@college.edu', 'CSE'),
    ('Prof. Smita Patil', 'Associate Professor', 's.patil@college.edu', 'CSE'),
    ('Prof. Anand Joshi', 'Assistant Professor', 'a.joshi@college.edu', 'CSE'),
    ('Prof. Sunita Rao', 'Associate Professor', 's.rao@college.edu', 'CSE'),
    ('Prof. Deven Kulkarni', 'Assistant Professor', 'd.kulkarni@college.edu', 'CSE'),
    ('Dr. Anita Shinde', 'Professor & HOD', 'a.shinde@college.edu', 'IT'),
    ('Prof. Manoj Nair', 'Associate Professor', 'm.nair@college.edu', 'IT'),
    ('Prof. Rekha Sharma', 'Assistant Professor', 'r.sharma@college.edu', 'IT'),
    ('Dr. Rajesh Kulkarni', 'Professor & HOD', 'r.kulkarni@college.edu', 'ECE'),
    ('Prof. Vijay Chavan', 'Associate Professor', 'v.chavan@college.edu', 'ECE'),
    ('Dr. Sanjay Deshmukh', 'Professor & HOD', 's.deshmukh@college.edu', 'MECH'),
    ('Prof. Amit Gaikwad', 'Associate Professor', 'a.gaikwad@college.edu', 'MECH')
]

SUBJECTS = [
    # CSE Sem 4
    ('CS401', 'Database Management Systems', 'CSE', 4, 4, 30, 70, 100, 40, 0),
    ('CS402', 'Design & Analysis of Algorithms', 'CSE', 4, 4, 30, 70, 100, 40, 0),
    ('CS403', 'Operating Systems', 'CSE', 4, 3, 30, 70, 100, 40, 0),
    ('CS404', 'Computer Networks', 'CSE', 4, 3, 30, 70, 100, 40, 0),
    ('CS405', 'Software Engineering', 'CSE', 4, 3, 30, 70, 100, 40, 0),
    # CSE Sem 3
    ('CS301', 'Data Structures & Applications', 'CSE', 3, 4, 30, 70, 100, 40, 0),
    ('CS302', 'Discrete Mathematics', 'CSE', 3, 4, 30, 70, 100, 40, 0),
    ('CS303', 'Digital Electronics', 'CSE', 3, 3, 30, 70, 100, 40, 0),
    # IT Sem 4
    ('IT401', 'Web Technologies & Frameworks', 'IT', 4, 4, 30, 70, 100, 40, 0),
    ('IT402', 'Database Systems & Applications', 'IT', 4, 4, 30, 70, 100, 40, 0),
    ('IT403', 'Information & Cyber Security', 'IT', 4, 3, 30, 70, 100, 40, 0),
    ('IT404', 'Cloud Computing Architecture', 'IT', 4, 3, 30, 70, 100, 40, 0),
    # ECE Sem 4
    ('EC401', 'Signals and Digital Systems', 'ECE', 4, 4, 30, 70, 100, 40, 0),
    ('EC402', 'Microprocessors & Microcontrollers', 'ECE', 4, 4, 30, 70, 100, 40, 0),
    ('EC403', 'Analog & Digital Communication', 'ECE', 4, 3, 30, 70, 100, 40, 0),
    # MECH Sem 4
    ('ME401', 'Applied Thermodynamics', 'MECH', 4, 4, 30, 70, 100, 40, 0),
    ('ME402', 'Fluid Mechanics & Machinery', 'MECH', 4, 4, 30, 70, 100, 40, 0),
    ('ME403', 'Manufacturing Processes & Materials', 'MECH', 4, 3, 30, 70, 100, 40, 0),
]

FIRST_NAMES_MALE = [
    'Aarav', 'Rohan', 'Aditya', 'Vikram', 'Rahul', 'Devesh', 'Shubham', 'Tejas',
    'Arjun', 'Kabir', 'Pranav', 'Siddharth', 'Nikhil', 'Harsh', 'Varun', 'Kunal',
    'Akash', 'Ayush', 'Gaurav', 'Manish', 'Karthik', 'Abhishek', 'Omkar', 'Tanmay'
]

FIRST_NAMES_FEMALE = [
    'Priya', 'Ananya', 'Sneha', 'Kavya', 'Pooja', 'Manali', 'Divya', 'Neha',
    'Isha', 'Ritu', 'Tanvi', 'Anushka', 'Shreya', 'Meera', 'Riya', 'Aditi',
    'Simran', 'Pallavi', 'Sanjana', 'Shruti', 'Bhavna', 'Komal', 'Deepika', 'Sakshi'
]

LAST_NAMES = [
    'Sharma', 'Patel', 'Mehta', 'Verma', 'Singh', 'Reddy', 'Iyer', 'Nair',
    'Joshi', 'Kulkarni', 'Deshmukh', 'Patil', 'Chavan', 'Gaikwad', 'Shinde',
    'Meshram', 'Kokate', 'Ghule', 'Bose', 'Gupta', 'Bhat', 'Rao', 'Pandey', 'Mishra'
]

def calculate_grade(total_marks):
    if total_marks >= 90:
        return 'O', 10, 1
    elif total_marks >= 80:
        return 'A+', 9, 1
    elif total_marks >= 70:
        return 'A', 8, 1
    elif total_marks >= 60:
        return 'B+', 7, 1
    elif total_marks >= 50:
        return 'B', 6, 1
    elif total_marks >= 40:
        return 'C', 5, 1
    else:
        return 'F', 0, 0

def init_and_seed_database():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Execute Schema
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    # 2. Insert Departments
    dept_map = {}
    for code, name, hod in DEPARTMENTS:
        cursor.execute("INSERT INTO departments (dept_code, dept_name, hod_name) VALUES (?, ?, ?)", (code, name, hod))
        dept_map[code] = cursor.lastrowid

    # 3. Insert Faculty
    fac_map = {}
    for name, desig, email, dept_code in FACULTY:
        cursor.execute("INSERT INTO faculty (name, designation, email, dept_id) VALUES (?, ?, ?, ?)",
                       (name, desig, email, dept_map[dept_code]))
        fac_map[name] = cursor.lastrowid

    # 4. Insert Subjects
    sub_map = {}
    for sub in SUBJECTS:
        code, name, d_code, sem, cred, m_int, m_ext, m_tot, p_mark, is_prac = sub
        cursor.execute("""
            INSERT INTO subjects (subject_code, subject_name, dept_id, semester, credits, max_internal, max_external, max_marks, pass_marks, is_practical)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, name, dept_map[d_code], sem, cred, m_int, m_ext, m_tot, p_mark, is_prac))
        sub_map[code] = cursor.lastrowid

    # Map faculty to subjects
    faculty_subj_pair = [
        ('CS401', 'Dr. Neerajkumar Sathawane'),
        ('CS402', 'Prof. Smita Patil'),
        ('CS403', 'Prof. Anand Joshi'),
        ('CS404', 'Prof. Sunita Rao'),
        ('CS405', 'Prof. Deven Kulkarni'),
        ('CS301', 'Prof. Smita Patil'),
        ('CS302', 'Prof. Anand Joshi'),
        ('CS303', 'Prof. Deven Kulkarni'),
        ('IT401', 'Dr. Anita Shinde'),
        ('IT402', 'Prof. Manoj Nair'),
        ('IT403', 'Prof. Rekha Sharma'),
        ('IT404', 'Prof. Manoj Nair'),
        ('EC401', 'Dr. Rajesh Kulkarni'),
        ('EC402', 'Prof. Vijay Chavan'),
        ('EC403', 'Dr. Rajesh Kulkarni'),
        ('ME401', 'Dr. Sanjay Deshmukh'),
        ('ME402', 'Prof. Amit Gaikwad'),
        ('ME403', 'Dr. Sanjay Deshmukh'),
    ]
    for sub_code, fac_name in faculty_subj_pair:
        if sub_code in sub_map and fac_name in fac_map:
            cursor.execute("INSERT INTO subject_faculty (subject_id, faculty_id) VALUES (?, ?)",
                           (sub_map[sub_code], fac_map[fac_name]))

    # 5. Generate Students & Marks
    dept_configs = [
        ('CSE', 4, 38, 'CS24'),
        ('CSE', 3, 20, 'CS23'),
        ('IT', 4, 30, 'IT24'),
        ('ECE', 4, 25, 'EC24'),
        ('MECH', 4, 22, 'ME24'),
    ]

    used_names = set()
    total_students_created = 0
    total_marks_created = 0

    for dept_code, sem, count, roll_prefix in dept_configs:
        # Determine subjects for this department and semester
        cursor.execute("SELECT subject_id, subject_code, subject_name FROM subjects WHERE dept_id = ? AND semester = ?",
                       (dept_map[dept_code], sem))
        dept_sem_subjects = cursor.fetchall()

        for i in range(1, count + 1):
            gender = 'Male' if random.random() < 0.52 else 'Female'
            first_pool = FIRST_NAMES_MALE if gender == 'Male' else FIRST_NAMES_FEMALE
            
            # Ensure unique name
            while True:
                fname = random.choice(first_pool)
                lname = random.choice(LAST_NAMES)
                fullname = f"{fname} {lname}"
                if fullname not in used_names:
                    used_names.add(fullname)
                    break

            year_code = '22' if sem == 4 else '23'
            roll_no = f"{roll_prefix}-{i:03d}"
            usn = f"1RS{year_code}{dept_code}{i:03d}"
            section = 'A' if i <= count // 2 else 'B'
            email = f"{fname.lower()}.{lname.lower()}{i}@college.edu"
            batch_year = '2022-2026' if sem >= 3 else '2023-2027'

            cursor.execute("""
                INSERT INTO students (roll_no, usn, name, gender, email, dept_id, semester, section, batch_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (roll_no, usn, fullname, gender, email, dept_map[dept_code], sem, section, batch_year))
            student_id = cursor.lastrowid
            total_students_created += 1

            # Give student a performance archetype to model realistic student variability:
            # 1. Star Topper (top 10%): avg 85-98 marks
            # 2. Consistent First Class (top 40%): avg 68-84 marks
            # 3. Average Performer (35%): avg 50-67 marks
            # 4. Struggling / Borderline (15%): avg 30-48 marks (with 1-2 backlogs)
            archetype_val = random.random()
            if archetype_val < 0.12:
                base_ability = random.uniform(85, 96)
            elif archetype_val < 0.55:
                base_ability = random.uniform(68, 84)
            elif archetype_val < 0.85:
                base_ability = random.uniform(50, 67)
            else:
                base_ability = random.uniform(32, 48)

            # Insert marks for each subject
            for sub_id, sub_code, sub_title in dept_sem_subjects:
                # Subject difficulty adjustment
                # E.g. Algorithms (CS402) and Signals (EC401) are harder; Web Tech (IT401) and SE (CS405) easier
                diff_penalty = 0
                if sub_code in ['CS402', 'EC401', 'ME401']:
                    diff_penalty = random.uniform(4, 9)
                elif sub_code in ['CS405', 'IT401']:
                    diff_penalty = -random.uniform(2, 5)

                subj_score = base_ability - diff_penalty + random.gauss(0, 4.5)
                # Cap between 20 and 100
                subj_score = max(22.0, min(99.5, subj_score))
                
                # Split into internal (out of 30) and external (out of 70)
                internal_ratio = 0.3
                internal_marks = round((subj_score * internal_ratio) + random.uniform(-1.5, 1.5), 1)
                internal_marks = max(8.0, min(30.0, internal_marks))
                
                external_marks = round(subj_score - internal_marks, 1)
                external_marks = max(10.0, min(70.0, external_marks))
                
                total_marks = round(internal_marks + external_marks, 1)
                grade, grade_point, is_passed = calculate_grade(total_marks)

                cursor.execute("""
                    INSERT INTO marks (student_id, subject_id, exam_term, internal_marks, external_marks, total_marks, grade, grade_point, is_passed)
                    VALUES (?, ?, 'End-Sem May 2024', ?, ?, ?, ?, ?, ?)
                """, (student_id, sub_id, internal_marks, external_marks, total_marks, grade, grade_point, is_passed))
                total_marks_created += 1

    conn.commit()
    conn.close()
    print(f"Database successfully seeded! Created {total_students_created} students and {total_marks_created} mark records.")

if __name__ == '__main__':
    init_and_seed_database()
