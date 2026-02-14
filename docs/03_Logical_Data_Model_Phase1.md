# Logical Data Model (LDM): Phase-1

## 1. Overview
The Logical Data Model (LDM) for MaaV Solutions Phase-1 is designed to support a robust tax filing workflow with strong auditability and clear ownership of financial records.

## 2. Core Entities & Relationships

### **2.1 User & Identity**
- **User**: The root entity. Represents an individual, business owner, CA, or Admin.
    - **Attributes**: `legal_name`, `email`, `pan`, `role`, `status`.
    - **Purpose**: Identity and Access Management.

### **2.2 Taxpayer Profile**
- **Taxpayer**: A distinct entity from User, representing the **tax persona**.
    - **Attributes**: `pan_type` (Individual, HUF, Firm), `residential_status`, `default_regime`.
    - **Relationship**: 1:1 with User. `user_id` is unique and mandatory.
    - **Why separate?**: Users manage the account; Taxpayers own the filing data. Allows CAs to be Users without being Taxpayers.

### **2.3 Financial Records (The "Source of Truth")**
- **Data Source**: Tracks the provenance of financial data (e.g., AIS import, Manual Entry).
    - **Attributes**: `source_type`, `reference_number`.
- **Income Record**: Granular income entries.
    - **Attributes**: `income_head` (Salary, Rent, Interest), `amount`, `financial_year`.
    - **Relationship**: Belongs to a **Taxpayer** and optionally links to a **Data Source**.
- **Business Entity**: Represents a business owned by a User (Sole Prop in Phase-1).
    - **Attributes**: `gstin`, `msme_status`.
    - **Relationship**: Belongs to a **User** (Owner).
- **Expense Record**: Business expenses.
    - **Attributes**: `category`, `amount`, `business_id` (FK), `msme_flag`.

### **2.4 Compliance & Filing Workflow**
- **Compliance Flag**: System-generated alerts based on rules.
    - **Attributes**: `rule_code`, `severity` (HARD/SOFT), `status` (OPEN/RESOLVED).
    - **Relationship**: Linked to **Taxpayer**.
- **Filing Case**: Represents a single tax filing journey for a specific Financial Year (FY).
    - **Attributes**: `financial_year`, `filing_mode` (SELF/CA), `current_state`.
    - **Relationship**: Many Filing Cases per Taxpayer (one per FY usually).
- **Submission Record**: Tracks attempts to submit a filing.
    - **Attributes**: `attempt_no`, `ack_number`, `status`.
    - **Relationship**: Belongs to a **Filing Case**.

### **2.5 Consent & Audit (Security Layer)**
- **Consent Artifact**: Explicit record of user consent for data operations.
    - **Attributes**: `purpose`, `scope`, `version`, `status` (ACTIVE/REVOKED).
    - **Relationship**: Linked to **User**.
- **User Confirmation**: Explicit sign-off on critical actions.
    - **Attributes**: `confirmation_type`, `ip_address`, `confirmed_at`.
    - **Relationship**: Links **User** to a specific context (e.g., Filing Case finalization).
- **Audit Log**: Immutable record of all data mutations.
    - **Attributes**: `actor_id`, `action`, `before_value`, `after_value`.
    - **Philosophy**: "Who did what, when, and from where."

## 3. Key Decisions
- **Separation of Concerns**: User identity is distinct from Taxpayer persona.
- **Explicit Provenance**: Every financial record links back to its origin (Data Source).
- **Auditability**: Every critical action requires a corresponding Audit or Confirmation record.
