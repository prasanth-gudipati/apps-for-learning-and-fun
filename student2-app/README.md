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

### 3. Using the App
- **Main Screen:** View all students, add new, edit, delete, and generate report.
- **Add Student:** Fill in the form. First and last names (min 2 chars), DOB, and sex are required. Address and middle name are optional.
- **Edit Student:** Update any field. Validation applies.
- **Delete Student:** Remove by clicking delete on the main screen.
- **Report:** Click 'Generate Report' to see all students in a table.

### 4. REST API Endpoints
- `GET /api/students` — List all students
- `POST /api/student` — Add a student (JSON)
- `PUT /api/student/<student_id>` — Update a student (JSON)
- `DELETE /api/student/<student_id>` — Delete a student

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
