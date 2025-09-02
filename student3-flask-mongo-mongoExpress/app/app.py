from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import datetime
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/studentdb')
client = MongoClient(mongo_uri)
db = client.get_database()
students = db.students

# Helper for unique student ID
def get_next_student_id():
    last = students.find_one(sort=[("student_id", -1)])
    if last and "student_id" in last:
        next_id = last["student_id"] + 1
    else:
        next_id = 10001
    if next_id > 99999:
        raise Exception("Student ID limit reached.")
    return next_id

# Validation helpers
def validate_student(data, is_new=True):
    errors = []
    # First Name
    if not data.get('first_name') or len(data['first_name']) < 2 or not re.match(r'^[A-Za-z0-9]+$', data['first_name']):
        errors.append('First Name must be at least 2 alphanumeric characters.')
    # Middle Name (optional)
    if data.get('middle_name') and not re.match(r'^[A-Za-z0-9]*$', data['middle_name']):
        errors.append('Middle Name must be alphanumeric.')
    # Last Name
    if not data.get('last_name') or len(data['last_name']) < 2 or not re.match(r'^[A-Za-z0-9]+$', data['last_name']):
        errors.append('Last Name must be at least 2 alphanumeric characters.')
    # DOB
    dob = data.get('dob', '01/01/2001')
    try:
        datetime.datetime.strptime(dob, '%d/%m/%Y')
    except Exception:
        errors.append('Date of Birth must be in DD/MM/YYYY format.')
    # Address (optional)
    if data.get('address') and not re.match(r'^[A-Za-z0-9 ._\-"']*$', data['address']):
        errors.append('Address contains invalid characters.')
    # Sex
    if data.get('sex') not in ['Male', 'Female', 'Other']:
        errors.append('Sex must be Male, Female, or Other.')
    # Uniqueness
    if is_new:
        exists = students.find_one({
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'dob': dob
        })
        if exists:
            errors.append('Student record already exists.')
    return errors


@app.route('/')
def index():
    return render_template('index.html')

# Navigation routes
@app.route('/add')
def add_student_page():
    return render_template('add_student.html')

@app.route('/delete')
def delete_student_page():
    return render_template('delete_student.html')

@app.route('/modify')
def modify_student_page():
    return render_template('modify_student.html')

@app.route('/report')
def report_page():
    return render_template('report.html')

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    errors = validate_student(data, is_new=True)
    if errors:
        return jsonify({'success': False, 'errors': errors, 'data': data}), 400
    student_id = get_next_student_id()
    student = {
        'student_id': student_id,
        'first_name': data['first_name'],
        'middle_name': data.get('middle_name', ''),
        'last_name': data['last_name'],
        'dob': data.get('dob', '01/01/2001'),
        'address': data.get('address', ''),
        'sex': data.get('sex', 'Male')
    }
    students.insert_one(student)
    return jsonify({'success': True, 'student_id': student_id})

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def modify_student(student_id):
    data = request.json
    errors = validate_student(data, is_new=False)
    if errors:
        return jsonify({'success': False, 'errors': errors, 'data': data}), 400
    result = students.update_one({'student_id': student_id}, {'$set': data})
    if result.matched_count == 0:
        return jsonify({'success': False, 'errors': ['Student not found.']}), 404
    return jsonify({'success': True})

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    result = students.delete_one({'student_id': student_id})
    if result.deleted_count == 0:
        return jsonify({'success': False, 'errors': ['Student not found.']}), 404
    return jsonify({'success': True})

@app.route('/api/students', methods=['GET'])
def get_students():
    all_students = list(students.find({}, {'_id': 0}))
    return jsonify({'students': all_students})

@app.route('/api/students/search', methods=['POST'])
def search_student():
    data = request.json
    query = {}
    if 'student_id' in data:
        query['student_id'] = int(data['student_id'])
    if 'first_name' in data:
        query['first_name'] = data['first_name']
    if 'last_name' in data:
        query['last_name'] = data['last_name']
    student = students.find_one(query, {'_id': 0})
    if not student:
        return jsonify({'success': False, 'errors': ['Student not found.']}), 404
    return jsonify({'success': True, 'student': student})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
