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
        'label': 'Syllabus & Notebooks', 'icon': 'book-open',
        'subitems': [
            {'label': 'Syllabus Workspace', 'endpoint': 'syllabus.index'},
            {'label': 'Syllabus Monitoring (Admin)', 'endpoint': 'syllabus_monitoring.index'},
            {'label': 'Monthly Syllabus Targets', 'endpoint': 'syllabus_monitoring.targets_list'},
            {'label': 'Create Monthly Target', 'endpoint': 'syllabus_monitoring.create_target_page'},
            {'label': 'Manage Chapters & Topics', 'endpoint': 'syllabus.manage'},
            {'label': 'Student Notebook Matrix', 'endpoint': 'syllabus.notebook_index'},
            {'label': 'Admin Progress Overview', 'endpoint': 'syllabus.admin_overview'}
        ]
    },
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
        'label': 'Communication & Notices', 'icon': 'chat',
        'subitems': [
            {'label': 'Notification Center', 'endpoint': 'notifications.center'},
            {'label': 'School Notices', 'endpoint': 'notices.index'},
            {'label': 'Publish School Notice', 'endpoint': 'notices.create'},
            {'label': 'Formal Circulars Catalog', 'endpoint': 'circulars.index'},
            {'label': 'Publish Formal Circular', 'endpoint': 'circulars.create'},
            {'label': 'Internal School Messages', 'endpoint': 'messaging.inbox'},
            {'label': 'SMS & WhatsApp Settings', 'endpoint': 'communication.settings'},
            {'label': 'Communication Templates', 'endpoint': 'communication.templates'}
        ]
    },
    {
        'label': 'School Store & POS', 'icon': 'shopping-bag',
        'subitems': [
            {'label': 'Store Command Center', 'endpoint': 'store.admin_dashboard'},
            {'label': 'Products Master Roster', 'endpoint': 'store.admin_products'},
            {'label': 'Physical Counter POS', 'endpoint': 'store.pos_terminal'}
        ]
    },
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
        'label': 'Reports & Analytics', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'Reports Directory', 'endpoint': 'reports.index'},
            {'label': 'Academic Reports', 'endpoint': 'reports.academic'},
            {'label': 'Print Report Cards', 'endpoint': 'reports.academic_report_card'},
            {'label': 'Attendance Reports', 'endpoint': 'reports.attendance'},
            {'label': 'Fee Collection Reports', 'endpoint': 'reports.fees'},
            {'label': 'Payroll Reports', 'endpoint': 'reports.payroll'},
            {'label': 'Student Roster Reports', 'endpoint': 'reports.students'},
            {'label': 'Performance Analytics', 'endpoint': 'reports.performance'}
        ]
    },
    {
        'label': 'Certificates', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'Certificates History', 'endpoint': 'certificates.index'},
            {'label': 'Issue New Certificate', 'endpoint': 'certificates.create'},
            {'label': 'Verify Certificate', 'endpoint': 'certificates.verify'}
        ]
    },
    {
        'label': 'Settings & Config', 'icon': 'cog',
        'subitems': [
            {'label': 'School Profile', 'endpoint': 'settings.school_profile'},
            {'label': 'Academic Sessions', 'endpoint': 'settings.academic_sessions'},
            {'label': 'Roles Overview', 'endpoint': 'settings.roles'},
            {'label': 'Permissions Matrix', 'endpoint': 'settings.permissions_matrix'},
            {'label': 'Communication & Providers', 'endpoint': 'settings.communication_settings'},
            {'label': 'Attendance Rules', 'endpoint': 'settings.attendance_settings'},
            {'label': 'Finance & Payroll Config', 'endpoint': 'settings.finance_settings'},
            {'label': 'System & Audit Logs', 'endpoint': 'settings.system_settings'}
        ]
    },
    {'label': 'AI School Insights', 'endpoint': 'ai_insights.index', 'icon': 'sparkles', 'subitems': []}
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
    {
        'label': 'Syllabus & Notebooks', 'icon': 'book-open',
        'subitems': [
            {'label': 'My Syllabus Tracker', 'endpoint': 'syllabus.index'},
            {'label': 'Student Notebook Matrix', 'endpoint': 'syllabus.notebook_index'}
        ]
    },
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
        'label': 'Communication & Notices', 'icon': 'chat',
        'subitems': [
            {'label': 'Notification Center', 'endpoint': 'notifications.center'},
            {'label': 'School Notices', 'endpoint': 'notices.index'},
            {'label': 'Publish School Notice', 'endpoint': 'notices.create'},
            {'label': 'Formal Circulars Catalog', 'endpoint': 'circulars.index'},
            {'label': 'Class & Parent Messages', 'endpoint': 'messaging.inbox'}
        ]
    },
    {
        'label': 'School Store & POS', 'icon': 'shopping-bag',
        'subitems': [
            {'label': 'Store Catalog & Ordering', 'endpoint': 'store.catalog'},
            {'label': 'Order History & Receipts', 'endpoint': 'store.user_orders'},
            {'label': 'Physical Counter POS', 'endpoint': 'store.pos_terminal'}
        ]
    },
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
        'label': 'Reports & Certificates', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'Academic Reports', 'endpoint': 'reports.academic'},
            {'label': 'Print Report Cards', 'endpoint': 'reports.academic_report_card'},
            {'label': 'Class Attendance Reports', 'endpoint': 'reports.attendance'},
            {'label': 'Class Performance', 'endpoint': 'reports.performance'},
            {'label': 'Certificates History', 'endpoint': 'certificates.index'},
            {'label': 'Issue Certificate', 'endpoint': 'certificates.create'}
        ]
    },
    {'label': 'Account Settings', 'endpoint': 'teacher.account', 'icon': 'cog', 'subitems': []},
    {'label': 'Log out', 'endpoint': 'auth.logout', 'icon': 'logout', 'subitems': []}
]

