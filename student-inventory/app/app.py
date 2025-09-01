from flask import Flask, request, render_template, jsonify, redirect, url_for
import redis
import json

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route('/')
def index():
    students = []
    for key in r.scan_iter("student:*"):
        students.append(json.loads(r.get(key)))
    return render_template('index.html', students=students)

@app.route('/api/students', methods=['GET'])
def get_students():
    students = []
    for key in r.scan_iter("student:*"):
        students.append(json.loads(r.get(key)))
    return jsonify(students)

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    key = f"student:{data['roll']}"
    r.set(key, json.dumps(data))
    return jsonify({"status": "success"}), 201

@app.route('/api/students/<roll>', methods=['PUT'])
def update_student(roll):
    data = request.json
    key = f"student:{roll}"
    if r.exists(key):
        r.set(key, json.dumps(data))
        return jsonify({"status": "updated"})
    return jsonify({"error": "not found"}), 404

@app.route('/api/students/<roll>', methods=['DELETE'])
def delete_student(roll):
    key = f"student:{roll}"
    if r.delete(key):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
