import random
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from models import (db, Beneficiary, Scheme, ScholarshipApplication, 
                    PensionApplication, RationApplication, SubsidyApplication, 
                    Officer, FraudLog)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///welfare.db'
app.config['SECRET_KEY'] = 'super_secret_key_123'
db.init_app(app)

SCHEME_CATEGORY_MAP = {
    "Post-Matric Scholarship":               "Student",
    "Indira Gandhi National Old Age Pension": "Senior Citizen",
    "National Food Security Act (PDS)":      "BPL",
    "PM Ujjwala Yojana (LPG)":               "General",
    "Electricity Subsidy":                    "General",
}

def _gen_app_id(prefix):
    return f"{prefix}-2024-{random.randint(1000,9999)}"

def _calc_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# ---------------- HOME PAGE ----------------
@app.route('/')
def index():
    # If the user is already logged in, send them straight to their Dashboard!
    if 'citizen_id' in session:
        return redirect(url_for('citizen_dashboard'))
        
    # If not logged in, show the public Home Page with all schemes
    schemes = Scheme.query.all()
    return render_template('index.html', schemes=schemes)

# ========================================================
# CITIZEN AUTHENTICATION ROUTES (Strict Category Mapping)
# ========================================================

# ---------------- CITIZEN REGISTER ----------------
@app.route('/citizen_register', methods=['GET', 'POST'])
def citizen_register():
    schemes = Scheme.query.all()
    
    if request.method == 'POST':
        scheme_id = request.form.get('scheme_id')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        aadhaar = request.form.get('aadhaar_number', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        phone = request.form.get('phone', '').strip()

        scheme = Scheme.query.get(scheme_id)
        if not scheme:
            flash("Please select a valid scheme.")
            return redirect(url_for('citizen_register'))

        if not full_name or len(password) < 6:
            flash("Name is required and password must be at least 6 characters.")
            return redirect(url_for('citizen_register'))
        
        if Beneficiary.query.filter_by(email=email).first():
            flash("Email already registered. Please login.")
            return redirect(url_for('citizen_login'))
            
        if Beneficiary.query.filter_by(aadhaar_number=aadhaar).first():
            flash("Aadhaar already registered. Please login.")
            return redirect(url_for('citizen_login'))

        auto_category = scheme.category
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        age = _calc_age(dob)

        if auto_category == "Senior Citizen" and age < 60:
            flash("You must be 60+ years old to apply for this scheme.")
            return redirect(url_for('citizen_register'))
        if auto_category == "Student" and not (15 <= age <= 35):
            flash("You must be between 15-35 years old to apply for this scheme.")
            return redirect(url_for('citizen_register'))

        prefix = auto_category[0:3].upper() if auto_category != "Senior Citizen" else "PEN"
        count = Beneficiary.query.filter(Beneficiary.user_id.like(f"{prefix}-2024-%")).count()
        user_id = f"{prefix}-2024-{count + 1:04d}"

        new_user = Beneficiary(
            user_id=user_id,
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            aadhaar_number=aadhaar,
            date_of_birth=dob,
            phone=phone,
            category=auto_category,
        )
        db.session.add(new_user)
        db.session.commit()

        # Redirect to the success page to show the ID to copy
        return redirect(url_for('registration_success', user_id=user_id))

    return render_template('citizen_register.html', schemes=schemes)

# ---------------- REGISTRATION SUCCESS ----------------
@app.route('/registration_success/<user_id>')
def registration_success(user_id):
    return render_template('registration_success.html', user_id=user_id)

# ---------------- CITIZEN LOGIN ----------------
@app.route('/citizen_login', methods=['GET', 'POST'])
def citizen_login():
    # Check if scheme_id was passed in the URL (Scenario 2)
    scheme_id = request.args.get('scheme_id') or request.form.get('scheme_id')
    scheme = Scheme.query.get(scheme_id) if scheme_id else None
    
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()

        user = Beneficiary.query.filter(
            (Beneficiary.email == login_id) | (Beneficiary.user_id == login_id)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            # SCENARIO 2 CHECK: Did they click a specific scheme?
            if scheme:
                # Strict mapping check
                if user.category != scheme.category:
                    flash(f"Access Denied! Your account is mapped to {user.category} schemes, but you selected {scheme.name}.")
                    return redirect(url_for('citizen_login', scheme_id=scheme_id))
            
            # If they pass the check (or if it's Scenario 1), log them in and go to Dashboard
            session['citizen_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('citizen_dashboard'))
        else:
            flash('Invalid login ID or password.')

    return render_template('citizen_login.html', scheme=scheme)
@app.route('/citizen_dashboard')
def citizen_dashboard():
    if 'citizen_id' not in session:
        flash('Please login to access your dashboard.')
        return redirect(url_for('citizen_login'))

    user = Beneficiary.query.get(session['citizen_id'])
    
    # Get ALL schemes that match the user's category (not just the first one)
    schemes = Scheme.query.filter_by(category=user.category).all()
    
    # Fetch all applications this user has ever submitted
    scholarships = ScholarshipApplication.query.filter_by(beneficiary_id=user.id).all()
    pensions = PensionApplication.query.filter_by(beneficiary_id=user.id).all()
    rations = RationApplication.query.filter_by(beneficiary_id=user.id).all()
    subsidies = SubsidyApplication.query.filter_by(beneficiary_id=user.id).all()
    
    return render_template('citizen_dashboard.html', 
                           user=user, 
                           schemes=schemes,
                           scholarships=scholarships,
                           pensions=pensions,
                           rations=rations,
                           subsidies=subsidies)
# ---------------- APPLY FOR SCHEME ----------------
@app.route('/apply/<int:scheme_id>', methods=['GET', 'POST'])
def apply_scheme(scheme_id):
    if 'citizen_id' not in session:
        flash('Please login to apply for this scheme.')
        return redirect(url_for('citizen_login', scheme_id=scheme_id))
        
    user = Beneficiary.query.get(session['citizen_id'])
    scheme = Scheme.query.get_or_404(scheme_id)
    
    if user.category != scheme.category:
        flash(f"Access Denied! You can only apply for {user.category} schemes.")
        return redirect(url_for('citizen_dashboard'))
    
    if request.method == 'POST':
        user.address = request.form.get('address', '').strip()
        user.state = request.form.get('state', '').strip()
        user.district = request.form.get('district', '').strip()
        user.annual_income = float(request.form.get('annual_income', 0))
        user.bank_account_number = request.form.get('bank_account_number', '').strip()
        user.ifsc_code = request.form.get('ifsc_code', '').strip()
        
        fraud_reasons = []
        current_status = "Pending"
        if user.category in ["BPL", "General"] and user.annual_income > 300000:
            fraud_reasons.append(f"Income {user.annual_income} exceeds limit for {scheme.name}.")
        if fraud_reasons:
            current_status = "Flagged"
            flash("⚠️ FRAUD DETECTED! Application flagged for review.")

        app_id = _gen_app_id(scheme.name[0:3].upper())
        
        if scheme.name == "Post-Matric Scholarship":
            application = ScholarshipApplication(
                application_id=app_id, beneficiary_id=user.id, scheme_id=scheme.id,
                student_id=request.form.get('student_id','').strip(),
                guardian_name=request.form.get('guardian_name','').strip(),
                institution_name=request.form.get('institution_name','').strip(),
                course_degree=request.form.get('course_degree','').strip(),
                academic_year=request.form.get('academic_year','').strip(),
                previous_year_marks_percentage=float(request.form.get('marks','0') or 0),
                annual_family_income=user.annual_income, status=current_status)
                
        elif "Pension" in scheme.name:
            ret_str = request.form.get('retirement_date','').strip()
            application = PensionApplication(
                application_id=app_id, beneficiary_id=user.id, scheme_id=scheme.id,
                pensioner_id=request.form.get('pensioner_id','').strip(),
                retirement_date=datetime.strptime(ret_str,'%Y-%m-%d').date() if ret_str else None,
                previous_employer_details=request.form.get('previous_employer','').strip() or "Unorganized Worker",
                spouse_name=request.form.get('spouse_name','').strip(), age_verified=True, status=current_status)
                
        elif "Food Security" in scheme.name:
            application = RationApplication(
                application_id=app_id, beneficiary_id=user.id, scheme_id=scheme.id,
                ration_card_number=request.form.get('ration_card_number','').strip(),
                ration_card_type=request.form.get('ration_card_type','').strip(),
                total_family_members=int(request.form.get('family_members','1') or 1),
                income_certificate_number=request.form.get('income_certificate','').strip(),
                assigned_fps_shop_id=f"FPS-{random.randint(1,100):03d}", status=current_status)
        else:
            application = SubsidyApplication(
                application_id=app_id, beneficiary_id=user.id, scheme_id=scheme.id,
                subsidy_type=request.form.get('subsidy_type','LPG Cooking Gas').strip(),
                connection_number=request.form.get('connection_number','').strip(),
                linked_bank_account=user.bank_account_number, annual_income=user.annual_income, status=current_status)

        db.session.add(application)
        db.session.flush() 

        if fraud_reasons:
            for reason in fraud_reasons:
                new_log = FraudLog(aadhaar_number=user.aadhaar_number, application_id=app_id, reason=reason, severity="High")
                db.session.add(new_log)

        db.session.commit()
        flash(f"Application submitted successfully! Your Application ID: {app_id}")
        return redirect(url_for('citizen_dashboard'))

    return render_template('apply_scheme.html', user=user, scheme=scheme)

# ========================================================
# OFFICER ROUTES
# ========================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        officer = Officer.query.filter_by(username=username).first()
        
        if officer and check_password_hash(officer.password_hash, password):
            session['officer_id'] = officer.id
            session['officer_name'] = officer.full_name
            session['role'] = officer.role
            session['department'] = officer.department # <--- SAVES DEPARTMENT
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'officer_id' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))
    
    # Get the department of the logged-in officer
    department = session.get('department')
    role = session.get('role')
    
    # Default empty lists
    scholarships, pensions, rations, subsidies = [], [], [], []

    # If Admin, fetch everything
    if role == 'Admin' or department == 'All':
        scholarships = ScholarshipApplication.query.all()
        pensions = PensionApplication.query.all()
        rations = RationApplication.query.all()
        subsidies = SubsidyApplication.query.all()
    elif department == 'Education':
        scholarships = ScholarshipApplication.query.all()
    elif department == 'Pension':
        pensions = PensionApplication.query.all()
    elif department == 'Food & PDS':
        rations = RationApplication.query.all()
        subsidies = SubsidyApplication.query.all() # Food officer handles subsidies too
    elif department == 'Subsidy':
        subsidies = SubsidyApplication.query.all()
    
    return render_template('dashboard.html', 
                           scholarships=scholarships,
                           pensions=pensions,
                           rations=rations,
                           subsidies=subsidies,
                           officer_department=department)
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))


