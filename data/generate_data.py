import sys
import os
# Add the parent directory to the path so it can find app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import app, db
from models import (Beneficiary, Scheme, ScholarshipApplication,
                    PensionApplication, RationApplication, SubsidyApplication, Officer)


SCHEMES = [
    {"name": "Post-Matric Scholarship", "category": "Student",
     "description": "For college students of weaker sections",
     "eligibility": "Family income < 2.5 LPA, age 15-35"},
    {"name": "Indira Gandhi National Old Age Pension", "category": "Senior Citizen",
     "description": "Monthly pension for elderly BPL",
     "eligibility": "Age 60+, BPL"},
    {"name": "National Food Security Act (PDS)", "category": "BPL",
     "description": "Subsidized food grains via Fair Price Shops",
     "eligibility": "BPL / Antyodaya families"},
    {"name": "PM Ujjwala Yojana (LPG)", "category": "General",
     "description": "Free LPG connection to women of BPL families",
     "eligibility": "Annual income < 3 LPA"},
    {"name": "Electricity Subsidy", "category": "General",
     "description": "Subsidized electricity bills",
     "eligibility": "Annual income < 3 LPA"},
]

COURSES = ["10th Grade", "12th Grade", "B.Tech", "B.A.", "B.Sc", "B.Com", "M.A.", "M.Tech"]
STATES = ["Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh",
          "Delhi", "West Bengal", "Gujarat", "Rajasthan"]
RATION_TYPES = ["BPL", "APL", "Antyodaya Anna Yojana"]
FIRST_NAMES = ["Aarav","Priya","Rahul","Sneha","Mohit","Anjali","Vikram","Kavya",
               "Suresh","Meena","Ramesh","Geeta"]
LAST_NAMES = ["Sharma","Patel","Reddy","Iyer","Singh","Nair","Gupta","Das","Khan","Bose"]

def rand_aadhaar():
    return ''.join(str(random.randint(0,9)) for _ in range(12))

def rand_phone():
    return ''.join(str(random.randint(0,9)) for _ in range(10))

def rand_dob(min_age, max_age):
    today = date.today()
    return today - timedelta(days=random.randint(min_age*365, max_age*365))

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def gen_beneficiaries(n=60):
    out = []
    used_aadhaar = set()
    
    # Counters for User IDs
    counters = {"Student": 1, "Senior Citizen": 1, "BPL": 1, "General": 1}
    
    for i in range(n):
        cat = random.choices(["Student","Senior Citizen","BPL","General"],
                             weights=[40,20,25,15])[0]
        
        # Generate User ID based on category
        if cat == "Student":          prefix = "SCH"
        elif cat == "Senior Citizen": prefix = "PEN"
        elif cat == "BPL":            prefix = "BPL"
        else:                         prefix = "GEN"
        
        user_id = f"{prefix}-2024-{counters[cat]:03d}"
        counters[cat] += 1

        if cat == "Student":          dob = rand_dob(17, 30)
        elif cat == "Senior Citizen": dob = rand_dob(60, 88)
        else:                         dob = rand_dob(28, 60)

        while True:
            aad = rand_aadhaar()
            if aad not in used_aadhaar:
                used_aadhaar.add(aad); break

        out.append(Beneficiary(
            user_id=user_id,
            full_name=rand_name(),
            aadhaar_number=aad,
            date_of_birth=dob,
            gender=random.choice(["Male","Female"]),
            phone=rand_phone(),
            email=f"user{i+1:03d}@mail.com", # Email for login
            address=f"House {i+1}, Lane {random.randint(1,30)}, {random.choice(STATES)}",
            state=random.choice(STATES),
            district=f"District_{random.randint(1,12)}",
            category=cat,
            annual_income=random.choice([60000, 120000, 180000, 250000, 400000]),
            bank_account_number=''.join(str(random.randint(0,9)) for _ in range(14)),
            ifsc_code=f"SBIN0{random.randint(10000,99999)}",
            password_hash=generate_password_hash("password123") # Default password for fake users
        ))
    return out

