# Phase-1 Exclusions (What We Are NOT Building)

This document explicitly calls out features and capabilities that are **OUT OF SCOPE** for MaaV Solutions Phase-1. This is to ensure engineering focus on the core "Body" and prevent scope creep.

## 1. No Artificial Intelligence (AI)
- **Generative AI**: No LLM integration (GPT-4, Claude, Llama, etc.).
- **Natural Language Processing (NLP)**: No chatbots or conversational interfaces.
- **Predictive Analytics**: No ML-based forecasting.
- **Reason**: Phase-1 is strictly deterministic. AI will be layered later.

## 2. No ERI / Government Direct Filing
- **E-Filing Integration**: We will **NOT** integrate directly with the Income Tax Department's ERI API for automatic filing submissions.
- **JSON Utility**: We will generate the JSON payload required for filing, but the user must download and upload it manually to the government portal.
- **Status Sync**: No automatic fetching of acknowledgement/processing status from the government portal.

## 3. No GST Automation
- **GSTR Filing**: We will **NOT** support GST return filing (GSTR-1, GSTR-3B).
- **Invoice Sync**: No automatic fetching of invoices from the GST portal.
- **GST Reconciliation**: No automated GSTR-2A/2B matching.

## 4. No Payment Gateway
- **Tax Payments**: Users can calculate tax liability, but cannot pay it through the platform.
- **Subscription Billing**: No billing integration for using the platform itself (Phase-1 is free/demo or manual billing).

## 5. Limited ITR Scope
- **ITR Forms**: Focused primarily on **ITR-1 (Sahaj)** and basic **ITR-4 (Sugam)** structures.
- **Complex Forms**: **ITR-2** (Capital Gains complexity) and **ITR-3** (Business Professions with heavy auditing) are **EXCLUDED**.
- **Foreign Assets**: No support for reporting foreign assets (Schedule FA).

## 6. No Complex Workflows
- **Multi-User Collaboration**: No detailed workflow for multiple CAs working on a single file. (Strict 1 CA: 1 Filing assignment).
- **Document OCR**: No automated scanning of Form-16 PDFs (Manual entry or JSON import only).
