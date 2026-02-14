# Phase-1 High Level Design (HLD)

## 1. Logical Architecture

The MaaV Phase-1 system is designed as a modular **Monorepo** architecture, separating concerns between Frontend (Client), API Gateway, Business Logic (Backend), and Data Storage.

### **1.1 The Client (Frontend)**
- **Stack**: Vite + React + TailwindCSS
- **Role**: Presentation and User Interaction.
- **State Management**: React Query / Context API.
- **Routing**: Client-side routing with protected routes based on Auth/Role.

### **1.2 API Gateway & Entry (Backend)**
- **Stack**: Nginx (Production) / Uvicorn (Dev) -> FastAPI
- **Role**: Request validation, Authentication (JWT), Rate Limiting.
- **Contract**: RESTful JSON API.

### **1.3 Backend Core (Application Logic)**
The heart of the system, structured into distinct layers:
- **API Layer**: Route definitions and Pydantic validation models.
- **Service Layer**: Orchestrates complex business flows (e.g., "Onboard User", "Calculate Tax").
- **Repository Layer**: Abstracts database access (SQLAlchemy).
- **Engines**: Pure-logic modules:
    - **Compliance Engine**: Validates data against tax rules.
    - **Calculation Engine**: Performs deterministic tax computations.

### **1.4 Data Layer**
- **Database**: PostgreSQL (Managed via Supabase).
- **Schema Management**: Alembic migrations based on `db/schema.sql`.
- **Storage**: Structured relational data (Users, Financials, Filings).

## 2. Component Boundaries
Strict boundaries enforce clean architecture:
- **Service -> Repository**: Services **never** access the DB directly; they must use Repositories.
- **API -> Service**: API handlers **never** contain business logic; they delegate to Services.
- **Engine Isolation**: Engines are pure functions/classes with no side effects (no DB access), making them testable and deterministic.

## 3. Deployment Assumptions
- **Containerization**: Docker for consistent environments (Dev/Prod parity).
- **Environment**: Linux/Unix-based runtime (but developed on Windows).
- **Database**: Supabase instances (Dev/Staging/Prod).
