from flask import Blueprint, render_template, redirect, url_for, flash
from app.utils.decorators import login_required

live_classes_bp = Blueprint('live_classes', __name__, url_prefix='/live-classes')

@live_classes_bp.route('/', methods=['GET'])
@login_required
def workspace():
    flash("Live Classes is scheduled for a future release.", "info")
    return redirect(url_for('admin.dashboard'))

@live_classes_bp.route('/schedule', methods=['POST'])
@login_required
def schedule_class():
    flash("Live Class scheduling is currently in preview mode.", "info")
    return redirect(url_for('admin.dashboard'))
