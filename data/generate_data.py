"""
Generates synthetic beneficiary data for testing, with intentional duplicates.

Usage:
    python3 data/generate_data.py
    python3 data/generate_data.py 500
    python3 data/generate_data.py 5000
"""

import sys
import os
import random

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from faker import Faker
from app import app
from models import db, Beneficiary

fake = Faker('en_IN')

SCHEMES = [
    'Scholarship',
    'Pension',
    'Food Ration',
    'Subsidy'
]

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
            'is_duplicate': False
        })

    num_duplicates = int(n * duplicate_rate)
    base_pool = records.copy()

    for _ in range(num_duplicates):
        if not base_pool:
            break

        original = random.choice(base_pool)

        duplicate = original.copy()

        duplicate['id_number'] = original['id_number']
        duplicate['address'] = original['address']
        duplicate['scheme'] = original['scheme']

        if len(original['name']) > 3:
            duplicate['name'] = original['name'] + ' '
        else:
            duplicate['name'] = original['name']

        duplicate['is_duplicate'] = True

        records.append(duplicate)

    random.shuffle(records)

    return records


def bulk_insert(records):
    total = len(records)

    for i in range(0, total, BATCH_SIZE):
        chunk = records[i:i + BATCH_SIZE]

        objects = []

        for record in chunk:

            if record['is_duplicate']:
                status = 'Flagged'
            else:
                status = random.choices(
                    ['Approved', 'Pending'],
                    weights=[85, 15],
                    k=1
                )[0]

            beneficiary = Beneficiary(
                name=record['name'],
                address=record['address'],
                id_number=record['id_number'],
                scheme=record['scheme'],
                status=status
            )

            objects.append(beneficiary)

        db.session.bulk_save_objects(objects)
        db.session.commit()

        print(
            f"  Inserted "
            f"{min(i + BATCH_SIZE, total)}/{total}..."
        )


if __name__ == '__main__':

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

    if n <= 0:
        print("Error: Number of records must be greater than 0.")
        sys.exit(1)

    print("Welfare Monitoring Framework")
    print("Synthetic Data Generator")
    print()

    print(f"Generating {n} synthetic beneficiary records...")

    data = generate_records(n)

    duplicate_count = sum(
        1 for record in data
        if record['is_duplicate']
    )

    normal_count = len(data) - duplicate_count

    print(f"Normal records: {normal_count}")
    print(f"Duplicate records: {duplicate_count}")

    with app.app_context():

        db.drop_all()
        db.create_all()

        print("Database recreated successfully.")
        print(f"Inserting {len(data)} records...")

        bulk_insert(data)

        approved_count = Beneficiary.query.filter_by(
            status='Approved'
        ).count()

        pending_count = Beneficiary.query.filter_by(
            status='Pending'
        ).count()

        flagged_count = Beneficiary.query.filter_by(
            status='Flagged'
        ).count()

        print()
        print("DATA GENERATION COMPLETE")
        print(f"Total records : {len(data)}")
        print(f"Approved      : {approved_count}")
        print(f"Pending       : {pending_count}")
        print(f"Flagged       : {flagged_count}")