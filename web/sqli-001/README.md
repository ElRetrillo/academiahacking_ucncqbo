# Login Bypass

| Field      | Value          |
|------------|----------------|
| **ID**     | `web-sqli-001` |
| **Category** | Web          |
| **Difficulty** | Easy       |
| **Points** | 100            |

## Objective

Bypass the login form of the SecureCorp admin portal and obtain the flag.

## How to Run

```bash
cd web/sqli-001
docker compose up --build
```

The application will be available at **http://localhost:8080**.

## How to Stop

```bash
docker compose down
```

## Expected Behavior

- The application presents a login form.
- Valid non-admin credentials grant access but do not reveal the flag.
- The flag is only visible when authenticated as the admin user.
- The database is created automatically inside the container on startup.

## ⚠️ Intentionally Vulnerable

This challenge contains a **deliberate security vulnerability** for educational purposes. Do **not** deploy this application in production or on a public network.
