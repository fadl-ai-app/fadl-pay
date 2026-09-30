# FADL PAY — General Integration Layer Contract V1

**Status:** Design Contract — Not Implemented  
**Scope:** Provider-neutral General Integration Layer  
**Implementation:** Not authorized by this document alone

---

## 1. Purpose

This contract defines the future General Integration Layer for FADL PAY.

The layer is intended to allow authorized external systems to connect to FADL PAY through a controlled, provider-neutral boundary.

Examples of possible external consumers include:

- merchant-owned applications
- e-commerce systems
- business platforms
- partner systems
- FADL AI, if authorized in the future
- other approved external systems

No specific external provider is privileged by this contract.

---

## 2. Core Architectural Rule

The General Integration Layer is **additive**.

It MUST NOT replace:

- the existing Merchant API Key authentication model
- the existing merchant identity boundary
- the existing Transaction Engine
- the existing transaction database model
- the existing Payment UI
- the existing Financial Admin
- the existing merchant browser session
- the existing webhook delivery semantics

The existing Transaction Engine remains the source of truth for transaction creation, retrieval, status transitions, idempotency, and transaction ownership.

---

## 3. Current System Boundary

Current implemented path:

    External HTTP request
            |
            v
    backend/api.py
            |
            v
    authenticate_api_key()
            |
            v
    authenticated merchant_reference
            |
            v
    Transaction Engine
            |
            v
    Existing database / transaction lifecycle

The current system has a Merchant API Key boundary.

It does NOT currently have a separate General Integration Credential boundary.

---

## 4. Future Integration Path

The future additive path is:

    External System
            |
            v
    General Integration Layer
            |
            v
    Integration Credential
            |
            v
    Integration Authorization
            |
            v
    Merchant Authorization
            |
            v
    Existing Merchant Boundary
            |
            v
    Existing Transaction API / Engine
            |
            v
    Existing Transaction Lifecycle

The Integration Layer MUST NOT bypass merchant authorization.

---

## 5. Integration Identity

A future integration SHOULD have a distinct identity from the merchant.

Conceptually:

    integration_id

The integration identity represents the external application/system.

It MUST NOT replace:

    merchant_reference

The relationship is:

    integration_id
          |
          v
    authorized merchant_reference

An integration may only act for merchants explicitly authorized to that integration.

No implementation of `integration_id` is part of V1.

---

## 6. Integration Credentials

A future integration credential SHOULD be separate from:

- Merchant API Keys
- Merchant browser sessions
- Webhook secrets

Conceptual distinction:

### Merchant API Key

Purpose:

    Authenticate an existing merchant API client.

### Integration Credential

Purpose:

    Authenticate an approved external integration identity.

### Webhook Secret

Purpose:

    Sign/verify webhook delivery.

These credentials MUST NOT be treated as interchangeable.

V1 does not define a concrete credential storage schema.

---

## 7. Credential Requirements

Any future Integration Credential implementation SHOULD provide:

- cryptographically secure generation
- one-way storage where appropriate
- credential status
- explicit ownership
- expiration capability where appropriate
- revocation
- rotation
- controlled one-time disclosure for secrets
- auditability

Raw credentials MUST NOT be logged.

Raw credentials MUST NOT be returned in ordinary authenticated API responses.

Credential issuance MUST NOT automatically grant access to every merchant.

---

## 8. Merchant Authorization

Integration authentication alone is insufficient.

The authorization chain MUST be:

    Integration
        |
        v
    Is integration credential valid?
        |
        v
    Is integration active?
        |
        v
    Is integration authorized for this merchant?
        |
        v
    Is requested operation allowed?
        |
        v
    Existing Transaction Engine

An external integration MUST NOT be able to choose an arbitrary merchant_reference merely by placing it in a request body.

Merchant identity must come from the authenticated/authorized boundary.

---

## 9. Scope / Permission Model

The future Integration Layer SHOULD support explicit scopes.

Illustrative scopes:

    transactions:create
    transactions:read
    transactions:sandbox_status

Additional scopes may be introduced later.

Scopes MUST be enforced server-side.

A client-provided scope or permission value MUST NOT grant itself permission.

V1 does not authorize implementation of any scope system.

