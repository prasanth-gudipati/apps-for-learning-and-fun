import argparse
import requests
import random
import string
import sys

API_URL = "http://localhost:5000/api/students"

def random_name(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_student():
    return {
        "first_name": random_name(5),
        "middle_name": random_name(3),
        "last_name": random_name(5),
        "dob": "01/01/2001",
        "address": f"{random.randint(1,999)} {random_name(8)} St",
        "sex": random.choice(["Male", "Female"])
    }

def create_student_auto():
    student = random_student()
    resp = requests.post(API_URL, json=student)
    print(resp.json())

def create_student_user(args):
    student = {
        "first_name": args.first_name,
        "middle_name": args.middle_name or "",
        "last_name": args.last_name,
        "dob": args.dob or "01/01/2001",
        "address": args.address or "",
        "sex": args.sex or "Male"
    }
    resp = requests.post(API_URL, json=student)
    print(resp.json())

def create_students_auto(args):
    for _ in range(args.count):
        create_student_auto()

def show_student(args):
    if args.student_id:
        url = f"{API_URL}/{args.student_id}"
        resp = requests.get(url)
    elif args.first_name:
        url = f"{API_URL}/search"
        resp = requests.post(url, json={"first_name": args.first_name})
    else:
        print("Provide student_id or first_name")
        return
    print(resp.json())

def modify_student(args):
    student_id = args.student_id
    new_data = {}
    if args.first_name: new_data["first_name"] = args.first_name
    if args.middle_name: new_data["middle_name"] = args.middle_name
    if args.last_name: new_data["last_name"] = args.last_name
    if args.dob: new_data["dob"] = args.dob
    if args.address: new_data["address"] = args.address
    if args.sex: new_data["sex"] = args.sex
    if student_id:
        url = f"{API_URL}/{student_id}"
        resp = requests.put(url, json=new_data)
    elif args.first_name:
        url = f"{API_URL}/modify"
        resp = requests.post(url, json={"first_name": args.first_name, **new_data})
    else:
        print("Provide student_id or first_name")
        return
    print(resp.json())

def delete_student(args):
    if args.student_id:
        url = f"{API_URL}/{args.student_id}"
        resp = requests.delete(url)
    elif args.first_name and args.last_name:
        url = f"{API_URL}/delete"
        resp = requests.post(url, json={"first_name": args.first_name, "last_name": args.last_name})
    else:
        print("Provide student_id or both first_name and last_name")
        return
    print(resp.json())

def main():
    parser = argparse.ArgumentParser(description="Student DB CLI via REST API")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("create-auto", help="Create 1 new student with auto-generated values")

    create_user_parser = subparsers.add_parser("create-user", help="Create 1 new student with user-given values")
    create_user_parser.add_argument("--first_name", required=True)
    create_user_parser.add_argument("--middle_name")
    create_user_parser.add_argument("--last_name", required=True)
    create_user_parser.add_argument("--dob")
    create_user_parser.add_argument("--address")
    create_user_parser.add_argument("--sex")

    create_n_parser = subparsers.add_parser("create-n-auto", help="Create N new students with auto-generated values")
    create_n_parser.add_argument("--count", type=int, required=True)

    show_parser = subparsers.add_parser("show", help="Show details of a student")
    show_parser.add_argument("--student_id")
    show_parser.add_argument("--first_name")

    modify_parser = subparsers.add_parser("modify", help="Modify a student")
    modify_parser.add_argument("--student_id")
    modify_parser.add_argument("--first_name")
    modify_parser.add_argument("--middle_name")
    modify_parser.add_argument("--last_name")
    modify_parser.add_argument("--dob")
    modify_parser.add_argument("--address")
    modify_parser.add_argument("--sex")

    delete_parser = subparsers.add_parser("delete", help="Delete a student")
    delete_parser.add_argument("--student_id")
    delete_parser.add_argument("--first_name")
    delete_parser.add_argument("--last_name")

    args = parser.parse_args()

    if args.command == "create-auto":
        create_student_auto()
    elif args.command == "create-user":
        create_student_user(args)
    elif args.command == "create-n-auto":
        create_students_auto(args)
    elif args.command == "show":
        show_student(args)
    elif args.command == "modify":
        modify_student(args)
    elif args.command == "delete":
        delete_student(args)
    else: