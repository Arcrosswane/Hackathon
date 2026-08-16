# Centralized Navigation Configuration for StratLearn (Matching Modern Expandable Grouped Sidebar)

ADMIN_NAV = [
    {
        'label': 'Dashboard',
        'endpoint': 'admin.dashboard',
        'icon': 'home',
        'subitems': []
    },
    {
        'label': 'General Settings',
        'icon': 'cog',
        'subitems': [
            {'label': 'School Profile', 'endpoint': 'settings.school_profile'},
            {'label': 'School Setup', 'endpoint': 'school.setup'}
        ]
    },
    {
        'label': 'Classes',
        'icon': 'academic-cap',
        'subitems': [
            {'label': 'All Classes', 'endpoint': 'classes.index'}
        ]
    },
    {
        'label': 'Subjects',
        'icon': 'book-open',
        'subitems': [
            {'label': 'Subjects Catalog', 'endpoint': 'subjects.index'},
            {'label': 'Subject Assignments', 'endpoint': 'subjects.assignments'}
        ]
    },
    {
        'label': 'Students',
        'icon': 'user',
        'subitems': [
            {'label': 'All Students', 'endpoint': 'students.index'},
            {'label': 'Parents & Guardians', 'endpoint': 'guardians.index'}
        ]
    },
    {
        'label': 'Employees',
        'icon': 'briefcase',
        'subitems': [
            {'label': 'All Employees', 'endpoint': 'employees.index'}
        ]
    },
    {
        'label': 'Timetable',
        'icon': 'calendar',
        'subitems': [
            {'label': 'Class Timetables', 'endpoint': 'timetables.index'},
            {'label': 'Period Settings', 'endpoint': 'timetables.period_settings'}
        ]
    },
    {
        'label': 'Homework',
        'icon': 'document-text',
        'subitems': [
            {'label': 'All Homework Tasks', 'endpoint': 'homework.manage'},
            {'label': 'Create Homework', 'endpoint': 'homework.create'}
        ]
    },
    {
        'label': 'Behaviour & Skills',
        'icon': 'sparkles',
        'subitems': [
            {'label': 'Behaviour Observations', 'endpoint': 'behaviour_skills.behaviour_index'},
            {'label': 'Record Observation', 'endpoint': 'behaviour_skills.create_behaviour'},
            {'label': 'Skill Assessments', 'endpoint': 'behaviour_skills.assessments_index'},
            {'label': 'Bulk Skill Rating', 'endpoint': 'behaviour_skills.bulk_assessments'},
            {'label': 'Behaviour Categories', 'endpoint': 'behaviour_skills.manage_categories'},
            {'label': 'Skill Definitions', 'endpoint': 'behaviour_skills.manage_skills'}
        ]
    },
    {
        'label': 'Fees & Collection',
        'icon': 'currency-dollar',
        'subitems': [
            {'label': 'Fee Invoices', 'endpoint': 'fees.invoices_list'},
            {'label': 'Generate Invoices', 'endpoint': 'fees.generate_invoices'},
            {'label': 'Collection History', 'endpoint': 'fees.payments_list'},
            {'label': 'Fee Structures', 'endpoint': 'fees.structures_list'},
            {'label': 'Fee Types', 'endpoint': 'fees.manage_types'}
        ]
    },
    {
        'label': 'Accounts & Finance',
        'icon': 'calculator',
        'subitems': [
            {'label': 'Finance Dashboard', 'endpoint': 'accounts.dashboard'},
            {'label': 'Record Income', 'endpoint': 'accounts.create_income'},
            {'label': 'Record Expense', 'endpoint': 'accounts.create_expense'},
            {'label': 'All Transactions', 'endpoint': 'accounts.transactions_list'},
            {'label': 'Financial Categories', 'endpoint': 'accounts.manage_categories'}
        ]
    },
    {
        'label': 'Salary & Payroll',
        'icon': 'banknotes',
        'subitems': [
            {'label': 'Payroll Dashboard', 'endpoint': 'payroll.dashboard'},
            {'label': 'Monthly Roster', 'endpoint': 'payroll.roster'},
            {'label': 'Generate Payroll', 'endpoint': 'payroll.generate_view'},
            {'label': 'Assign Structures', 'endpoint': 'payroll.assignments'},
            {'label': 'Salary Structures', 'endpoint': 'payroll.structures_list'},
            {'label': 'Salary Components', 'endpoint': 'payroll.components_list'}
        ]
    },
    {
        'label': 'Attendance',
        'icon': 'clipboard-check',
        'subitems': [
            {'label': 'Record Class Attendance', 'endpoint': 'attendance.class_attendance'},
            {'label': 'Class Attendance Matrix', 'endpoint': 'attendance.class_matrix'},
            {'label': 'Attendance Calendar', 'endpoint': 'attendance.calendar_view'},
            {'label': 'Staff Attendance', 'endpoint': 'attendance.employee_attendance'}
        ]
    }
]

