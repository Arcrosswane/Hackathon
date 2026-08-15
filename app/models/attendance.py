from app.models import db

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey('institutes.id'), nullable=False)
    entity_type = db.Column(db.String(20), nullable=False) # "Student" or "Employee"
    entity_id = db.Column(db.Integer, nullable=False) # Student ID or Employee ID
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False) # "Present", "Absent", "Leave"

    def __repr__(self):
        return f'<Attendance {self.entity_type} #{self.entity_id} on {self.date}: {self.status}>'
