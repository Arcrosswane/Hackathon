from app.models import db

class Salary(db.Model):
    __tablename__ = 'salaries'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    monthly_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=True)
    month_year = db.Column(db.String(50), nullable=True) # e.g. "Aug 2026"
    status = db.Column(db.String(20), default="Not Received") # "Received", "Not Received"

    def __repr__(self):
        return f'<Salary Employee #{self.employee_id} [{self.month_year}]: {self.status}>'