def gen_apps(benes, schemes):
    s=p=r=su=0
    for b in benes:
        cat = b.category

        if cat == "Student":
            sch = next(x for x in schemes if x.name == "Post-Matric Scholarship")
            app_obj = ScholarshipApplication(
                application_id=f"SCH-2024-{s+1:04d}",
                beneficiary=b, scheme=sch,
                student_id=f"STU{random.randint(100000,999999)}",
                guardian_name=f"Guardian of {b.full_name}",
                institution_name=f"College_{random.randint(1,20)}",
                course_degree=random.choice(COURSES),
                academic_year="2023-2024",
                previous_year_marks_percentage=round(random.uniform(55,95),2),
                annual_family_income=b.annual_income,
                status=random.choices(["Pending","Approved","Flagged","Rejected"],
                                      weights=[40,40,10,10])[0]
            )
            db.session.add(app_obj) # <--- ADDED THIS
            s+=1

        elif cat == "Senior Citizen":
            sch = next(x for x in schemes if "Pension" in x.name)
            app_obj = PensionApplication(
                application_id=f"PEN-2024-{p+1:04d}",
                beneficiary=b, scheme=sch,
                pensioner_id=f"PEN{random.randint(100000,999999)}",
                retirement_date=rand_dob(58,75) if random.random()>0.3 else None,
                previous_employer_details=random.choice(
                    ["Retired from Pvt Ltd","Retired Govt Employee","Unorganized Worker"]),
                spouse_name=f"Spouse of {b.full_name}",
                age_verified=True,
                status=random.choices(["Pending","Approved","Flagged"],
                                      weights=[40,50,10])[0]
            )
            db.session.add(app_obj) # <--- ADDED THIS
            p+=1

        elif cat == "BPL":
            sch = next(x for x in schemes if "Food Security" in x.name)
            app_obj = RationApplication(
                application_id=f"RAT-2024-{r+1:04d}",
                beneficiary=b, scheme=sch,
                ration_card_number=f"RC{random.randint(10000000,99999999)}",
                ration_card_type=random.choice(RATION_TYPES),
                total_family_members=random.randint(2,8),
                income_certificate_number=f"IC{random.randint(100000,999999)}",
                assigned_fps_shop_id=f"FPS-{random.randint(1,100):03d}",
                status=random.choices(["Pending","Approved","Flagged"],
                                      weights=[40,50,10])[0]
            )
            db.session.add(app_obj) # <--- ADDED THIS
            r+=1

        # General OR BPL can also apply for subsidy
        if cat in ("General","BPL"):
            sch = next(x for x in schemes if "Ujjwala" in x.name)
            app_obj = SubsidyApplication(
                application_id=f"SUB-2024-{su+1:04d}",
                beneficiary=b, scheme=sch,
                subsidy_type="LPG Cooking Gas",
                connection_number=f"LPG{random.randint(10000000,99999999)}",
                linked_bank_account=b.bank_account_number,
                annual_income=b.annual_income,
                status=random.choices(["Pending","Approved","Flagged"],
                                      weights=[40,50,10])[0]
            )
            db.session.add(app_obj) 
            su+=1

    print(f"Generated: Scholarship={s}, Pension={p}, Ration={r}, Subsidy={su}")
def gen_officers():
    return [
        Officer(username="admin",           password_hash=generate_password_hash("admin123"),
                full_name="System Admin",      department="All",        role="Admin"),
        Officer(username="edu_officer",      password_hash=generate_password_hash("edu123"),
                full_name="Education Officer", department="Education"),
        Officer(username="pension_officer",  password_hash=generate_password_hash("pen123"),
                full_name="Pension Officer",   department="Pension"),
        Officer(username="food_officer",     password_hash=generate_password_hash("food123"),
                full_name="Food & PDS Officer",department="Food & PDS"),
        # NEW OFFICER FOR SUBSIDIES:
        Officer(username="subsidy_officer",  password_hash=generate_password_hash("sub123"),
                full_name="Subsidy Officer",  department="Subsidy"),
    ]
def main():
    with app.app_context():
        db.drop_all()
        db.create_all()

        schemes = [Scheme(**s) for s in SCHEMES]
        db.session.add_all(schemes); db.session.commit()

        benes = gen_beneficiaries(60)
        db.session.add_all(benes); db.session.commit()

        gen_apps(benes, schemes)

        db.session.add_all(gen_officers())
        db.session.commit()
        print("✅ Database seeded: 60 citizens + 4 scheme tables + officers.")

if __name__ == "__main__":
    main()