# Student Management App (Flask + MongoDB + Mongo Express)

## a) Description of the App
This is a Dockerized microservice application for managing student records. It uses Python Flask for the backend, MongoDB for data storage, and Mongo Express for database administration. The app provides a web interface for adding, deleting, modifying, and reporting on students, with full CRUD support via REST API.

## b) Main Components
- **Flask App**: Handles the web UI and REST API for student management.
- **MongoDB**: Stores all student data.
- **Mongo Express**: Web-based MongoDB admin interface.

### Accessing Mongo Express
- After starting the app, open your browser and go to:  
  `http://localhost:8081`  
- Login with username: `admin` and password: `admin` (default, see `docker-compose.yml`).

## c) How to Start, Stop, and Restart the App

**Start:**
```bash
cd student3-flask-mongo-mongoExpress
sudo docker-compose up --build
```

**Stop:**
```bash
sudo docker-compose down
```

**Restart:**
```bash
sudo docker-compose down
sudo docker-compose up --build
```

The Flask app will be available at:  
`http://localhost:5000`

## d) Supported REST API Endpoints & Sample Commands

### Add Student
```
curl -X POST http://localhost:5000/api/students \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "John",
    "middle_name": "A",
    "last_name": "Doe",
    "dob": "01/01/2001",
    "address": "123 Main St",
    "sex": "Male"
  }'
```

### Modify Student
```
curl -X PUT http://localhost:5000/api/students/10001 \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Jane",
    "middle_name": "B",
    "last_name": "Smith",
    "dob": "02/02/2002",
    "address": "456 Elm St",
    "sex": "Female"
  }'
```

### Delete Student
```
curl -X DELETE http://localhost:5000/api/students/10001
```

### Get All Students (Report)
```
curl http://localhost:5000/api/students
```

### Search Student by ID
```
curl -X POST http://localhost:5000/api/students/search \
  -H 'Content-Type: application/json' \
  -d '{
    "student_id": 10001
  }'
```

## e) Debugging Steps
- Check container status:
  ```bash
  sudo docker-compose ps
  ```
- View logs for Flask app:
  ```bash
  sudo docker-compose logs flask-app
  ```
- View logs for MongoDB or Mongo Express:
  ```bash
  sudo docker-compose logs mongo
  sudo docker-compose logs mongo-express
  ```
- If the app is not accessible, ensure ports 5000 (Flask) and 8081 (Mongo Express) are not blocked.
- For code changes, restart the containers using the restart steps above.
- For database issues, access Mongo Express at `http://localhost:8081` for direct DB inspection.
