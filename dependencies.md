# Project Dependencies

This project requires the following Python packages. Use pip to install them:

```bash
pip install Django==5.2.1 djangorestframework==3.15.0 django-filter==24.1 channels==4.0.0 channels-redis==4.2.0 daphne==4.1.0 django-extensions==3.2.3 django-redis==5.4.0 Pillow==10.2.0 pytest==8.0.2 pytest-django==4.7.0 six==1.16.0
```

## Core Dependencies

- Django==5.2.1: Web framework
- djangorestframework==3.15.0: REST API framework 
- django-filter==24.1: Filtering for Django QuerySets
- django-extensions==3.2.3: Extensions for Django

## Real-time Communication
- channels==4.0.0: WebSocket support for Django
- channels-redis==4.2.0: Redis backend for Django Channels
- daphne==4.1.0: HTTP and WebSocket protocol server

## Caching and Storage
- django-redis==5.4.0: Redis integration for Django
- Pillow==10.2.0: Python Imaging Library for image processing

## Testing
- pytest==8.0.2: Testing framework
- pytest-django==4.7.0: Django plugin for pytest

## Utilities
- six==1.16.0: Python 2 and 3 compatibility library

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