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
