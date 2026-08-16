from app.services.academic_service import get_active_academic_session, set_active_academic_session
from app.services.admin_dashboard_service import get_admin_dashboard_summary
from app.services.teacher_dashboard_service import get_teacher_dashboard_summary
from app.services.student_dashboard_service import get_student_dashboard_summary
from app.services.parent_dashboard_service import get_parent_dashboard_summary
from app.services.setting_service import get_setting, set_setting, get_all_settings
from app.services.class_service import get_classes_for_session, create_class, create_section
from app.services.subject_service import get_all_subjects, get_subjects_for_class, assign_subject_to_class
from app.services.employee_service import get_all_employees, get_teachers, get_employee_by_id
from app.services.student_service import get_all_students, get_current_enrollment, transfer_student
from app.services.guardian_service import get_all_guardians, link_guardian_student, unlink_guardian_student
from app.services.timetable_service import (
    DAYS_OF_WEEK, ENTRY_TYPES, TIMETABLE_STATUSES,
    get_all_periods_for_session, initialize_default_periods_for_session,
    check_conflicts, get_class_timetable, get_teacher_timetable, get_student_timetable,
    create_or_update_timetable_entry, delete_timetable_entry, publish_class_timetable
)
from app.services.homework_service import (
    get_homework_by_id, get_all_homework, create_homework, update_homework,
    publish_homework, archive_homework, delete_homework, get_student_eligible_homework,
    submit_student_homework, get_homework_submission_roster, review_student_submission,
    get_parent_children_homework_summary
)
from app.services.behaviour_skills_service import (
    get_all_behaviour_categories, create_behaviour_category, update_behaviour_category, toggle_behaviour_category_status,
    get_all_skill_definitions, create_skill_definition, update_skill_definition, toggle_skill_definition_status,
    create_behaviour_record, update_behaviour_record, delete_behaviour_record, get_behaviour_records,
    record_skill_assessment, record_bulk_skill_assessments, get_skill_assessments,
    get_student_development_summary, verify_teacher_student_access, verify_parent_student_access,
    RATING_LABELS
)
from app.services.fee_service import (
    get_all_fee_types, create_fee_type, update_fee_type, toggle_fee_type_status,
    get_fee_structures, create_fee_structure, update_fee_structure, toggle_fee_structure_status,
    generate_student_invoice, generate_batch_class_invoices, get_invoices, delete_invoice,
    record_payment, get_payments, get_receipt_by_id,
    get_student_fee_summary, get_collection_summary,
    verify_parent_invoice_access, verify_parent_receipt_access, VALID_PAYMENT_METHODS
)
from app.services.question_bank_service import (
    create_question, update_question, archive_question, delete_question, delete_question_bank, delete_question_paper, get_questions,
    create_question_paper, add_question_to_paper_section, remove_question_from_paper,
    recalculate_paper_totals, finalize_question_paper, duplicate_question_paper,
    VALID_QUESTION_TYPES, VALID_DIFFICULTIES
)
from app.services.ai_question_service import (
    generate_ai_questions, improve_question_with_ai, convert_document_to_questions
)
from app.services.examination_service import (
    get_exam_types, create_exam_type, delete_exam_type, get_grade_rules, delete_grade_rule, calculate_grade_from_percentage,
    create_examination, update_examination, delete_examination, get_examinations, assign_classes_to_exam, add_exam_subject,
    attach_question_paper_to_exam_subject, check_schedule_conflicts, save_bulk_exam_marks,
    calculate_and_publish_exam_results, correct_published_result, get_student_published_results,
    get_exam_performance_statistics, generate_result_sheet_csv, generate_ai_exam_insights
)
from app.services.finance_service import (
    get_all_categories, create_category, update_category, toggle_category_status,
    create_manual_transaction, sync_single_payment_to_finance, sync_all_fee_payments_to_finance,
    get_financial_transactions, get_finance_dashboard_summary, cancel_transaction
)
from app.services.payroll_service import (
    get_all_salary_components, create_salary_component, toggle_salary_component_status,
    get_all_salary_structures, create_salary_structure, update_salary_structure, delete_salary_structure,
    assign_salary_structure, assign_structure_to_all_employees, get_employee_active_assignment, calculate_employee_salary_snapshot,
    generate_batch_payroll, approve_payroll, record_salary_payment, delete_payroll_record,
    sync_payroll_to_finance_expense, get_payroll_records, get_payroll_summary_metrics
)
from app.services.attendance_service import (
    save_bulk_class_student_attendance, save_bulk_employee_attendance,
    get_class_daily_attendance, get_student_attendance_summary,
    get_employee_attendance_summary, get_class_attendance_matrix,
    verify_teacher_class_access, get_today_attendance_overview,
    get_month_calendar_attendance, generate_attendance_csv_export,
    VALID_ATTENDANCE_STATUSES
)

