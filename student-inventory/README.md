# Student Inventory Microservices Project

## Overview
A simple microservices-based student inventory app using Python Flask, Redis, and Docker Compose. Supports REST API and a basic web UI.

## Features
- Add, update, delete, and list students
- REST API endpoints for all operations
- Simple web UI (HTML/CSS)
- Redis as the backend database

## Requirements
- Ubuntu 22.04
- Docker & Docker Compose

## Usage
1. Clone this repo and navigate to the project directory.
2. Build and start the services:
   ```bash
   sudo docker-compose up --build
   ```
3. Access the app at [http://localhost:5000](http://localhost:5000)

## API Endpoints
- `GET /api/students` - List all students
- `POST /api/students` - Add a student (JSON: name, roll, class)
- `PUT /api/students/<roll>` - Update a student
- `DELETE /api/students/<roll>` - Delete a student

## Directory Structure
```
student-inventory/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
├── docker-compose.yml
└── README.md
```
