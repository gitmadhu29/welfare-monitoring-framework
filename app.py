from flask import Flask, request, jsonify, render_template
from models import db, Beneficiary, Scheme, Allocation, AdminUser
from ml.fraud_detection import check_duplicate
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///welfare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.form
    name = data.get('name')
    address = data.get('address')
    id_number = data.get('id_number')
    scheme_name = data.get('scheme')

    is_duplicate, matched_with = check_duplicate(name, address, id_number)

    beneficiary = Beneficiary(
        name=name,
        address=address,
        id_number=id_number,
        scheme=scheme_name,
        status='Flagged - Duplicate' if is_duplicate else 'Approved'
    )
    db.session.add(beneficiary)
    db.session.commit()

    if not is_duplicate:
        allocation = Allocation(beneficiary_id=beneficiary.id, scheme=scheme_name, amount=1000)
        db.session.add(allocation)
        db.session.commit()

    return render_template('status.html', beneficiary=beneficiary, is_duplicate=is_duplicate, matched_with=matched_with)


@app.route('/status/<int:beneficiary_id>')
def status(beneficiary_id):
    beneficiary = Beneficiary.query.get_or_404(beneficiary_id)
    return render_template('status.html', beneficiary=beneficiary, is_duplicate=(beneficiary.status.startswith('Flagged')), matched_with=None)


@app.route('/admin/dashboard')
def admin_dashboard():
    total = Beneficiary.query.count()
    flagged = Beneficiary.query.filter(Beneficiary.status.like('Flagged%')).count()
    approved = Beneficiary.query.filter_by(status='Approved').count()
    all_beneficiaries = Beneficiary.query.all()
    return render_template('dashboard.html', total=total, flagged=flagged, approved=approved, beneficiaries=all_beneficiaries)


@app.route('/api/beneficiaries')
def api_beneficiaries():
    beneficiaries = Beneficiary.query.all()
    return jsonify([{
        'id': b.id, 'name': b.name, 'scheme': b.scheme, 'status': b.status
    } for b in beneficiaries])


if __name__ == '__main__':
    app.run(debug=True)