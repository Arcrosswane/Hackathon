import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, School
from app.utils.decorators import login_required, role_required

school_bp = Blueprint('school', __name__, url_prefix='/admin')

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@school_bp.route('/school', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def setup():
    school = School.query.first()
    is_new = school is None

    if request.method == 'POST':
        school_name = request.form.get('school_name', '').strip() or request.form.get('name', '').strip()
        school_code = request.form.get('school_code', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        website = request.form.get('website', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        academic_session = request.form.get('academic_session', '').strip()

        # Server-side Validations
        errors = []
        if not school_name:
            errors.append("Please enter a school name.")
        if not academic_session:
            errors.append("Please select or enter a current academic session.")
        if email and not EMAIL_REGEX.match(email):
            errors.append("Please enter a valid email address.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            # Create transient mock object for re-populating form on error
            form_data = {
                'name': school_name,
                'school_code': school_code,
                'email': email,
                'phone': phone,
                'website': website,
                'address': address,
                'city': city,
                'state': state,
                'country': country,
                'postal_code': postal_code,
                'academic_session': academic_session
            }
            return render_template('admin/school.html', school=form_data, is_new=is_new)

        if not school:
            school = School(
                name=school_name,
                school_code=school_code,
                email=email,
                phone=phone,
                website=website,
                address=address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                academic_session=academic_session
            )
            db.session.add(school)
            message = "School profile created successfully."
        else:
            school.name = school_name
            school.school_code = school_code
            school.email = email
            school.phone = phone
            school.website = website
            school.address = address
            school.city = city
            school.state = state
            school.country = country
            school.postal_code = postal_code
            school.academic_session = academic_session
            message = "School profile updated successfully."

        db.session.commit()
        flash(message, 'success')
        return redirect(url_for('school.setup'))

    return render_template('admin/school.html', school=school, is_new=is_new)
