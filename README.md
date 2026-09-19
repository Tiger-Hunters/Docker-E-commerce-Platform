# ShopSphere – E-Commerce Microservices Platform

ShopSphere is a containerized e-commerce application built using a microservices architecture. It includes separate services for user management, products, and orders, with Nginx acting as the API gateway.

## Features

- User registration and login with JWT authentication
- Product listing and product details
- Shopping cart and checkout
- Order creation, order listing, and cancellation
- Redis caching for product data
- PostgreSQL databases for persistent storage
- Docker Compose for running the application

## Architecture

```text
                   ┌─────────────────────┐
                   │    React Frontend   │
                   │    Vite :5173       │
                   └──────────┬──────────┘
                              │ /api
                   ┌──────────▼──────────┐
                   │    Nginx Gateway    │
                   │       :9000         │
                   └──────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
      ┌──────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
      │ User       │   │ Product    │   │ Order      │
      │ Service    │   │ Service    │   │ Service    │
      └──────┬─────┘   └──────┬─────┘   └──────┬─────┘
             │                │                │
      ┌──────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
      │ User DB    │   │ Product DB │   │ Order DB   │
      │ PostgreSQL │   │ PostgreSQL │   │ PostgreSQL │
      └────────────┘   └────────────┘   └────────────┘
                              │
                       ┌──────▼─────┐
                       │   Redis    │
                       │   Cache    │
                       └────────────┘
```

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend services | Python, FastAPI |
| API Gateway | Nginx |
| Database | PostgreSQL |
| Cache | Redis |
| Authentication | JWT |
| Containerization | Docker, Docker Compose |

## Project Structure

```text
E-Commerce-platform/
├── Docker/
│   └── docker-compose.yml
├── Frontend/
├── Nginx/
│   └── nginx.conf
├── Redis/
├── Services/
│   ├── user-service/
│   ├── product-service/
│   └── order-service/
└── Secrets/
    ├── postgres_password.txt
    ├── redis_password.txt
    └── jwt_secret.txt
```

*The exact folder and service names may vary depending on the current repository version.*

## Requirements

Install the following before running the project:

- Git
- Docker Desktop
- Docker Compose
- Node.js and npm, if running the frontend locally

Make sure Docker Desktop is running before starting the containers.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Tiger-Hunters/Docker-E-Commerce-Platform.git
cd Docker-E-Commerce-Platform
```

### 2. Configure secrets

Create the required secret files under the `Secrets/` directory:

| File | Purpose |
|---|---|
| `postgres_password.txt` | PostgreSQL password |
| `redis_password.txt` | Redis password |
| `jwt_secret.txt` | Secret used to sign and verify JWTs |

Use strong, unique values. Check the Docker Compose file and service configuration to confirm the exact secret paths and expected environment variables.

**Never commit real passwords, JWT secrets, or other credentials to GitHub.**

### 3. Start the backend services

From the project root, run:

```bash
docker compose -f Docker/docker-compose.yml up -d --build
```

Check the running containers:

```bash
docker compose -f Docker/docker-compose.yml ps
```

View logs:

```bash
docker compose -f Docker/docker-compose.yml logs -f
```

Stop the containers:

```bash
docker compose -f Docker/docker-compose.yml down
```

To remove containers and their associated Compose network:

```bash
docker compose -f Docker/docker-compose.yml down
```

This command does not normally remove named database volumes. Use `-v` only if you intentionally want to delete persisted database data.

## Running the Frontend Locally

Open a separate terminal:

```bash
cd Frontend
npm install
npm run dev
```

Open the local Vite URL shown in the terminal, usually:

```text
http://localhost:5173
```

The frontend sends API requests through the Nginx gateway, which is published on port `9000`.

## Application Flow

1. A user registers or logs in.
2. The user browses the available products.
3. Product information is retrieved through the Nginx gateway.
4. The user adds products to the cart.
5. At checkout, the frontend submits the order request.
6. The order service processes the order and stores it in PostgreSQL.
7. The user can view their orders and cancel an order where supported.

## API Gateway

The frontend uses the Nginx gateway rather than connecting directly to each backend service.

Typical local gateway address:

```text
http://localhost:9000
```

API requests use the `/api` prefix. The Nginx configuration routes requests to the appropriate backend service.

Check `Nginx/nginx.conf` for the exact route mappings.

## Troubleshooting

### Docker services are not starting
Check Docker Desktop and inspect service logs:

```bash
docker compose -f Docker/docker-compose.yml ps
docker compose -f Docker/docker-compose.yml logs
```
## Contributing

1. Create or switch to a feature branch.
2. Make your changes.
3. Test the affected services.
4. Commit your changes with a descriptive message.
5. Push the branch and open a pull request.

Example:

```bash
git checkout -b feat/your-feature
git add .
git commit -m "feat: describe your change"
git push -u origin feat/your-feature
```

## Security Notes

- Keep secrets out of source control.
- Use strong passwords and JWT signing secrets.
- Do not expose internal service ports publicly unless required.
- Validate user input and protect authenticated endpoints.
- Avoid sharing production credentials in logs or screenshots.