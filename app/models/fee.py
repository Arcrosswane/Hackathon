from app.models import db

class Fee(db.Model):
    __tablename__ = 'fees'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    estimated_amount = db.Column(db.Numeric(10, 2), nullable=False)
    collected_amount = db.Column(db.Numeric(10, 2), default=0.00)
    due_date = db.Column(db.Date, nullable=True)
    payment_status = db.Column(db.String(20), default="Unpaid") # "Paid", "Partial", "Unpaid"
    month_year = db.Column(db.String(50), nullable=True) # e.g. "August 2026"

    def __repr__(self):
        return f'<Fee Student #{self.student_id} [{self.month_year}]: {self.payment_status}>'
