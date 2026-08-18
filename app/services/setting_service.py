from app.models import db, Setting

DEFAULT_SETTINGS = {
    'timezone': 'Asia/Kolkata',
    'country': 'India',
    'currency': 'INR (₹)',
    'date_format': 'YYYY-MM-DD',
    'time_format': '12-hour',
    'passing_percentage': '33',
    'grading_system': 'Percentage'
}

def get_setting(key, default=None):
    """
    Retrieve value of a setting by key. Returns default if key is not found.
    """
    setting = Setting.query.filter_by(key=key).first()
    if setting and setting.value is not None:
        return setting.value
    if default is not None:
        return default
    return DEFAULT_SETTINGS.get(key, None)

def set_setting(key, value):
    """
    Update or create a setting key-value pair.
    """
    setting = Setting.query.filter_by(key=key).first()
    if not setting:
        setting = Setting(key=key, value=str(value))
        db.session.add(setting)
    else:
        setting.value = str(value)
    db.session.commit()
    return setting

def get_all_settings():
    """
    Returns a dictionary of all current settings merged with default fallback values.
    """
    all_records = Setting.query.all()
    settings_dict = DEFAULT_SETTINGS.copy()
    for record in all_records:
        settings_dict[record.key] = record.value
    return settings_dict

def initialize_default_settings():
    """
    Ensures default settings exist in the database.
    """
    for key, value in DEFAULT_SETTINGS.items():
        existing = Setting.query.filter_by(key=key).first()
        if not existing:
            new_setting = Setting(key=key, value=value)
            db.session.add(new_setting)
    db.session.commit()


# ==========================================
# ROLE & PERMISSION MATRIX MANAGEMENT
# ==========================================

ALL_PERMISSIONS = [
    'students.view', 'students.create', 'students.edit', 'students.delete',
    'attendance.view', 'attendance.manage',
    'homework.view', 'homework.create', 'homework.edit',
    'exams.view', 'exams.manage',
    'fees.view', 'fees.manage',
    'payroll.view', 'payroll.manage',
    'reports.view',
    'syllabus.view', 'syllabus.manage',
    'syllabus_monitoring.view', 'syllabus_monitoring.manage',
    'communication.view', 'communication.manage',
    'settings.view', 'settings.manage'
]

DEFAULT_ROLE_PERMISSIONS = {
    'ADMIN': ALL_PERMISSIONS,
    'TEACHER': [
        'students.view', 'attendance.view', 'attendance.manage',
        'homework.view', 'homework.create', 'homework.edit',
        'exams.view', 'exams.manage', 'reports.view',
        'syllabus.view', 'syllabus.manage', 'communication.view'
    ],
    'STUDENT': [
        'attendance.view', 'homework.view', 'exams.view', 'reports.view', 'syllabus.view'
    ],
    'PARENT': [
        'attendance.view', 'homework.view', 'exams.view', 'fees.view', 'reports.view', 'syllabus.view'
    ]
}


def initialize_default_role_permissions():
    """
    Ensures default role permission records exist in the database.
    """
    from app.models import RolePermission
    for role_name, granted_keys in DEFAULT_ROLE_PERMISSIONS.items():
        for p_key in ALL_PERMISSIONS:
            existing = RolePermission.query.filter_by(role_name=role_name, permission_key=p_key).first()
            if not existing:
                is_granted = p_key in granted_keys
                rp = RolePermission(role_name=role_name, permission_key=p_key, is_granted=is_granted)
                db.session.add(rp)
    db.session.commit()


def get_role_permissions_matrix():
    """
    Returns matrix dictionary of role permissions: {role_name: {permission_key: bool}}.
    """
    from app.models import RolePermission
    initialize_default_role_permissions()
    records = RolePermission.query.all()
    matrix = {'ADMIN': {}, 'TEACHER': {}, 'STUDENT': {}, 'PARENT': {}}
    for r in records:
        if r.role_name not in matrix:
            matrix[r.role_name] = {}
        matrix[r.role_name][r.permission_key] = r.is_granted
    return matrix


def update_role_permission(role_name, permission_key, is_granted):
    """
    Updates or creates a specific role permission setting. Protects ADMIN settings.manage.
    """
    from app.models import RolePermission
    # Protect critical admin permission
    if role_name == 'ADMIN' and permission_key == 'settings.manage' and not is_granted:
        return False

    rp = RolePermission.query.filter_by(role_name=role_name, permission_key=permission_key).first()
    if not rp:
        rp = RolePermission(role_name=role_name, permission_key=permission_key, is_granted=is_granted)
        db.session.add(rp)
    else:
        rp.is_granted = is_granted
    db.session.commit()
    return True


def has_permission(user, permission_key):
    """
    SERVER-SIDE AUTHORIZATION: Checks if a user has a specific permission.
    Admins automatically have all granted permissions unless explicitly restricted.
    """
    if not user:
        return False

    user_role = (user.user_type or '').upper()
    if user_role in ('ADMIN', 'ADMINISTRATOR'):
        return True

    from app.models import RolePermission
    rp = RolePermission.query.filter_by(role_name=user_role, permission_key=permission_key).first()
    if rp:
        return rp.is_granted

    # Fallback to default role permissions
    default_granted = DEFAULT_ROLE_PERMISSIONS.get(user_role, [])
    return permission_key in default_granted


# ==========================================
# AUDIT LOGGING
# ==========================================

def log_audit_event(school_id, user_id, action, module, details=None):
    """
    Records an administrative audit log event.
    """
    from app.models import db, AuditLog
    sch_id = school_id or 1
    log = AuditLog(
        school_id=sch_id,
        user_id=user_id,
        action=action,
        module=module,
        details=str(details) if details else None
    )
    db.session.add(log)
    db.session.commit()
    return log


def get_audit_logs(school_id=None, limit=50):
    """
    Fetches recent audit log records for administrative inspection.
    """
    from app.models import AuditLog
    sch_id = school_id or 1
    return AuditLog.query.filter_by(school_id=sch_id).order_by(AuditLog.created_at.desc()).limit(limit).all()
