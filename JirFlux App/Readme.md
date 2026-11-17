# JirFlux

**A Jira and Trello inspired project workspace, built to explore backend security and role-based access control.**

JirFlux lets teams plan projects, break them into work items, assign people, discuss the work and attach files, with access that is controlled **per project** instead of by one global admin and user split.


<!-- Add 3 to 4 screenshots here: dashboard, board, project detail, roles -->
<!-- ![Dashboard](docs/screenshots/dashboard.png) -->

---

## Table of contents

- [Why I built this](#why-i-built-this)
- [Features](#features)
- [Roles and permissions](#roles-and-permissions)
- [Security](#security)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Google sign-in (OAuth)](#google-sign-in-oauth)
- [File attachments](#file-attachments)
- [Deploying to Vercel](#deploying-to-vercel)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Why I built this

My previous project, **ScholarHub**, had a simple admin panel and a user panel. JirFlux goes deeper on **how permissions and access control really work on the backend**, not just how the interface looks.

Two ideas drive the design:

1. **Roles belong to the project, not the person.** The same user can own one project, contribute to another and only watch a third.
2. **Hiding a button is not access control.** Every action is checked on the server against the user's role in that project.

It takes its structure from **Jira** (projects, work items, priorities, assignees) and its board from **Trello** (drag cards between status columns).

---

## Features

### Workspace

- **Dashboard** with completed, in-progress, not-started and overdue counts, a recent activity feed and a calendar
- **Kanban board** with drag-and-drop status updates (Not Started, In Progress, Completed)
- **Projects** with status (Active, Completed, On Hold), start and deadline dates, and automatic progress tracking
- **Work items** with priority, progress, dates, descriptions and multiple assignees
- **Comments** on every work item, editable and deletable by their author
- **File attachments** on work items (PNG, JPEG and PDF)
- **GitHub repository link** on each project, validated before it is saved
- **My tasks** page that gathers everything assigned to you across all projects, with status filters, priority filters and sorting
- **Calendar** view of deadlines
- **Team and connections**: find people, connect, and add accepted connections to a project

### Accounts

- Email and password registration with **email verification (OTP)**
- **Google sign-in** (OAuth 2.0)
- **Two-factor authentication** with device verification for new devices
- **Trusted devices**: a verified browser is remembered, so you are not challenged again
- **Profile** with photo, bio, location and skills
- **Settings** for personal details, security and notification preferences

### Notifications and activity

- In-app notifications with filters (all, unread, due today, mentions, system) and mark-all-as-read
- Security notifications for failed logins, locked accounts and new-device sign-ins
- Audit log of important actions

### Panels

- **User panel:** the workspace described above
- **Admin panel:** a separate dashboard and profile for administrators, protected by an admin-only access check

---

## Roles and permissions

Roles are assigned **per project**.

| Action | Owner | Member | Visitor |
|---|:---:|:---:|:---:|
| View the project and its work items | Yes | Yes | Yes |
| Add, update and delete work items | Yes | Yes | No |
| Assign people to work items | Yes | Yes | No |
| Comment on work items | Yes | Yes | Yes |
| Attach files | Yes | Yes | No |
| Edit or delete the project | Yes | No | No |
| Add or remove members and visitors | Yes | No | No |
| Link a GitHub repository | Yes | No | No |
| Leave the project | No (delete it instead) | Yes | Yes |

Notes:

- Only the **owner** can add people, and only people who are already **accepted connections**.
- Comments and attached files can only be edited or removed by the person who created them.
- When a member leaves, their assignments are removed and the work items they created move to the project owner.

---

## Security

Security is the main reason this project exists. What is implemented:

- **Password hashing**: passwords are never stored in plain text
- **Server-side authorization**: every project action (edit, delete, add or remove member, set repository link) checks the user's role in that project, whatever the interface shows
- **Email verification**: new accounts must verify through a one-time code
- **Two-factor authentication** with **device verification**: unrecognized devices need a code sent by email
- **Trusted devices** use a random token stored in an HttpOnly cookie; only a **hash** of the token is stored in the database
- **Account lockout**: five failed password attempts lock the account for one day
- **Generic login errors**: the same message is shown for a wrong password and an unknown email
- **Security alerts**: new-device sign-ins and failed attempts create notifications and alert emails
- **Audit logging** of sign-ins, failures, lockouts and profile changes
- **Profile pictures** are validated, re-encoded and resized on the server (Pillow), with size and pixel limits
- **Output escaping**: comments and filenames are rendered as plain text, never as HTML
- **Validated input**: GitHub links are checked before saving

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Flask (blueprints, application factory) |
| Templates | Jinja2, plain CSS and JavaScript |
| Database | PostgreSQL (hosted on Neon) |
| ORM and migrations | SQLAlchemy, Alembic |
| Authentication | Werkzeug password hashing, Authlib (Google OAuth) |
| Images | Pillow |
| Forms | Flask-WTF |
| Hosting | Vercel (serverless Python) |

---

## Project structure

A simplified view:

```
JirFlux/
├── run.py                      # entry point (also used by Vercel)
├── requirements.txt
├── vercel.json
├── .env.example
└── app/
    ├── __init__.py             # create_app(): config, extensions, blueprints
    ├── models.py               # User, Project, ProjectMember, WorkItem, ...
    ├── routes/
    │   ├── auth/               # login, register, OAuth, verification
    │   ├── admin/              # admin dashboard and profile
    │   └── user/               # dashboard, project, workitem, assignee,
    │                           # comment, attachment, task, profile, avatar,
    │                           # notification, connection
    ├── templates/              # auth/, admin/, user/, shared/
    └── static/                 # css, js, images
```

---

## Getting started

### Prerequisites

- Python 3.10 or newer
- A PostgreSQL database (local, or a free one from [Neon](https://neon.tech))
- A Google Cloud project, if you want Google sign-in
- An SMTP account for sending verification and alert emails

### Install

```powershell
git clone [repository URL]
cd JirFlux

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate         # macOS or Linux

pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and fill in the values (see [Environment variables](#environment-variables)).

### Create the database tables

```powershell
flask --app run db upgrade
```

### Run

```powershell
python run.py
```

Open <http://127.0.0.1:5000>.

---

## Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs session cookies. Use a long random value and **never change it casually**, because that signs everyone out |
| `DATABASE_URL` | PostgreSQL connection string |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `MAIL_SERVER`, `MAIL_PORT` | SMTP host and port |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | SMTP credentials |
| `MAIL_DEFAULT_SENDER` | "From" address on emails |

Generate a secret key with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

The names above must match the ones read in `app/__init__.py`. Never commit your real `.env` file.

---

## Google sign-in (OAuth)

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. Go to **APIs and Services, then OAuth consent screen**, and configure it.
3. Go to **Credentials, then Create credentials, then OAuth client ID**, and choose **Web application**.
4. Add these **Authorized redirect URIs**, using your own callback path:
   - `http://127.0.0.1:5000/[callback-path]` for local development
   - `https://jirflux.vercel.app/[callback-path]` for production
5. Copy the client ID and secret into `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

The redirect URI in Google must match your app's callback **exactly**, including `http` or `https` and any trailing slash.

---

## File attachments

Owners and members can attach files to a work item. Visitors can view the item but cannot upload.

- **Allowed types:** PNG, JPEG and PDF
- **Maximum size:** 5 MB per file
- Only the person who attached a file can remove it
- Filenames are shown as plain text, so a malicious name cannot inject markup

**Profile pictures** are handled separately: they are resized to 256 by 256, converted to JPEG and stored in PostgreSQL, then served through a login-protected `/avatar/<user id>` route.

> **Why not the `static` folder?** On Vercel the filesystem is read-only, so uploads cannot be saved to disk. Anything users upload has to live in the database or in external storage.

---

## Deploying to Vercel

1. Push the project to GitHub and import it in Vercel.
2. Make sure `requirements.txt` lists every package, including `Authlib` and `Pillow`.
3. In **Settings, then Environment Variables**, add every variable from the table above for the **Production** environment. Vercel does not read your local `.env`.
4. Add your production URL to the Google OAuth redirect URIs.
5. Deploy, then check the **Deployments** tab turns green.

Place this near your app setup so Flask knows it is behind Vercel's HTTPS proxy:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
```

### Serverless things to remember

- The filesystem is **read-only**, so never save uploads inside the project folder
- Several instances can run at once, so keep state in the database or in the signed cookie, never in Python globals
- `SECRET_KEY` must be the **same** on every instance
- Request bodies are limited to roughly 4.5 MB
- Cookies belong to a domain, so a preview URL starts with no trusted devices

---

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'authlib'` | The virtual environment is not active, or the package is missing. Activate `.venv` and run `pip install -r requirements.txt` |
| Login says "successful" but returns a 500 on Vercel | `set_cookie` was called with `None` when a new device had no token. Only set the cookie when a token exists |
| Every login shows "unauthorized device" on a new domain | Device cookies are per domain. Verify the device once on the new domain |
| `Read-only file system` on upload | The code saves to disk. Store in the database or external storage |
| `BuildError: Could not build url for endpoint ...` in a template | `url_for` was used for a value that is not a route. Print the value directly, for example `{{ user.picture }}` |
| `ImportError: cannot import name ...` at startup | A route file imports something that does not exist or was never deployed. Run `python run.py` locally first |
| `column ... does not exist` | A model column has no matching database column. Run the migration against the database the app uses |
| Profile pictures missing | The page is requesting an old `/static/pictures/...` path. Use the `/avatar/<id>` URL instead |

---

## Roadmap

- UI polish and refinements
- More granular admin tools
- Real-time updates for the board
- Automated tests for the permission rules

---

## Author

Built by **Javeria Zia** as a hands-on way to learn how access control and backend security work.
