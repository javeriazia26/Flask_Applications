# JirFlux

JirFlux is a Flask-based team collaboration and project management system. It is being developed to make it easier for users to connect with each other, create teams, manage projects, assign tasks, and keep track of their work in one place.

The project is currently **under development**, so some features are still being improved and added. **OAuth authentication is also currently in progress.**

## Main Features

### 1. User account and security

* Users can register, log in, and verify their email accounts.
* Password reset is supported through an OTP-based verification flow.
* Two-factor authentication is supported through authenticator services.
* Trusted devices can be tracked for additional account security.
* Users can manage their profiles, including their bio, location, title, and profile image.

### 2. Connection and networking

* Users can send connection requests to other users.
* Received requests can be accepted or rejected.
* Connected users can collaborate more easily when working together on teams and projects.
* Connection requests and related activities are handled through the connection and notification system.

### 3. Team creation and collaboration

* Users can create their own teams.
* Team members can be added and managed.
* Each team provides a shared space for collaboration.
* Team membership and related activities are stored and managed through the database.
* Notifications help keep team members informed about important team activities.

### 4. Project management

* Users can create projects by providing a title, description, start date, and deadline.
* Every project has an owner and can have multiple members.
* Project members can be invited and assigned different roles.
* Project status can be updated as the project moves forward.

### 5. Task and work item tracking

* Users can create tasks or work items inside a project.
* Each work item can contain a title, description, start date, deadline, priority, and progress status.
* Tasks can be assigned to specific users.
* Work items can be edited, commented on, or deleted when needed.

### 6. Progress monitoring

* Work items can have different progress states such as **Not Started, In Progress, and Completed**.
* Users can update the progress of their assigned work as they complete different parts of a project.
* Project and user dashboards provide an overview of current work and assigned tasks.
* Notifications help users stay updated about assignments, changes, and reminders.

### 7. Notifications and communication

* Users receive notifications about project changes, work item updates, assignments, and connection activity.
* Notifications can be marked as read.
* Users can manage their notification preferences for account, security, email, and team-related updates.

### 8. Admin and audit visibility

* Admin users can review activity logs and manage system settings.
* The audit trail keeps track of important actions related to users, projects, and work items.
* This provides better visibility into activity within the system.

## Services included

JirFlux includes several service modules that handle specific parts of the application:

* `authenticator_service.py`: Handles authentication and security-related workflows.
* `email_service.py`: Handles email notifications and communication.
* `encryption_service.py`: Handles encryption and protection of sensitive values and data.
* `otp_service.py`: Handles OTP generation and verification.

**OAuth authentication is currently being integrated into the project and is still in progress.**

## How the workflow works

### User connection flow

1. A user registers for an account and verifies their email.
2. They open the connection section.
3. They send a connection request to another user.
4. The other user can accept or reject the request.
5. Once the request is accepted, the users become connected and can collaborate more easily in teams and projects.

### Team creation flow

1. A user creates a team from their dashboard.
2. The person who creates the team becomes its owner.
3. Other users can be added as team members.
4. The team provides a shared space where members can work together on projects and tasks.

### Project creation flow

1. A user creates a new project.
2. They enter the project details, including its title, description, and timeline.
3. Other users can be invited to the project and assigned appropriate roles.
4. Project members can then work together within the project.

### Task and work item flow

1. A user opens a project.
2. They create a new task or work item.
3. They provide details such as the title, description, priority, deadline, and assignee.
4. The work item becomes part of the project's workflow.
5. Team members can update the work item, add comments, and track its progress.

### Progress tracking flow

1. Every work item has a progress status.
2. Users can move a task from **Not Started** to **In Progress** and eventually to **Completed**.
3. The dashboard reflects the current progress of the work.
4. Project views and notifications help team members stay informed about ongoing work.

## Project Structure

```text
JirFlux/
├── .env
├── config.py
├── run.py
├── README.md
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── admin_profile.py
│   │   │   ├── admin_setting.py
│   │   │   └── audit_log.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── forget_pass.py
│   │   │   ├── login_form.py
│   │   │   ├── reg_form.py
│   │   │   └── verify.py
│   │   └── user/
│   │       ├── __init__.py
│   │       ├── connection.py
│   │       ├── dash.py
│   │       ├── notification.py
│   │       ├── profile.py
│   │       ├── project.py
│   │       ├── project_member.py
│   │       ├── setting.py
│   │       ├── task.py
│   │       ├── team.py
│   │       ├── user.py
│   │       └── workitem.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── authenticator_service.py
│   │   ├── email_service.py
│   │   ├── encryption_service.py
│   │   └── otp_service.py
│   ├── static/
│   │   ├── css/
│   │   │   ├── admin.css
│   │   │   ├── auth.css
│   │   │   └── user.css
│   │   ├── images/
│   │   ├── js/
│   │   │   └── notifications.js
│   │   └── pictures/
│   └── templates/
│       ├── base.html
│       ├── admin/
│       │   ├── audit_log.html
│       │   ├── base.html
│       │   ├── profile.html
│       │   └── setting.html
│       ├── auth/
│       │   ├── forgot_pass.html
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── reset_pass.html
│       │   └── verify.html
│       ├── shared/
│       │   ├── _profile_content.html
│       │   └── _settings_content.html
│       └── user/
│           ├── base.html
│           ├── board.html
│           ├── connection.html
│           ├── notification.html
│           ├── profile.html
│           ├── project.html
│           ├── setting.html
│           ├── task.html
│           ├── team.html
│           ├── user_dash.html
│           └── workitem.html
├── migrations/
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── bd952a661d38_initial_schema.py
└── __pycache__/
```

## Run the application

```bash
python run.py
```

## Project Status

JirFlux is currently **under active development**. The core collaboration, project management, task tracking, notification, and account security features are being developed and improved.

Some functionality may still change as the project evolves. **OAuth authentication is currently in the process of being implemented**, along with further improvements to the existing system.

## Summary

JirFlux is being developed as a lightweight but practical platform for team collaboration and project management. It brings together user connections, team creation, project planning, task assignment, progress tracking, notifications, and account security into one Flask-based application.

The goal is to provide users with a simple place where they can connect with others, organize their teams, manage projects, assign work, and keep track of their progress without having to use separate systems for each part of the workflow.

