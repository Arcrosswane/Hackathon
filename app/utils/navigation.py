# Centralized Navigation Configuration for StratLearn
# Unbuilt/Future items flagged with 'is_future': True for dull styling and FUTURE badge.

ADMIN_NAV = [
    {'label': 'Dashboard', 'endpoint': 'admin.dashboard', 'icon': 'home', 'subitems': []},
    {
        'label': 'General Settings', 'icon': 'cog',
        'subitems': [
            {'label': 'School Profile', 'endpoint': 'settings.school_profile'},
            {'label': 'School Setup', 'endpoint': 'school.setup'}
        ]
    },
    {
        'label': 'Classes', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'All Classes', 'endpoint': 'classes.index'}
        ]
    },
    {
        'label': 'Subjects', 'icon': 'book-open',
        'subitems': [
            {'label': 'Subjects Catalog', 'endpoint': 'subjects.index'},
            {'label': 'Subject Assignments', 'endpoint': 'subjects.assignments'}
        ]
    },
    {
        'label': 'Students', 'icon': 'user',
        'subitems': [
            {'label': 'All Students', 'endpoint': 'students.index'},
            {'label': 'Parents & Guardians', 'endpoint': 'guardians.index'}
        ]
    },
    {
        'label': 'Employees', 'icon': 'briefcase',
        'subitems': [
            {'label': 'All Employees', 'endpoint': 'employees.index'}
        ]
    },
    {
        'label': 'Accounts', 'icon': 'calculator',
        'subitems': [
            {'label': 'Finance Dashboard', 'endpoint': 'accounts.dashboard'},
            {'label': 'Record Income', 'endpoint': 'accounts.create_income'},
            {'label': 'Record Expense', 'endpoint': 'accounts.create_expense'},
            {'label': 'All Transactions', 'endpoint': 'accounts.transactions_list'},
            {'label': 'Financial Categories', 'endpoint': 'accounts.manage_categories'}
        ]
    },
    {
        'label': 'Fees', 'icon': 'currency-dollar',
        'subitems': [
            {'label': 'Fee Invoices', 'endpoint': 'fees.invoices_list'},
            {'label': 'Generate Invoices', 'endpoint': 'fees.generate_invoices'},
            {'label': 'Collection History', 'endpoint': 'fees.payments_list'},
            {'label': 'Fee Structures', 'endpoint': 'fees.structures_list'},
            {'label': 'Fee Types', 'endpoint': 'fees.manage_types'}
        ]
    },
    {
        'label': 'Salary', 'icon': 'banknotes',
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
        'label': 'Attendance', 'icon': 'clipboard-check',
        'subitems': [
            {'label': 'Record Class Attendance', 'endpoint': 'attendance.class_attendance'},
            {'label': 'Class Attendance Matrix', 'endpoint': 'attendance.class_matrix'},
            {'label': 'Attendance Calendar', 'endpoint': 'attendance.calendar_view'},
            {'label': 'Staff Attendance', 'endpoint': 'attendance.employee_attendance'}
        ]
    },
    {
        'label': 'Timetable', 'icon': 'calendar',
        'subitems': [
            {'label': 'Class Timetables', 'endpoint': 'timetables.index'},
            {'label': 'Period Settings', 'endpoint': 'timetables.period_settings'}
        ]
    },
    {'label': 'Homework', 'endpoint': 'homework.manage', 'icon': 'document-text', 'subitems': []},
    {
        'label': 'Behaviour & Skills', 'icon': 'sparkles',
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
        'label': 'Online Store & POS', 'icon': 'shopping-bag', 'is_future': True,
        'subitems': [
            {'label': 'Fee & Service Accounts', 'endpoint': 'fees.invoices_list'}
        ]
    },
    {
        'label': 'Messaging', 'icon': 'chat',
        'subitems': [
            {'label': 'Internal School Messages', 'endpoint': 'admin.dashboard'},
            {'label': 'WhatsApp Gateway & Services', 'endpoint': 'admin.dashboard', 'is_future': True},
            {'label': 'SMS Services & Broadcasts', 'endpoint': 'admin.dashboard', 'is_future': True}
        ]
    },
    {'label': 'Live Class', 'endpoint': 'timetables.live_class', 'icon': 'video-camera', 'is_future': True, 'subitems': []},
    {
        'label': 'Question Paper', 'icon': 'document-text',
        'subitems': [
            {'label': 'Question Bank Catalog', 'endpoint': 'question_bank.questions_list'},
            {'label': 'AI Question Generator', 'endpoint': 'question_bank.ai_generate'},
            {'label': 'Question Papers Directory', 'endpoint': 'question_bank.papers_list'}
        ]
    },
    {
        'label': 'Exams', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'All Examinations', 'endpoint': 'examination.exams_list'},
            {'label': 'Exam Types & Grading', 'endpoint': 'examination.exam_types_page'}
        ]
    },
    {
        'label': 'Class Tests', 'icon': 'document-check',
        'subitems': [
            {'label': 'All Class Tests', 'endpoint': 'homework.manage'}
        ]
    },
    {
        'label': 'Reports', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'Exam Result Matrices', 'endpoint': 'examination.exams_list'}
        ]
    },
    {
        'label': 'Certificates', 'icon': 'academic-cap', 'is_future': True,
        'subitems': [
            {'label': 'Issue Certificates', 'endpoint': 'students.index', 'is_future': True}
        ]
    }
]

