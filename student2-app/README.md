# Student Management App (Flask + MongoDB + Docker)

A web-based student management system built with Python Flask, MongoDB, and Docker Compose. Supports full CRUD operations, REST API, and a modern UI.

## Features
- Add, edit, delete, and view student records
- Unique student ID generation (10001-99999)
- Input validation and error handling
- Generate report of all students
- REST API for CRUD operations
- Responsive HTML/CSS UI
- Dockerized for easy deployment

## Requirements
- Ubuntu 22.04+
- Docker (tested with 28.3.3)
- Docker Compose (tested with 1.29.2)


## Getting Started

### 1. Clone the repository
```
git clone <repo-url>
cd apps-for-learning-and-fun/student2-app
```


### 2. Build and run with Docker Compose
```
docker-compose up --build
```
- The Flask app will be available at: http://localhost:5002
- MongoDB will run on port 27018

### a) How to Stop and Restart the App

**To stop the app:**
```
docker-compose down
```

**To restart the app:**
```
docker-compose up --build
```

You can also use `docker-compose restart` to quickly restart containers without rebuilding.

### 3. Using the App
- **Main Screen:** View all students, add new, edit, delete, and generate report.
- **Add Student:** Fill in the form. First and last names (min 2 chars), DOB, and sex are required. Address and middle name are optional.
- **Edit Student:** Update any field. Validation applies.
- **Delete Student:** Remove by clicking delete on the main screen.
- **Report:** Click 'Generate Report' to see all students in a table.


### b) REST API Endpoints & Examples

- `GET /api/students` — List all students
- `POST /api/student` — Add a student (JSON)
- `PUT /api/student/<student_id>` — Update a student (JSON)
- `DELETE /api/student/<student_id>` — Delete a student

**Examples:**

**Get all students:**
```
curl http://localhost:5002/api/students
```

**Add a student:**
```
curl -X POST http://localhost:5002/api/student \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "middle_name": "A",
    "last_name": "Doe",
    "dob": "2000-01-01",
    "address": "123 Main St",
    "sex": "Male"
  }'
```

**Update a student:**
```
curl -X PUT http://localhost:5002/api/student/10001 \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith"
  }'
```

**Delete a student:**
```
curl -X DELETE http://localhost:5002/api/student/10001
```

## File Structure
```
student2-app/
├── app/
│   ├── app.py            # Flask application
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile        # Flask app Dockerfile
│   ├── static/
│   │   └── style.css     # CSS styles
│   └── templates/        # HTML templates
│       ├── index.html
│       ├── add_student.html
│       ├── edit_student.html
│       └── report.html
├── docker-compose.yml    # Docker Compose config
└── README.md             # This file
```

### c) How to Access MongoDB and See the DB Records

You can access the MongoDB instance running in Docker using the MongoDB shell or a GUI client.

**Using the MongoDB shell:**
1. Open a shell into the running MongoDB container:
  ```
  docker-compose exec mongo mongosh
  ```
2. Switch to the `studentdb` database:
  ```
  use studentdb
  ```
3. Show all student records:
  ```
  db.students.find().pretty()
  ```

**Using a GUI client (e.g., MongoDB Compass):**
- Connect to: `mongodb://localhost:27018/studentdb`

You can now browse, query, and edit records visually.

## Troubleshooting
- If you see errors about 'form is undefined', ensure the backend is up-to-date.
- For Docker errors, try:
  ```
  docker-compose down --volumes --remove-orphans
  docker system prune -af
  docker volume prune -f
  docker-compose up --build
  ```

## License
MIT

---
For questions or issues, contact the project maintainer.
