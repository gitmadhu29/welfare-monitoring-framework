from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------- Master Scheme table ----------
class Scheme(db.Model):
    __tablename__ = 'schemes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)   # Student / Senior Citizen / BPL / General
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scholarship_apps = db.relationship('ScholarshipApplication', backref='scheme', lazy=True)
    pension_apps     = db.relationship('PensionApplication',     backref='scheme', lazy=True)
    ration_apps      = db.relationship('RationApplication',       backref='scheme', lazy=True)
    subsidy_apps    = db.relationship('SubsidyApplication',       backref='scheme', lazy=True)

# ---------- Beneficiary (master citizen credentials) ----------
class Beneficiary(db.Model):
    __tablename__ = 'beneficiaries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name            = db.Column(db.String(150), nullable=False)
    aadhaar_number       = db.Column(db.String(12),  unique=True, nullable=False, index=True)
    date_of_birth        = db.Column(db.Date, nullable=False)
    gender               = db.Column(db.String(10))
    phone                = db.Column(db.String(10))
    email                = db.Column(db.String(120), unique=True, nullable=False)
    address              = db.Column(db.Text)
    state                = db.Column(db.String(50))
    district             = db.Column(db.String(50))
    category             = db.Column(db.String(50), nullable=False)
    annual_income        = db.Column(db.Float)
    bank_account_number  = db.Column(db.String(20))
    ifsc_code            = db.Column(db.String(11))
    password_hash        = db.Column(db.String(255), nullable=False)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

    scholarship_apps = db.relationship('ScholarshipApplication', backref='beneficiary', lazy=True, cascade='all, delete-orphan')
    pension_apps     = db.relationship('PensionApplication',     backref='beneficiary', lazy=True, cascade='all, delete-orphan')
    ration_apps      = db.relationship('RationApplication',       backref='beneficiary', lazy=True, cascade='all, delete-orphan')
    subsidy_apps    = db.relationship('SubsidyApplication',       backref='beneficiary', lazy=True, cascade='all, delete-orphan')

# ---------- 1. Scholarship ----------
class ScholarshipApplication(db.Model):
    __tablename__ = 'scholarship_applications'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(25), unique=True, nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False)
    scheme_id      = db.Column(db.Integer, db.ForeignKey('schemes.id'),       nullable=False)

    student_id                          = db.Column(db.String(50),  nullable=False)
    guardian_name                       = db.Column(db.String(150), nullable=False)
    institution_name                    = db.Column(db.String(200), nullable=False)
    course_degree                       = db.Column(db.String(100), nullable=False)
    academic_year                       = db.Column(db.String(20),  nullable=False)
    previous_year_marks_percentage      = db.Column(db.Float,       nullable=False)
    annual_family_income                = db.Column(db.Float,        nullable=False)
    status        = db.Column(db.String(20), default='Pending')
    applied_at    = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at  = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text) 
    amount_allocated = db.Column(db.Float, default=0)
    remarks       = db.Column(db.Text)

# ---------- 2. Pension ----------
class PensionApplication(db.Model):
    __tablename__ = 'pension_applications'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(25), unique=True, nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False)
    scheme_id      = db.Column(db.Integer, db.ForeignKey('schemes.id'),       nullable=False)

    pensioner_id                  = db.Column(db.String(50), nullable=False)
    retirement_date              = db.Column(db.Date)
    previous_employer_details    = db.Column(db.String(255))
    spouse_name                  = db.Column(db.String(150))
    age_verified                 = db.Column(db.Boolean, default=False)
    status        = db.Column(db.String(20), default='Pending')
    applied_at    = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at  = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text) 
    amount_allocated = db.Column(db.Float, default=0)
    remarks       = db.Column(db.Text)

# ---------- 3. Ration (PDS) ----------
class RationApplication(db.Model):
    __tablename__ = 'ration_applications'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(25), unique=True, nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False)
    scheme_id      = db.Column(db.Integer, db.ForeignKey('schemes.id'),       nullable=False)

    ration_card_number          = db.Column(db.String(20), nullable=False, unique=True)
    ration_card_type            = db.Column(db.String(50), nullable=False)
    total_family_members        = db.Column(db.Integer,   nullable=False)
    income_certificate_number   = db.Column(db.String(50))
    assigned_fps_shop_id        = db.Column(db.String(50))
    status        = db.Column(db.String(20), default='Pending')
    applied_at    = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at  = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text) 
    amount_allocated = db.Column(db.Float, default=0)
    remarks       = db.Column(db.Text)

# ---------- 4. Subsidy (LPG / Electricity) ----------
class SubsidyApplication(db.Model):
    __tablename__ = 'subsidy_applications'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.String(25), unique=True, nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiaries.id'), nullable=False)
    scheme_id      = db.Column(db.Integer, db.ForeignKey('schemes.id'),       nullable=False)

    subsidy_type          = db.Column(db.String(50), nullable=False)
    connection_number     = db.Column(db.String(50), nullable=False)
    linked_bank_account   = db.Column(db.String(20), nullable=False)
    annual_income         = db.Column(db.Float,      nullable=False)
    status        = db.Column(db.String(20), default='Pending')
    applied_at    = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at  = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text) 
    amount_allocated = db.Column(db.Float, default=0)
    remarks       = db.Column(db.Text)

# ---------- Officer (for admin login later) ----------
class Officer(db.Model):
    __tablename__ = 'officers'
    id = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    department    = db.Column(db.String(100))
    role          = db.Column(db.String(20), default='Officer')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Fraud Log ----------
class FraudLog(db.Model):
    __tablename__ = 'fraud_logs'
    id = db.Column(db.Integer, primary_key=True)
    aadhaar_number = db.Column(db.String(12), nullable=False, index=True)
    application_id = db.Column(db.String(25))
    reason         = db.Column(db.Text, nullable=False)
    severity       = db.Column(db.String(20), default='High')
    detected_at    = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Government Fund/Budget Tracking ----------
class SchemeFund(db.Model):
    __tablename__ = 'scheme_funds'
    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('schemes.id'), nullable=False)
    total_budget = db.Column(db.Float, nullable=False)          # Total govt allocation
    allocated_amount = db.Column(db.Float, default=0)           # Amount given to approved apps
    pending_amount = db.Column(db.Float, default=0)             # Amount in pending applications
    per_beneficiary_amount = db.Column(db.Float, nullable=False) # e.g., ₹25,000 per student
    financial_year = db.Column(db.String(10), default='2024-2025')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    scheme = db.relationship('Scheme', backref='fund')