# Bookkeeping Django App with HTMX

A basic Django project with HTMX integration demonstrating dynamic web interactions without JavaScript.

## Features

- Django 5.2.4 backend
- HTMX for dynamic frontend interactions
- Modern, responsive UI
- Sample dynamic button with real-time updates

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

5. **Visit the application:**
   - Home page: http://127.0.0.1:8000/
   - HTMX Demo: http://127.0.0.1:8000/htmx-demo/

## Project Structure

```
rocksolid-bk/
├── bookkeeping/                 # Main app
│   ├── templates/
│   │   └── bookkeeping/
│   │       ├── base.html       # Base template with HTMX
│   │       ├── home.html       # Home page
│   │       └── htmx_demo.html  # HTMX demo page
│   ├── urls.py                 # App URL configuration
│   └── views.py                # View functions
├── bookkeeping_project/        # Django project settings
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## HTMX Demo

The HTMX demo page features a dynamic button that:
- Uses `hx-post` to make AJAX requests
- Uses `hx-target` to specify which element to update
- Uses `hx-swap` to define how to insert the response
- Updates content without page refresh

## Technologies Used

- **Django**: Web framework
- **django-htmx**: HTMX integration for Django
- **HTMX**: Modern JavaScript library for dynamic interactions
- **SQLite**: Database (default Django database) 