---

## 10. Transaction Operations

The future Integration Layer may expose the capabilities already supported by the existing transaction system.

Current transaction capabilities include:

### Create

Existing engine operation:

    create_transaction(...)

### Read

Existing engine operation:

    get_transaction(...)

### Sandbox Status

Existing engine operation:

    update_transaction_status(...)

The Integration Layer MUST forward authorized operations to the existing transaction capability rather than implementing a second transaction engine.

---

## 11. Transaction Fields

The currently implemented transaction contract includes:

- merchant_reference
- amount
- currency
- customer_reference
- payment_method
- transaction_reference
- status
- idempotency_key
- created_at
- updated_at

The following MUST NOT be assumed to be current transaction fields merely because they may be useful for future integrations:

- country
- metadata

`environment` currently represents API/sandbox context and MUST NOT be treated as a persisted transaction field without a separate design decision.

`description` requires preservation of the existing implementation semantics and must not be redefined by the Integration Layer.

---

## 12. Transaction Reference

`transaction_reference` remains an FADL PAY-generated identifier.

The external integration MUST NOT manufacture or override an FADL PAY transaction reference during transaction creation.

Existing ownership checks remain authoritative.

---

## 13. Idempotency

Existing idempotency behavior MUST be preserved.

The future Integration Layer MUST:

- preserve the incoming idempotency key where applicable
- not silently replace it
- not weaken existing idempotency behavior
- not create a second conflicting idempotency mechanism

The Transaction Engine remains authoritative for transaction idempotency.

---

## 14. Merchant Isolation

A transaction belonging to Merchant A MUST NOT be readable or mutable through an integration authorized only for Merchant B.

Authorization MUST be checked before transaction data is returned or status is changed.

The Integration Layer MUST preserve the existing merchant ownership boundary.

---

## 15. Error Boundary

Future Integration endpoints SHOULD expose normalized external-facing errors.

Internal implementation details SHOULD NOT leak through public integration responses.

Examples of conceptual error classes:

- authentication_failed
- integration_inactive
- merchant_not_authorized
- scope_denied
- invalid_request
- idempotency_conflict
- transaction_not_found
- invalid_status_transition
- rate_limited

The exact HTTP mapping is intentionally deferred.

---

## 16. Rate Limiting

The future Integration Layer SHOULD support integration-aware rate limiting.

Rate limits SHOULD be attributable to the authenticated integration and, where appropriate:

- merchant
- endpoint
- operation

Rate limiting MUST NOT be implemented by bypassing existing authentication.

---

## 17. Audit Trail

A future Integration Layer SHOULD provide an auditable record of integration activity.

Conceptual audit information:

- integration identity
- merchant identity
- operation
- request outcome
- transaction reference when applicable
- timestamp
- request correlation identifier

Secrets and raw credentials MUST NOT be recorded.

A future audit design must define retention and access rules separately.

---

## 18. Webhooks

Existing webhook infrastructure remains separate.

The Integration Layer MAY use existing webhook capability.

It MUST NOT:

- redefine webhook secrets
- bypass SSRF validation
- replace webhook signing
- replace delivery retry semantics
- create a second webhook delivery engine

Webhook infrastructure remains a backend capability shared by authorized features.

---

## 19. Replay Protection

The current webhook signing system does not establish a general Integration API replay-protection mechanism.

A future Integration Layer SHOULD explicitly define:

- request timestamp handling
- nonce or request identifier where needed
- replay window
- duplicate-request behavior

This is a future security requirement and is not considered implemented by this contract.

---

## 20. Provider Neutrality

The Integration Layer MUST remain provider-neutral.

It MUST NOT contain architecture that assumes:

- FADL AI
- OpenAI
- Stripe
- PayPal
- Shopify
- or any other single provider

FADL AI, if integrated later, would be one authorized consumer of the general layer.

---

## 21. Protected Components

The following components are protected by this contract:

    payments/transaction_engine.py
    database/database.py
    app/payment_ui.py
    app/financial_admin.py
    app/financial_admin_ui.py
    app/merchant_dashboard.py
    backend/merchant_auth_routes.py
    security/merchant_session.py
    webhooks/service.py

