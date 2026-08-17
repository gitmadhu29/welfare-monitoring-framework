"""
Generates synthetic beneficiary data for testing, with intentional duplicates.
Usage:
    python3 data/generate_data.py            -> generates 1000 records
    python3 data/generate_data.py 5000        -> generates 5000 records
"""
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from app import app
from models import db, Beneficiary

fake = Faker('en_IN')
SCHEMES = ['Scholarship', 'Pension', 'Food Ration', 'Subsidy']
BATCH_SIZE = 1000


def generate_records(n, duplicate_rate=0.05):
    records = []
    fake.unique.clear()

    for _ in range(n):
        records.append({
            'name': fake.name(),
            'address': fake.address().replace('\n', ', '),
            'id_number': fake.unique.numerify('##########'),
            'scheme': random.choice(SCHEMES),
        })

    num_duplicates = int(n * duplicate_rate)
    base_pool = records[:n] if n > 0 else []
    for _ in range(num_duplicates):
        if not base_pool:
            break
        original = random.choice(base_pool)
        duplicate = original.copy()
        duplicate['name'] = original['name'].replace('a', 'a ').strip()
        records.append(duplicate)

    random.shuffle(records)
    return records


def bulk_insert(records):
    total = len(records)
    for i in range(0, total, BATCH_SIZE):
        chunk = records[i:i + BATCH_SIZE]
        objs = [
            Beneficiary(
                name=r['name'],
                address=r['address'],
                id_number=r['id_number'],
                scheme=r['scheme'],
                status='Pending'
            )
            for r in chunk
        ]
        db.session.bulk_save_objects(objs)
        db.session.commit()
        print(f"  Inserted {min(i + BATCH_SIZE, total)}/{total}...")


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

    with app.app_context():
        db.drop_all()
        db.create_all()

        print(f"Generating {n} synthetic beneficiary records...")
        data = generate_records(n)

        print(f"Inserting {len(data)} records into database...")
        bulk_insert(data)

        print(f"Done. Inserted {len(data)} records total.")