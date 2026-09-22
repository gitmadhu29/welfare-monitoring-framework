import pandas as pd
from sklearn.ensemble import IsolationForest
import sys
import os
from datetime import date

# Add parent directory to path to find app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_training_data():
    """Fetches all beneficiaries and converts to a numeric matrix for the AI"""
    # LAZY IMPORTS: Import inside the function to avoid circular import errors
    from app import app, db
    from models import Beneficiary
    
    with app.app_context():
        benes = Beneficiary.query.all()
        data = []
        
        for b in benes:
            cat_map = {"Student": 1, "Senior Citizen": 2, "BPL": 3, "General": 4}
            age = date.today().year - b.date_of_birth.year
            
            row = {
                "age": age,
                "income": b.annual_income,
                "category_code": cat_map.get(b.category, 0),
                "has_bank_account": 1 if b.bank_account_number else 0
            }
            data.append(row)
            
        return pd.DataFrame(data)

def train_model():
    """Trains the Isolation Forest model"""
    print("🔄 Training AI Fraud Detection Model...")
    df = get_training_data()
    
    if df.empty:
        print("⚠️ No data to train on!")
        return None
        
    model = IsolationForest(contamination=0.15, random_state=42)
    model.fit(df)
    print("✅ AI Model Trained Successfully!")
    return model

if __name__ == "__main__":
    train_model()