TEACHER_NAV = [
    {'label': 'Dashboard', 'endpoint': 'teacher.dashboard', 'icon': 'home', 'subitems': []},
    {
        'label': 'Attendance', 'icon': 'clipboard-check',
        'subitems': [
            {'label': 'Mark Class Attendance', 'endpoint': 'attendance.class_attendance'},
            {'label': 'Class Monthly Matrix', 'endpoint': 'attendance.class_matrix'},
            {'label': 'Attendance Calendar', 'endpoint': 'attendance.calendar_view'},
            {'label': 'My Staff Attendance', 'endpoint': 'attendance.my_staff_attendance'}
        ]
    },
    {'label': 'Homework', 'endpoint': 'homework.manage', 'icon': 'document-text', 'subitems': []},
    {'label': 'My Timetable', 'endpoint': 'teacher.my_timetable', 'icon': 'calendar', 'subitems': []},
    {
        'label': 'Behaviour & Skills', 'icon': 'sparkles',
        'subitems': [
            {'label': 'Behaviour Observations', 'endpoint': 'behaviour_skills.behaviour_index'},
            {'label': 'Record Observation', 'endpoint': 'behaviour_skills.create_behaviour'},
            {'label': 'Skill Assessments', 'endpoint': 'behaviour_skills.assessments_index'},
            {'label': 'Bulk Skill Rating', 'endpoint': 'behaviour_skills.bulk_assessments'}
        ]
    },
    {
        'label': 'Messaging', 'icon': 'chat',
        'subitems': [
            {'label': 'Class & Parent Messages', 'endpoint': 'teacher.dashboard'},
            {'label': 'WhatsApp Notifications', 'endpoint': 'teacher.dashboard', 'is_future': True},
            {'label': 'SMS Alerts', 'endpoint': 'teacher.dashboard', 'is_future': True}
        ]
    },
    {'label': 'Live Class', 'endpoint': 'timetables.live_class', 'icon': 'video-camera', 'is_future': True, 'subitems': []},
    {
        'label': 'Question Paper', 'icon': 'document-text',
        'subitems': [
            {'label': 'Question Bank Catalog', 'endpoint': 'question_bank.questions_list'},
            {'label': 'AI Question Generator', 'endpoint': 'question_bank.ai_generate'},
            {'label': 'Question Papers Directory', 'endpoint': 'question_bank.papers_list'}
        ]
    },
    {
        'label': 'Exams', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'Mark Student Exams', 'endpoint': 'examination.teacher_marks_dashboard'},
            {'label': 'Exam Schedules & Papers', 'endpoint': 'examination.exams_list'}
        ]
    },
    {
        'label': 'Class Tests', 'icon': 'document-check',
        'subitems': [
            {'label': 'Class Assignments & Tests', 'endpoint': 'homework.manage'}
        ]
    },
    {
        'label': 'Reports', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'Class Performance Reports', 'endpoint': 'examination.exams_list'}
        ]
    },
    {'label': 'Account Settings', 'endpoint': 'teacher.account', 'icon': 'cog', 'subitems': []},
    {'label': 'Log out', 'endpoint': 'auth.logout', 'icon': 'logout', 'subitems': []}
]

