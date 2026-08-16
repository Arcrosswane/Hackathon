from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they are registered with SQLAlchemy
from app.models.institute import Institute
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.employee import Employee
from app.models.student import Student
from app.models.student_enrollment import StudentEnrollment
from app.models.guardian import Guardian
from app.models.guardian_student import GuardianStudent
from app.models.user import User
from app.models.attendance import Attendance
from app.models.fee import Fee
from app.models.salary import Salary
from app.models.homework import Homework, HomeworkAttachment, HomeworkSubmission
from app.models.period import Period
from app.models.timetable import Timetable
from app.models.school import School
from app.models.academic_session import AcademicSession
from app.models.setting import Setting
from app.models.subject import Subject
from app.models.subject_class import SubjectClass
from app.models.behaviour_skills import BehaviourCategory, BehaviourRecord, SkillDefinition, SkillAssessment
from app.models.fee_management import (
    FeeType, FeeStructure, FeeComponent, StudentFeeAssignment,
    FeeInvoice, FeeInvoiceItem, Payment, Receipt
)
from app.models.finance import FinanceCategory, FinancialTransaction
from app.models.payroll import (
    SalaryComponent, SalaryStructure, SalaryStructureItem,
    EmployeeSalaryAssignment, PayrollRecord, PayrollItem
)
from app.models.question_bank import (
    Question, QuestionPaper, QuestionPaperSection,
    QuestionPaperQuestion, AIQuestionGenerationLog
)
from app.models.examination import (
    ExamType, Examination, ExaminationClass, ExaminationSubject,
    ExaminationResult, ExamOverallResult, GradeRule
)

__all__ = [
    'db',
    'Institute',
    'SchoolClass',
    'Section',
    'Employee',
    'Student',
    'StudentEnrollment',
    'Guardian',
    'GuardianStudent',
    'User',
    'Attendance',
    'Fee',
    'Salary',
    'Homework',
    'HomeworkAttachment',
    'HomeworkSubmission',
    'Period',
    'Timetable',
    'School',
    'AcademicSession',
    'Setting',
    'Subject',
    'SubjectClass',
    'BehaviourCategory',
    'BehaviourRecord',
    'SkillDefinition',
    'SkillAssessment',
    'FeeType',
    'FeeStructure',
    'FeeComponent',
    'StudentFeeAssignment',
    'FeeInvoice',
    'FeeInvoiceItem',
    'Payment',
    'Receipt',
    'FinanceCategory',
    'FinancialTransaction',
    'SalaryComponent',
    'SalaryStructure',
    'SalaryStructureItem',
    'EmployeeSalaryAssignment',
    'PayrollRecord',
    'PayrollItem',
    'Question',
    'QuestionPaper',
    'QuestionPaperSection',
    'QuestionPaperQuestion',
    'AIQuestionGenerationLog',
    'ExamType',
    'Examination',
    'ExaminationClass',
    'ExaminationSubject',
    'ExaminationResult',
    'ExamOverallResult',
    'GradeRule'
]
