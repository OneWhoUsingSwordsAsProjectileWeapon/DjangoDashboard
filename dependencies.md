
# Project Dependencies

This project requires the following Python packages. Use pip to install them:

```bash
pip install channels==4.2.2 channels-redis==4.2.1 django==5.2.1 django-extensions==4.1 django-filter==25.1 django-redis==5.4.0 djangorestframework==3.16.0 pillow==11.2.1 pytest==8.3.5 pytest-django==4.11.1
```

## Core Dependencies

- **Django==5.2.1**: Web framework
- **djangorestframework==3.16.0**: REST API framework 
- **django-filter==25.1**: Filtering for Django QuerySets
- **django-extensions==4.1**: Extensions for Django

## Real-time Communication
- **channels==4.2.2**: WebSocket support for Django
- **channels-redis==4.2.1**: Redis backend for Django Channels

## Caching and Storage
- **django-redis==5.4.0**: Redis integration for Django
- **pillow==11.2.1**: Python Imaging Library for image processing

## Testing
- **pytest==8.3.5**: Testing framework
- **pytest-django==4.11.1**: Django plugin for pytest

## Quick Installation

To install all dependencies at once:

```bash
pip install -r requirements.txt
```

Or using the project configuration:

```bash
pip install -e .
```

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Run migrations: `python manage.py migrate`
4. Create admin/moderator users: `python manage.py create_admin_moder`
5. Collect static files: `python manage.py collectstatic --noinput`
6. Start the server: `python manage.py runserver 0.0.0.0:5000`

## Default Accounts
- **Admin**: username `Admin`, password `123`
- **Moderator**: username `Moder`, password `123`