STUDENT_NAV = [
    {'label': 'Dashboard', 'endpoint': 'student.dashboard', 'icon': 'home', 'subitems': []},
    {
        'label': 'Academics & Timetable', 'icon': 'calendar',
        'subitems': [
            {'label': 'My Class Timetable', 'endpoint': 'timetables.index'},
            {'label': 'Home Assignments', 'endpoint': 'homework.student_index'}
        ]
    },
    {
        'label': 'Exams & Performance', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'Exam Results & Report Card', 'endpoint': 'examination.student_results'},
            {'label': 'Test Papers & Question Banks', 'endpoint': 'question_bank.student_banks'}
        ]
    },
    {
        'label': 'Fees & Receipts', 'icon': 'currency-dollar',
        'subitems': [
            {'label': 'My Fee Account & Receipts', 'endpoint': 'fees.student_fee_account'}
        ]
    },
    {
        'label': 'Reports & Certificates', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'My Official Report Card', 'endpoint': 'reports.academic_report_card'},
            {'label': 'My Attendance Summary', 'endpoint': 'reports.attendance'},
            {'label': 'My Certificates', 'endpoint': 'certificates.index'}
        ]
    },
    {
        'label': 'Communication & Notices', 'icon': 'chat',
        'subitems': [
            {'label': 'Notification Center', 'endpoint': 'notifications.center'},
            {'label': 'School Notices', 'endpoint': 'notices.index'},
            {'label': 'Official Circulars', 'endpoint': 'circulars.index'},
            {'label': 'Teacher Communication', 'endpoint': 'messaging.inbox'}
        ]
    },
    {'label': 'Account Settings', 'endpoint': 'student.account', 'icon': 'cog', 'subitems': []}
]

PARENT_NAV = [
    {'label': 'Dashboard', 'endpoint': 'parent.dashboard', 'icon': 'home', 'subitems': []},
    {
        'label': 'Child Academics', 'icon': 'academic-cap',
        'subitems': [
            {'label': 'Child Homework', 'endpoint': 'homework.parent_index'},
            {'label': 'Child Development & Skills', 'endpoint': 'behaviour_skills.parent_child_development'},
            {'label': 'Child Exam Results', 'endpoint': 'examination.parent_results'}
        ]
    },
    {
        'label': 'Reports & Certificates', 'icon': 'chart-bar',
        'subitems': [
            {'label': 'Child Official Report Card', 'endpoint': 'reports.academic_report_card'},
            {'label': 'Child Attendance Summary', 'endpoint': 'reports.attendance'},
            {'label': 'Child Fee Account', 'endpoint': 'reports.fees'},
            {'label': 'Child Certificates', 'endpoint': 'certificates.index'}
        ]
    },
    {
        'label': 'Fees & Accounts', 'icon': 'currency-dollar',
        'subitems': [
            {'label': 'Fee Payment & History', 'endpoint': 'fees.student_fee_account'}
        ]
    },
    {
        'label': 'School Store & POS', 'icon': 'shopping-bag',
        'subitems': [
            {'label': 'School Store Catalog', 'endpoint': 'store.catalog'},
            {'label': 'My Store Orders', 'endpoint': 'store.user_orders'}
        ]
    },
    {
        'label': 'Communication & Notices', 'icon': 'chat',
        'subitems': [
            {'label': 'Notification Center', 'endpoint': 'notifications.center'},
            {'label': 'School Notices', 'endpoint': 'notices.index'},
            {'label': 'Official Circulars', 'endpoint': 'circulars.index'},
            {'label': 'School Messaging', 'endpoint': 'messaging.inbox'}
        ]
    },
    {'label': 'Account Settings', 'endpoint': 'parent.account', 'icon': 'cog', 'subitems': []}
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