STUDENT_NAV = [
    {'label': 'Dashboard', 'endpoint': 'student.dashboard', 'icon': 'home', 'subitems': []},
    {'label': 'Admission Letter', 'endpoint': 'students.index', 'icon': 'document', 'is_future': True, 'subitems': []},
    {'label': 'Paid Fee Recipt', 'endpoint': 'fees.student_fee_account', 'icon': 'currency-dollar', 'subitems': []},
    {'label': 'My Timetable', 'endpoint': 'timetables.index', 'icon': 'calendar', 'subitems': []},
    {'label': 'My Report Card', 'endpoint': 'examination.student_results', 'icon': 'academic-cap', 'subitems': []},
    {'label': 'Test Results', 'endpoint': 'question_bank.student_banks', 'icon': 'document-check', 'subitems': []},
    {'label': 'Exam Result', 'endpoint': 'examination.student_results', 'icon': 'academic-cap', 'subitems': []},
    {'label': 'Home Assignments', 'endpoint': 'homework.student_index', 'icon': 'document-text', 'subitems': []},
    {'label': 'Online Store', 'endpoint': 'fees.student_fee_account', 'icon': 'shopping-bag', 'is_future': True, 'subitems': []},
    {
        'label': 'Messaging', 'icon': 'chat',
        'subitems': [
            {'label': 'Teacher Communication', 'endpoint': 'student.dashboard'},
            {'label': 'WhatsApp Notifications', 'endpoint': 'student.dashboard', 'is_future': True}
        ]
    },
    {'label': 'Live Class', 'endpoint': 'timetables.live_class', 'icon': 'video-camera', 'is_future': True, 'subitems': []},
    {'label': 'Account Settings', 'endpoint': 'student.account', 'icon': 'cog', 'subitems': []},
    {'label': 'Log out', 'endpoint': 'auth.logout', 'icon': 'logout', 'subitems': []}
]

PARENT_NAV = [
    {'label': 'Dashboard', 'endpoint': 'parent.dashboard', 'icon': 'home', 'subitems': []},
    {'label': 'Child Attendance', 'endpoint': 'attendance.my_attendance', 'icon': 'clipboard-check', 'is_future': True, 'subitems': []},
    {'label': 'Child Homework', 'endpoint': 'homework.parent_index', 'icon': 'document-text', 'subitems': []},
    {'label': 'Child Development', 'endpoint': 'behaviour_skills.parent_child_development', 'icon': 'sparkles', 'subitems': []},
    {'label': 'Fee Payment & History', 'endpoint': 'fees.student_fee_account', 'icon': 'currency-dollar', 'is_future': True, 'subitems': []},
    {'label': 'Child Exam Results', 'endpoint': 'examination.parent_results', 'icon': 'academic-cap', 'subitems': []},
    {'label': 'Account Settings', 'endpoint': 'parent.account', 'icon': 'cog', 'subitems': []},
    {'label': 'Log out', 'endpoint': 'auth.logout', 'icon': 'logout', 'subitems': []}
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