__all__ = [
    'get_active_academic_session',
    'set_active_academic_session',
    'get_setting',
    'set_setting',
    'get_all_settings',
    'get_classes_for_session',
    'create_class',
    'create_section',
    'get_all_subjects',
    'get_subjects_for_class',
    'assign_subject_to_class',
    'get_all_employees',
    'get_teachers',
    'get_employee_by_id',
    'get_all_students',
    'get_current_enrollment',
    'transfer_student',
    'get_all_guardians',
    'link_guardian_student',
    'unlink_guardian_student',
    'DAYS_OF_WEEK',
    'ENTRY_TYPES',
    'TIMETABLE_STATUSES',
    'get_all_periods_for_session',
    'initialize_default_periods_for_session',
    'check_conflicts',
    'get_class_timetable',
    'get_teacher_timetable',
    'get_student_timetable',
    'create_or_update_timetable_entry',
    'delete_timetable_entry',
    'publish_class_timetable',
    'get_homework_by_id',
    'get_all_homework',
    'create_homework',
    'update_homework',
    'publish_homework',
    'archive_homework',
    'delete_homework',
    'get_student_eligible_homework',
    'submit_student_homework',
    'get_homework_submission_roster',
    'review_student_submission',
    'get_parent_children_homework_summary',
    'get_all_behaviour_categories',
    'create_behaviour_category',
    'update_behaviour_category',
    'toggle_behaviour_category_status',
    'get_all_skill_definitions',
    'create_skill_definition',
    'update_skill_definition',
    'toggle_skill_definition_status',
    'create_behaviour_record',
    'update_behaviour_record',
    'delete_behaviour_record',
    'get_behaviour_records',
    'record_skill_assessment',
    'record_bulk_skill_assessments',
    'get_skill_assessments',
    'get_student_development_summary',
    'verify_teacher_student_access',
    'verify_parent_student_access',
    'RATING_LABELS',
    'get_all_fee_types',
    'create_fee_type',
    'update_fee_type',
    'toggle_fee_type_status',
    'get_fee_structures',
    'create_fee_structure',
    'update_fee_structure',
    'toggle_fee_structure_status',
    'generate_student_invoice',
    'generate_batch_class_invoices',
    'get_invoices',
    'record_payment',
    'get_payments',
    'get_receipt_by_id',
    'get_student_fee_summary',
    'get_collection_summary',
    'verify_parent_invoice_access',
    'verify_parent_receipt_access',
    'VALID_PAYMENT_METHODS',
    'get_all_categories',
    'create_category',
    'update_category',
    'toggle_category_status',
    'create_manual_transaction',
    'sync_single_payment_to_finance',
    'sync_all_fee_payments_to_finance',
    'get_financial_transactions',
    'get_finance_dashboard_summary',
    'cancel_transaction',
    'get_all_salary_components',
    'create_salary_component',
    'toggle_salary_component_status',
    'get_all_salary_structures',
    'create_salary_structure',
    'assign_salary_structure',
    'get_employee_active_assignment',
    'calculate_employee_salary_snapshot',
    'generate_batch_payroll',
    'approve_payroll',
    'record_salary_payment',
    'sync_payroll_to_finance_expense',
    'get_payroll_records',
    'get_payroll_summary_metrics',
    'save_bulk_class_student_attendance',
    'save_bulk_employee_attendance',
    'get_class_daily_attendance',
    'get_student_attendance_summary',
    'get_employee_attendance_summary',
    'get_class_attendance_matrix',
    'verify_teacher_class_access',
    'get_today_attendance_overview',
    'get_month_calendar_attendance',
    'generate_attendance_csv_export',
    'VALID_ATTENDANCE_STATUSES',
    'create_question',
    'update_question',
    'archive_question',
    'get_questions',
    'create_question_paper',
    'add_question_to_paper_section',
    'remove_question_from_paper',
    'recalculate_paper_totals',
    'finalize_question_paper',
    'duplicate_question_paper',
    'generate_ai_questions',
    'improve_question_with_ai',
    'VALID_QUESTION_TYPES',
    'VALID_DIFFICULTIES'
]
