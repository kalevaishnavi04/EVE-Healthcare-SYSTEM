# EVE Healthcare – Diagnostic Booking & Payment API

A simple backend project for booking diagnostic tests and making simulated payments.

The project is built using **Python, Django and Django REST Framework**.

## Features

* User Signup and Login
* JWT Authentication
* Browse Diagnostic Centres
* Browse Diagnostic Tests
* Book a Diagnostic Test
* Cancel Booking
* Simulated Payment
* Payment Webhook
* Swagger API Documentation
* PostgreSQL with Docker
* API Tests

## Technologies Used

* Python 3.11
* Django 5
* Django REST Framework
* PostgreSQL
* JWT Authentication
* Docker
* Swagger / OpenAPI

## Project Structure

```text
EVE Healthcare
│
├── config/
│   └── Django project settings
│
├── apps/
│   ├── users/
│   ├── centres/
│   ├── bookings/
│   └── payments/
│
├── templates/
│   └── index.html
│
├── manage.py
├── requirements.txt
└── docker-compose.yml
```

## How to Run the Project

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migration

```bash
python manage.py migrate
```

### 5. Create Admin User

```bash
python manage.py createsuperuser
```

### 6. Add Sample Data

```bash
python manage.py seed_data
```

### 7. Start the Server

```bash
python manage.py runserver
```

## Project URLs

* Frontend: `http://127.0.0.1:8000/`
* API: `http://127.0.0.1:8000/api/`
* Swagger: `http://127.0.0.1:8000/api/docs/`
* Admin Panel: `http://127.0.0.1:8000/admin/`

## Main APIs

### Authentication

| Method | API                        | Purpose            |
| ------ | -------------------------- | ------------------ |
| POST   | `/api/auth/signup/`        | Create new account |
| POST   | `/api/auth/login/`         | Login              |
| POST   | `/api/auth/token/refresh/` | Refresh JWT token  |
| GET    | `/api/auth/me/`            | Get current user   |

### Diagnostic Centres & Tests

| Method | API                  | Purpose             |
| ------ | -------------------- | ------------------- |
| GET    | `/api/centres/`      | View centres        |
| GET    | `/api/centres/{id}/` | View centre details |
| GET    | `/api/tests/`        | View tests          |
| GET    | `/api/tests/{id}/`   | View test details   |

Admin users can create, update and delete centres and tests.

### Bookings

| Method | API                          | Purpose              |
| ------ | ---------------------------- | -------------------- |
| POST   | `/api/bookings/`             | Create booking       |
| GET    | `/api/bookings/`             | View my bookings     |
| GET    | `/api/bookings/{id}/`        | View booking details |
| POST   | `/api/bookings/{id}/cancel/` | Cancel booking       |

### Payments

| Method | API                      | Purpose                |
| ------ | ------------------------ | ---------------------- |
| POST   | `/api/payments/`         | Make simulated payment |
| POST   | `/api/payments/webhook/` | Handle payment webhook |

The payment system is **simulated** and can return either successful or failed payment results.

## Booking Flow

```text
User Signup/Login
       ↓
Browse Centres
       ↓
Select Diagnostic Test
       ↓
Create Booking
       ↓
Booking Status = PENDING
       ↓
Make Payment
       ↓
SUCCESS → CONFIRMED
FAILED  → FAILED
```

## Security

* JWT authentication is used for protected APIs.
* Users can access only their own bookings.
* Booking price is calculated from the selected test on the server.
* Admin/staff users manage diagnostic centres and tests.
* Duplicate webhook events are handled safely.

## Database

Main models:

```text
User
  ↓
Booking
  ↓
DiagnosticTest
  ↓
DiagnosticCentre

Booking
  ↓
Payment

WebhookEvent
```

The booking stores the test price at the time of booking, so later price changes do not affect old bookings.

## Testing

Run:

```bash
python manage.py test
```

The project includes tests for authentication, bookings, payments, webhook idempotency and user access control.

## Docker

To run with PostgreSQL:

```bash
docker-compose up --build
```

Then create an admin user:

```bash
docker-compose exec web python manage.py createsuperuser
```

## Future Improvements

Some improvements that can be added later:

* Webhook authentication using HMAC
* Celery for background payment processing
* Redis caching
* Email notifications
* Custom user roles
* Booking reschedule API
* Better audit logs

## Author

**Vaishnavi Kale**

B.E. Information Technology
Python | Django | REST API | SQL | Backend Development
