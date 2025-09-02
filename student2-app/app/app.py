from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import random
import re
from datetime import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongo:27017/studentdb"
app.secret_key = 'supersecretkey'
mongo = PyMongo(app)

# Helper to generate unique student ID

def generate_student_id():
    while True:
        student_id = random.randint(10001, 99999)
        if not mongo.db.students.find_one({"student_id": student_id}):
            return student_id

def valid_name(name):
    return bool(re.match(r"^[A-Za-z]{2,}$", name))

def valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

@app.route('/')
def index():
    students = list(mongo.db.students.find())
    return render_template('index.html', students=students)

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        dob = request.form.get('dob', '').strip()
        address = request.form.get('address', '').strip()
        sex = request.form.get('sex', 'Male')

        # Validation
        errors = []
        if not valid_name(first_name):
            errors.append('First name must be at least 2 characters and alphabetic.')
        if last_name and not valid_name(last_name):
            errors.append('Last name must be at least 2 characters and alphabetic.')
        if not last_name:
            errors.append('Last name is required.')
        if not valid_date(dob):
            errors.append('Date of birth must be a valid date (YYYY-MM-DD).')
        if sex not in ['Male', 'Female', 'Other']:
            errors.append('Sex must be Male, Female, or Other.')
        if mongo.db.students.find_one({"first_name": first_name, "last_name": last_name, "dob": dob}):
            errors.append('Student record already exists.')
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('add_student.html', form={})
        student_id = generate_student_id()
        mongo.db.students.insert_one({
            "student_id": student_id,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "dob": dob,
            "address": address,
            "sex": sex
        })
        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_student.html', form={})

@app.route('/delete/<student_id>', methods=['POST'])
def delete_student(student_id):
    mongo.db.students.delete_one({"student_id": int(student_id)})
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = mongo.db.students.find_one({"student_id": int(student_id)})
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        dob = request.form.get('dob', '').strip()
        address = request.form.get('address', '').strip()
        sex = request.form.get('sex', 'Male')
        errors = []
        if not valid_name(first_name):
            errors.append('First name must be at least 2 characters and alphabetic.')
        if last_name and not valid_name(last_name):
            errors.append('Last name must be at least 2 characters and alphabetic.')
        if not last_name:
            errors.append('Last name is required.')
        if not valid_date(dob):
            errors.append('Date of birth must be a valid date (YYYY-MM-DD).')
        if sex not in ['Male', 'Female', 'Other']:
            errors.append('Sex must be Male, Female, or Other.')
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('edit_student.html', student=student, form=request.form)
        mongo.db.students.update_one({"student_id": int(student_id)}, {"$set": {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "dob": dob,
            "address": address,
            "sex": sex
        }})
        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_student.html', student=student, form={})

@app.route('/report')
def report():
    students = list(mongo.db.students.find())
    return render_template('report.html', students=students)

# REST API endpoints
@app.route('/api/students', methods=['GET'])
def api_get_students():
    students = list(mongo.db.students.find({}, {'_id': 0}))
    return jsonify(students)

@app.route('/api/student', methods=['POST'])
def api_add_student():
    data = request.json
    # Validation as above
    # ...
    return jsonify({'status': 'not implemented'}), 501

@app.route('/api/student/<int:student_id>', methods=['PUT', 'DELETE'])
def api_modify_student(student_id):
    # Implement update and delete logic
    return jsonify({'status': 'not implemented'}), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