TEACHER_NAV = [
    {
        'label': 'Dashboard',
        'endpoint': 'teacher.dashboard',
        'icon': 'home',
        'subitems': []
    },
    {
        'label': 'Question Bank & Papers',
        'icon': 'document-text',
        'subitems': [
            {'label': 'Question Bank Catalog', 'endpoint': 'question_bank.questions_list'},
            {'label': 'AI Question Generator', 'endpoint': 'question_bank.ai_generate'},
            {'label': 'Question Papers Directory', 'endpoint': 'question_bank.papers_list'}
        ]
    },
    {
        'label': 'Attendance',
        'icon': 'clipboard-check',
        'subitems': [
            {'label': 'Mark Class Attendance', 'endpoint': 'attendance.class_attendance'},
            {'label': 'Class Monthly Matrix', 'endpoint': 'attendance.class_matrix'},
            {'label': 'Attendance Calendar', 'endpoint': 'attendance.calendar_view'},
            {'label': 'My Staff Attendance', 'endpoint': 'attendance.my_staff_attendance'}
        ]
    },
    {
        'label': 'Homework',
        'icon': 'document-text',
        'subitems': [
            {'label': 'Homework Tasks', 'endpoint': 'homework.manage'},
            {'label': 'Create Homework', 'endpoint': 'homework.create'}
        ]
    },
    {
        'label': 'Behaviour & Skills',
        'icon': 'sparkles',
        'subitems': [
            {'label': 'Behaviour Observations', 'endpoint': 'behaviour_skills.behaviour_index'},
            {'label': 'Record Observation', 'endpoint': 'behaviour_skills.create_behaviour'},
            {'label': 'Skill Assessments', 'endpoint': 'behaviour_skills.assessments_index'},
            {'label': 'Bulk Skill Rating', 'endpoint': 'behaviour_skills.bulk_assessments'}
        ]
    },
    {
        'label': 'Salary & Slips',
        'icon': 'banknotes',
        'subitems': [
            {'label': 'My Salary History', 'endpoint': 'payroll.my_salary'}
        ]
    }
]

STUDENT_NAV = [
    {
        'label': 'Dashboard',
        'endpoint': 'student.dashboard',
        'icon': 'home',
        'subitems': []
    },
    {
        'label': 'Attendance',
        'icon': 'clipboard-check',
        'subitems': [
            {'label': 'My Attendance Record', 'endpoint': 'attendance.my_attendance'}
        ]
    },
    {
        'label': 'Homework',
        'icon': 'document-text',
        'subitems': [
            {'label': 'My Homework', 'endpoint': 'homework.student_index'}
        ]
    },
    {
        'label': 'Behaviour & Skills',
        'icon': 'sparkles',
        'subitems': [
            {'label': 'My Development', 'endpoint': 'behaviour_skills.student_development'}
        ]
    },
    {
        'label': 'Fees & Dues',
        'icon': 'currency-dollar',
        'subitems': [
            {'label': 'My Fee Account', 'endpoint': 'fees.student_fee_account'}
        ]
    },
    {
        'label': 'Question Banks',
        'icon': 'book-open',
        'subitems': [
            {'label': 'Practice Question Banks', 'endpoint': 'question_bank.student_banks'}
        ]
    }
]

PARENT_NAV = [
    {
        'label': 'Dashboard',
        'endpoint': 'parent.dashboard',
        'icon': 'home',
        'subitems': []
    },
    {
        'label': 'Attendance',
        'icon': 'clipboard-check',
        'subitems': [
            {'label': 'Children Attendance', 'endpoint': 'attendance.my_attendance'}
        ]
    },
    {
        'label': 'Homework',
        'icon': 'document-text',
        'subitems': [
            {'label': 'Children Homework', 'endpoint': 'homework.parent_index'}
        ]
    },
    {
        'label': 'Behaviour & Skills',
        'icon': 'sparkles',
        'subitems': [
            {'label': 'Child Development', 'endpoint': 'behaviour_skills.parent_child_development'}
        ]
    },
    {
        'label': 'Fees & Dues',
        'icon': 'currency-dollar',
        'subitems': [
            {'label': 'Children Fee Account', 'endpoint': 'fees.student_fee_account'}
        ]
    }
]

def get_navigation_for_role(role):
    """Return categorized navigation structure based on user role."""
    if not role:
        return []
    
    role = str(role).lower()
    if role == 'admin':
        return ADMIN_NAV
    elif role in ('teacher', 'employee'):
        return TEACHER_NAV
    elif role == 'student':
        return STUDENT_NAV
    elif role in ('parent', 'guardian'):
        return PARENT_NAV
    return []
