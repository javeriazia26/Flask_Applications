# Web Applications with Flask

A collection of Flask web applications built while learning backend web development with Python. This repository contains projects that demonstrate authentication, database management, CRUD operations, session handling, role-based access control, API development, security features, and practical backend application design using Flask and SQLAlchemy.

## About the Repository

This repository documents my learning journey in Flask and backend development. Each project focuses on different backend concepts and gradually introduces more advanced features, from simple CRUD applications to larger management and security-focused systems.

The goal of these projects is to gain practical experience by building real applications rather than only studying individual concepts. Along the way, I am learning how to structure Flask applications, work with databases, handle authentication and authorization, build APIs, and implement security-related features.

The projects are continuously being improved, and new projects will be added as I learn and experiment with different backend and cybersecurity concepts.

## Projects

### To-Do App

A simple task management application built to practice the basics of Flask, database operations, authentication, and user-specific data.

Users can:

* Register and log in
* Create and manage personal tasks
* Update task status
* Store passwords securely using hashing
* Maintain separate task lists for each user

### ScholarHub

A university scholarship management system designed to manage students, scholarships, academic information, and related university data.

The application includes:

* Student management
* Scholarship management
* Funding source management
* Department and university management
* Academic results management
* Role-based access control
* Audit logging
* Administrator and student dashboards
* Authentication and authorization
* REST API
* Database migration
* Security-focused backend features

### JirFlux

JirFlux is a Flask-based team collaboration and project management system. It is being developed to provide a single platform where users can connect with each other, create teams, manage projects, assign tasks, and track project progress.

The application includes:

* User registration and login
* Email verification
* OTP-based password reset
* Two-factor authentication
* Trusted device tracking
* User profiles
* User connections and connection requests
* Team creation and team management
* Project creation and project members
* Project roles and collaboration
* Task and work item management
* Task assignment
* Task priorities and deadlines
* Progress tracking
* Comments on work items
* Notifications
* User and project dashboards
* Admin management
* Audit logging
* Encryption and security services

JirFlux is **currently under development**, and new features and improvements are still being added. **OAuth authentication is also currently in progress.**

### JIRZO

JIRZO is an upcoming **rule-based anomaly detection agent** focused on identifying unusual or potentially risky login behavior.

The idea behind JIRZO is to collect information about a login attempt and compare it with known or expected user behavior. Based on predefined rules, the agent can determine whether a login appears normal, suspicious, or risky.

JIRZO is planned to analyze information such as:

* IP address
* Location
* Region
* Device information
* Trusted or untrusted device status
* Operating system information
* Browser information
* Username
* Login time
* Previous login information
* Failed login attempts
* OTP requests
* Other available login-related information

The agent will use these inputs to apply rules and make a decision about the login attempt.

For example:

* A login from a known device and familiar location may be considered **normal**.
* A login from a new device or unusual location may be considered **suspicious**.
* Multiple failed attempts combined with an unknown device or unusual location may result in a **high-risk** decision.

JIRZO is planned as a **rule-based system rather than a machine-learning model**. The purpose of the project is to understand how an agent can collect information, apply logical rules, assess risk, and take an appropriate action.

This project is planned and will be developed as part of my learning in **AI and cybersecurity**.

More projects will be added as I continue learning Flask and backend development.

## Concepts Practiced

* Flask Application Factory
* Blueprints
* Flask-SQLAlchemy
* Flask-WTF
* SQLAlchemy Relationships
* CRUD Operations
* Authentication
* Authorization
* Encryption
* REST API
* Database Migration
* Session Management
* Password Hashing
* Role-Based Access Control (RBAC)
* Flash Messages
* Form Validation
* Jinja2 Templates
* Static File Management
* Email Services
* OTP Verification
* Two-Factor Authentication
* Trusted Device Management
* Audit Logging
* Backend Security
* Rule-Based Anomaly Detection
* Agent-Based Logic

## Technologies Used

* Python
* Flask
* Flask-SQLAlchemy
* Flask-WTF
* SQLite
* PostgreSQL
* HTML5
* CSS3
* JavaScript
* Jinja2
* Werkzeug
* SQLAlchemy
* Alembic / Flask-Migrate

## Repository Structure

```text
web_app_with_flask/
│
├── Todo_App/
├── ScholarHub/
├── JirFlux/
├── JIRZO/
├── ...
└── README.md
```

Each project contains its own source code, templates, static files, configuration, and project-specific README where applicable.

## Getting Started

1. Clone the repository.

```bash
git clone https://github.com/javeriazia26/Web_App_with_Flask
```

2. Navigate to the project you want to run.

```bash
cd project-name
```

3. Create and activate a virtual environment.

```bash
python -m venv venv
venv\Scripts\activate
```

4. Install the required packages.

```bash
pip install -r requirements.txt
```

5. Run the application.

```bash
python run.py
```

## Learning Objectives

This repository is intended to strengthen practical knowledge of:

* Flask web development
* Backend application development
* Database design
* SQLAlchemy ORM
* User authentication
* User authorization
* Role-Based Access Control (RBAC)
* Data hashing and encryption
* REST API development
* Session handling
* Backend architecture
* RESTful application design
* Full CRUD functionality
* Email services
* OTP services
* Two-factor authentication
* Database migrations
* Audit logging
* Security-focused application development
* Rule-based decision making
* Anomaly detection concepts
* Agent-based systems

## Future Projects

Planned additions and improvements include:

* **JIRZO – Rule-Based Anomaly Detection Agent**
* Flask Deployment Examples
* Additional backend and cybersecurity projects

## Developer

**Jaweria Zia**

BS Computer Science

## Note

This repository is part of my backend development portfolio and reflects my progress in learning Flask by building practical web applications.

The projects are developed as part of my learning process, so some applications are still under development and may continue to receive new features, improvements, and security enhancements.