@app.route('/fraud_logs')
def fraud_logs():
    if 'officer_id' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))
    
    department = session.get('department')
    role = session.get('role')
    
    logs = []
    
    # Admin sees everything
    if role == 'Admin' or department == 'All':
        logs = FraudLog.query.order_by(FraudLog.detected_at.desc()).all()
    # Education Officer sees only Scholarship frauds (SCH-)
    elif department == 'Education':
        logs = FraudLog.query.filter(FraudLog.application_id.like('SCH-%')).order_by(FraudLog.detected_at.desc()).all()
    # Pension Officer sees only Pension frauds (PEN-)
    elif department == 'Pension':
        logs = FraudLog.query.filter(FraudLog.application_id.like('PEN-%')).order_by(FraudLog.detected_at.desc()).all()
    # Food Officer sees Ration (RAT-) and Subsidy (SUB-) frauds
    elif department == 'Food & PDS':
        logs = FraudLog.query.filter(
            (FraudLog.application_id.like('RAT-%')) | (FraudLog.application_id.like('SUB-%'))
        ).order_by(FraudLog.detected_at.desc()).all()
    # Subsidy Officer sees only Subsidy frauds (SUB-)
    elif department == 'Subsidy':
        logs = FraudLog.query.filter(FraudLog.application_id.like('SUB-%')).order_by(FraudLog.detected_at.desc()).all()
    
    return render_template('fraud_logs.html', logs=logs)
@app.route('/update_status/<app_type>/<int:app_id>/<status>', methods=['POST'])
def update_status(app_type, app_id, status):
    if 'officer_id' not in session:
        return redirect(url_for('login'))
        
    app_obj = None
    if app_type == 'scholarship':
        app_obj = ScholarshipApplication.query.get(app_id)
    elif app_type == 'pension':
        app_obj = PensionApplication.query.get(app_id)
    elif app_type == 'ration':
        app_obj = RationApplication.query.get(app_id)
    elif app_type == 'subsidy':
        app_obj = SubsidyApplication.query.get(app_id)
        
    if app_obj:
        app_obj.status = status
        app_obj.processed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Application {app_obj.application_id} has been {status}.')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)