
# Project Dependencies

This project requires the following Python packages. Use pip to install them:

```bash
pip install Django==5.2.1 djangorestframework==3.15.0 django-filter==24.1 channels==4.0.0 channels-redis==4.2.0 daphne==4.1.0 django-extensions==3.2.3 django-redis==5.4.0 Pillow==10.2.0 pytest==8.0.2 pytest-django==4.7.0 six==1.16.0 redis==5.0.1 asgiref==3.7.2 python-dateutil==2.8.2 pytz==2023.3
```

## Core Dependencies

- **Django==5.2.1**: Web framework
- **djangorestframework==3.15.0**: REST API framework 
- **django-filter==24.1**: Filtering for Django QuerySets
- **django-extensions==3.2.3**: Extensions for Django

## Real-time Communication
- **channels==4.0.0**: WebSocket support for Django
- **channels-redis==4.2.0**: Redis backend for Django Channels
- **daphne==4.1.0**: HTTP and WebSocket protocol server
- **asgiref==3.7.2**: ASGI compatibility utilities

## Caching and Storage
- **django-redis==5.4.0**: Redis integration for Django
- **redis==5.0.1**: Redis Python client
- **Pillow==10.2.0**: Python Imaging Library for image processing

## Date and Time Utilities
- **python-dateutil==2.8.2**: Extensions to the standard Python datetime module
- **pytz==2023.3**: World timezone definitions

## Testing
- **pytest==8.0.2**: Testing framework
- **pytest-django==4.7.0**: Django plugin for pytest

## Utilities
- **six==1.16.0**: Python 2 and 3 compatibility library

## Installation Instructions

### Quick Install (All Dependencies)
```bash
pip install Django==5.2.1 djangorestframework==3.15.0 django-filter==24.1 channels==4.0.0 channels-redis==4.2.0 daphne==4.1.0 django-extensions==3.2.3 django-redis==5.4.0 Pillow==10.2.0 pytest==8.0.2 pytest-django==4.7.0 six==1.16.0 redis==5.0.1 asgiref==3.7.2 python-dateutil==2.8.2 pytz==2023.3
```

### Create Requirements File
To create a requirements.txt file:
```bash
pip freeze > requirements.txt
```

### Install from Requirements
```bash
pip install -r requirements.txt
```

## Setting Up a Virtual Environment

To create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Additional Setup Commands

After installing dependencies, run these commands to set up the project:

```bash
# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin and moderator accounts
python manage.py create_admin_moder

# Collect static files
python manage.py collectstatic --noinput

# Run the development server
python manage.py runserver 0.0.0.0:5000
```

## Default Accounts

The project creates these default accounts:
- **Admin**: username `Admin`, password `123`
- **Moderator**: username `Moder`, password `123`

## Project Features

- User management with custom user model
- Property listings system with approval workflow
- Real-time chat with WebSocket support
- Notifications system
- Content moderation and reporting
- User complaints system
- Calendar availability system
- Booking management
