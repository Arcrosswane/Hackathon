from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app.utils.decorators import login_required, role_required
from app.services.ai_copilot_service import generate_ai_school_insights, get_school_data_context

ai_insights_bp = Blueprint('ai_insights', __name__, url_prefix='/admin/ai-insights')


@ai_insights_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def index():
    """Renders the dedicated full-page AI School Insights & Admin Copilot Workspace."""
    school_id = session.get('school_id') or 1
    insights_data = generate_ai_school_insights(school_id=school_id)

    return render_template(
        'ai_insights/index.html',
        insights=insights_data,
        context=insights_data.get('context', {})
    )


@ai_insights_bp.route('/ask', methods=['POST'])
@login_required
@role_required('admin')
def ask_copilot():
    """Async JSON API endpoint answering natural-language admin questions using real ERP data."""
    school_id = session.get('school_id') or 1
    data = request.get_json() or {}
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'status': 'error', 'message': 'Please enter a valid question.'}), 400

    insights_data = generate_ai_school_insights(school_id=school_id, user_question=question)
    return jsonify(insights_data)
