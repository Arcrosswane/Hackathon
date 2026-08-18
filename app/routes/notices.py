from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.models import db, User, SchoolNotice, SchoolClass, Section
from app.utils.decorators import login_required
from app.services.communication_service import (
    publish_school_notice,
    get_audience_notices
)

notices_bp = Blueprint('notices', __name__, url_prefix='/notices')


@notices_bp.route('/')
@login_required
def index():
    """Renders School Notices Directory Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    notices = get_audience_notices(school_id=sch_id, current_user=current_user)

    return render_template(
        'notices/index.html',
        current_user=current_user,
        notices=notices,
        user_role=user_role
    )


@notices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Renders Create / Publish School Notice Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'teacher', 'employee'):
        flash('Permission denied to publish school notices.', 'danger')
        return redirect(url_for('notices.index'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'Normal').strip()
        target_audience = request.form.get('target_audience', 'Entire School').strip()
        class_id = request.form.get('class_id', type=int)

        if not title or not content:
            flash('Please provide both notice title and content.', 'warning')
            return redirect(url_for('notices.create'))

        notice = publish_school_notice(
            school_id=sch_id,
            title=title,
            content=content,
            priority=priority,
            target_audience=target_audience,
            class_id=class_id,
            published_by_id=current_user.id
        )

        flash(f"School Notice '{notice.title}' published successfully to {target_audience}!", 'success')
        return redirect(url_for('notices.detail', notice_id=notice.id))

    classes = SchoolClass.query.all()
    audiences = ["Entire School", "Teachers", "Students", "Parents", "Class"]

    return render_template(
        'notices/create.html',
        current_user=current_user,
        classes=classes,
        audiences=audiences
    )


@notices_bp.route('/<int:notice_id>')
@login_required
def detail(notice_id):
    """Renders Dedicated School Notice Detail Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    notice = SchoolNotice.query.get_or_404(notice_id)

    return render_template(
        'notices/detail.html',
        current_user=current_user,
        notice=notice
    )


@notices_bp.route('/<int:notice_id>/archive', methods=['POST'])
@login_required
def archive(notice_id):
    """Archives a published notice."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user or (current_user.user_type or '').lower() != 'admin':
        flash('Permission denied to archive notices.', 'danger')
        return redirect(url_for('notices.index'))

    notice = SchoolNotice.query.get_or_404(notice_id)
    notice.status = 'Archived'
    db.session.commit()

    flash('School Notice archived successfully.', 'info')
    return redirect(url_for('notices.index'))
