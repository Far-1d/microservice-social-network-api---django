# Social Network API (Django)

This is a Django-based Social Network API project designed to provide core social networking features with a focus on API-driven development.

---

## Prerequisites

Before setting up the project, ensure you have the following installed and configured on your development machine:

- **Python 3.6+** (recommended latest stable version)
- **pip** for Python package management
- **Virtual environment tool** (e.g., `venv` or `virtualenv`)
- **Django** (version compatible with your project)
- Basic knowledge of Django and REST APIs
- Familiarity with environment variables and `.env` files
- (Optional) An SMTP server or `aiosmtpd` for email testing during development

---
## Getting Started

### Running the Development Server

To start the project in development mode, run the following command:

```
python3 manage.py runserver --settings=settings.settings.dev
```

---

### Initial Setup

Before running the server, make sure to:

- Collect static files:
```
python3 manage.py collectstatic
```

- Create and apply database migrations:
```
python3 manage.py makemigrations
python3 manage.py migrate
```

---

### Email Sending in Development

To test email sending on your development server, start a local SMTP debugging server using `aiosmtpd`:

```
python3 -m aiosmtpd -n -l localhost:8025
```

This will listen on port 8025 and capture outgoing emails for testing purposes.

---

### Environment Variables

Create a `.env` file in your project root with at least the following variables:

```
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=your_jwt_algorithm
```

> **Note:** For production deployments, additional environment variables are required, including database credentials and Django's `SECRET_KEY`.

---

## Testing & Feedback

You are encouraged to test the API thoroughly and help improve it by reporting any bugs or issues you encounter.

Please send your feedback or bug reports via:

- **Email:** farid.zarie.000@gmail.com
- **Telegram:** [@el_fredoo](https://t.me/el_fredoo)

Your contributions and feedback are highly appreciated!


---

Thank you for using the Social Network API project!