Changes to these components require a separate audit and explicit implementation decision.

---

## 22. No Direct Database Coupling

The future Integration Layer SHOULD NOT implement transaction persistence independently.

It MUST use the existing application/service boundary.

The Integration Layer MUST NOT create a parallel transaction table merely for integrations.

Any future integration-specific persistence requires a separate schema design and migration review.

---

## 23. Credential Management API

The current system has internal API-key functions:

- generate_api_key()
- create_api_key()
- revoke_api_key()
- verify_api_key()

There is currently no public API-key creation/revocation endpoint.

The existing `/api-key-login` endpoint authenticates using an existing API key; it is not an API-key management endpoint.

Future integration credential issuance MUST be designed separately from `/api-key-login`.

---

## 24. Browser Merchant Sessions

Merchant browser sessions remain separate from integration credentials.

The Integration Layer MUST NOT reuse a browser session cookie as an external integration credential.

Likewise, an integration credential MUST NOT automatically create or impersonate a merchant browser session.

---

## 25. Sandbox and Production

The future Integration Layer SHOULD preserve explicit environment boundaries.

Existing sandbox operations must remain subject to the existing sandbox rules.

A future production integration capability requires an explicit security and environment design before implementation.

No production integration is authorized by V1.

---

## 26. Implementation Boundary

V1 authorizes the following as design principles only:

- separate integration identity
- separate integration credential concept
- integration-to-merchant authorization
- optional scopes
- integration-aware auditing
- integration-aware rate limiting
- preservation of existing idempotency
- forwarding to the existing transaction engine

V1 does NOT authorize:

- database schema changes
- credential issuance implementation
- new public API routes
- Transaction Engine modifications
- Payment UI changes
- Financial Admin changes
- merchant login changes
- webhook redesign
- external provider connection
- FADL AI connection
- GitHub push
- Render deployment

---

## 27. Security Invariants

The following invariants MUST remain true after any future implementation:

1. An external request cannot choose an unauthorized merchant.
2. Merchant identity cannot be overridden by request body data.
3. Transaction ownership remains enforced.
4. Existing idempotency remains enforced.
5. API credentials are never logged in raw form.
6. Integration credentials are separate from webhook secrets.
7. Webhook SSRF protections remain active.
8. Transaction Engine remains the transaction source of truth.
9. Financial Admin remains unchanged unless explicitly authorized.
10. Payment UI remains unchanged unless explicitly authorized.
11. Provider-neutral architecture is preserved.
12. No external integration is considered active until explicit authorization exists.

---

## 28. V1 Architecture Summary

    +---------------------------+
    |      External System      |
    +-------------+-------------+
                  |
                  v
    +---------------------------+
    | General Integration Layer |
    |                           |
    | Integration Identity      |
    | Credential Validation     |
    | Merchant Authorization    |
    | Scopes                    |
    | Rate Limits               |
    | Audit                     |
    +-------------+-------------+
                  |
                  v
    +---------------------------+
    | Existing Merchant         |
    | Authorization Boundary    |
    +-------------+-------------+
                  |
                  v
    +---------------------------+
    | Existing Transaction API  |
    +-------------+-------------+
                  |
                  v
    +---------------------------+
    | Transaction Engine        |
    +-------------+-------------+
                  |
                  v
    +---------------------------+
    | Existing Database         |
    +---------------------------+

Webhooks remain an adjacent existing capability.

---

## 29. Final Status

**GENERAL INTEGRATION LAYER V1: DESIGN ONLY**

Current implementation status:

- Merchant API Key authentication: IMPLEMENTED
- Merchant identity: IMPLEMENTED
- Transaction Engine: IMPLEMENTED
- Idempotency: IMPLEMENTED
- Webhooks: IMPLEMENTED
- Separate Integration Identity: NOT IMPLEMENTED
- Separate Integration Credentials: NOT IMPLEMENTED
- Integration-to-Merchant authorization: NOT IMPLEMENTED
- Integration scopes: NOT IMPLEMENTED
- Integration management API: NOT IMPLEMENTED
- External provider connection: NOT IMPLEMENTED

This document defines boundaries for future implementation.

It does not itself implement any integration capability.
