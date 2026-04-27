# YBTMK Dashboard

A Django-based dashboard application.

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

## Project Structure

```
ybtmk_project/
├── settings.py       # Django settings
├── urls.py          # URL routing
├── wsgi.py          # WSGI application
└── asgi.py          # ASGI application
templates/           # HTML templates
manage.py            # Django management script
requirements.txt     # Python dependencies
```

## Development

- Admin panel: `http://localhost:8000/admin/`

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

Refer to `ybtmk_project/settings.py` for available configuration options.
