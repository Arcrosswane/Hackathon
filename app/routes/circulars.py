from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.models import db, User, SchoolCircular, SchoolClass
from app.utils.decorators import login_required
from app.services.communication_service import (
    publish_school_circular,
    get_audience_circulars
)

circulars_bp = Blueprint('circulars', __name__, url_prefix='/circulars')


@circulars_bp.route('/')
@login_required
def index():
    """Renders Formal School Circulars Catalog Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    sch_id = current_user.school_id or 1

    circulars = get_audience_circulars(school_id=sch_id, current_user=current_user)

    return render_template(
        'circulars/index.html',
        current_user=current_user,
        circulars=circulars,
        user_role=user_role
    )


@circulars_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Renders Create / Publish Formal School Circular Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    user_role = (current_user.user_type or '').lower()
    if user_role not in ('admin', 'employee'):
        flash('Permission denied to publish formal school circulars.', 'danger')
        return redirect(url_for('circulars.index'))

    sch_id = current_user.school_id or 1

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        target_audience = request.form.get('target_audience', 'Entire School').strip()
        class_id = request.form.get('class_id', type=int)

        if not title or not content:
            flash('Please provide both circular title and content.', 'warning')
            return redirect(url_for('circulars.create'))

        circular = publish_school_circular(
            school_id=sch_id,
            title=title,
            content=content,
            target_audience=target_audience,
            class_id=class_id,
            published_by_id=current_user.id
        )

        flash(f"Formal Circular #{circular.circular_number} published successfully!", 'success')
        return redirect(url_for('circulars.detail', circular_id=circular.id))

    classes = SchoolClass.query.all()
    audiences = ["Entire School", "Teachers", "Students", "Parents", "Class"]

    return render_template(
        'circulars/create.html',
        current_user=current_user,
        classes=classes,
        audiences=audiences
    )


@circulars_bp.route('/<int:circular_id>')
@login_required
def detail(circular_id):
    """Renders Dedicated Printable Formal School Circular View Page."""
    user_id = session.get('user_id')
    current_user = User.query.get(user_id) if user_id else None
    if not current_user:
        return redirect(url_for('auth.login'))

    circular = SchoolCircular.query.get_or_404(circular_id)

    return render_template(
        'circulars/detail.html',
        current_user=current_user,
        circular=circular
    )
