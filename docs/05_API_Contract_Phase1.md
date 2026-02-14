# API Contract: Phase-1

## 1. Principles
- **RESTful**: Resource-based URLs (`/users`, `/taxpayers`, `/filings`).
- **Stateless**: All state managed via standardized tokens (Bearer JWT).
- **JSON**: All request/response bodies are JSON.
- **Validation**: Strict Pydantic models for input/output.

## 2. Base URL
`https://api.maav.solutions/api/v1`

## 3. Core Resource Groups

### **3.1 Authentication & User**
- `POST /auth/login`: Basic login (Email/Password or OTP).
- `POST /auth/refresh`: Refresh access token.
- `GET /users/me`: Current user profile.
- `PUT /users/me`: Update profile details.

### **3.2 Taxpayer Management**
- `POST /taxpayers`: Create a new Taxpayer Profile.
- `GET /taxpayers/{id}`: Retrieve profile.
- `GET /taxpayers/{id}/compliance`: Get active compliance flags.

### **3.3 Financial Records (The Ledger)**
- `POST /incomes`: Add income record.
- `GET /incomes`: List incomes (filter by FY, Source).
- `POST /expenses`: Add business expense.
- `GET /expenses`: List expenses.

### **3.4 Filing Workflow**
- `POST /filings`: Initiate a new filing case for a FY.
- `GET /filings/{id}`: Get filing status.
- `PUT /filings/{id}/state`: Transition state (Draft -> Review -> Submitted).
- `POST /filings/{id}/confirm`: User confirmation (Digital Sign simulation).

### **3.5 Audit & Consent**
- `POST /consent`: Grant specific data access consent.
- `GET /audit/logs`: View audit history (Admin/User specific).

## 4. Error Handling
Standardized error responses:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Taxpayer profile not found for ID: ...",
    "details": { ... }
  }
}
```

## 5. Security Headers
- `Authorization`: `Bearer <token>`
- `X-Request-ID`: Traceability ID.
- `X-Client-Version`: Version control.
