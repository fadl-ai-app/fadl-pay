# FADL PAY — Integration Authentication, Authorization & Scopes Contract V1

## Status

**DESIGN CONTRACT — NOT IMPLEMENTED**

This contract defines the future authentication, merchant authorization,
and scope model for the general FADL PAY Integration Layer.

The model is provider-neutral.

FADL AI is only one possible future external consumer.
Any authorized external system must use the same security boundary.

No database migration is authorized by this document.
No SQLite table is created by this document.
No API endpoint is created by this document.
No external provider is connected by this document.

Source Schema Contract SHA256:

`96da993a37dfaacde6399396c78f644990072ba6efd51c19f1b2d07ff06ca4d1`

---

# 1. Architectural Boundary

Future request flow:

External System
→ General FADL PAY Integration Layer
→ Integration Authentication
→ Integration Identity
→ Integration → Merchant Authorization
→ Scope Authorization
→ Existing Merchant Boundary
→ Existing Transaction API / Transaction Engine

The Integration Layer is additive.

It does not replace:

- Merchant Login
- Browser Sessions
- Merchant API Keys
- Merchant identity
- Transaction Engine
- Payment UI
- Financial Admin
- existing webhook semantics

---

# 2. Integration Identity

Every external integration has a distinct identity.

Canonical identifier:

`integration_id`

Rules:

- `integration_id` identifies the external integration.
- It is unique across integrations.
- It is distinct from `merchant_reference`.
- It is distinct from `transaction_reference`.
- It is distinct from Merchant API Keys.
- It is distinct from Browser Sessions.
- It is distinct from Webhook Secrets.
- A client-supplied identifier cannot substitute for authenticated identity.

The authenticated `integration_id` must come from validated Integration
Credential state.

---

# 3. Integration Credentials

The Integration Layer uses a dedicated credential type.

Relationship:

`integration_id → integration credential`

Integration credentials are separate from:

- Merchant API Keys
- Browser Session tokens
- Webhook Secrets
- transaction references
- merchant identity

No credential type may silently substitute for another.

Credential lifecycle must support:

1. issuance
2. activation
3. authentication
4. rotation
5. revocation
6. optional expiration

---

# 4. Credential Protection

Raw integration credentials:

- must not be stored in plaintext;
- must not be logged;
- must not appear in ordinary API responses;
- must not be recoverable through normal application reads;
- should be displayed only once at issuance when required.

Only a protected representation suitable for later verification may be
persisted.

A revoked or expired credential must not authenticate a new request.

---

# 5. Authentication Sequence

Future Integration Layer processing:

1. Receive external request.
2. Extract Integration Credential.
3. Validate credential.
4. Resolve authenticated `integration_id`.
5. Check integration status.
6. Resolve requested merchant.
7. Check Integration → Merchant Authorization.
8. Check requested scope.
9. Enforce existing merchant isolation.
10. Invoke existing transaction capability.
11. Record audit identity.

Authentication must happen before protected transaction operations.

A client must not authenticate by merely supplying an arbitrary
`integration_id`.

---

# 6. Integration Lifecycle

Future integration status:

- `active`
- `disabled`
- `revoked`

### Active

May authenticate with valid credentials.

### Disabled

Must not authenticate new protected requests.

### Revoked

Must not authenticate new protected requests.

Disabling or revoking an integration does not delete or rewrite
historical transactions.

---

# 7. Existing Merchant Identity

The existing merchant identity remains authoritative.

The Integration Layer uses:

`merchant_reference`

as the merchant identity boundary.

The Integration Layer must not create a second merchant identity model.

The external integration is not itself a merchant.

One integration may be authorized for multiple merchants.

One merchant may authorize multiple integrations.

---

# 8. Integration → Merchant Authorization

Authorization is an explicit relationship:

`integration_id`
+
`merchant_reference`

An authenticated integration is not automatically authorized for every
merchant.

Authorization must be independently revocable.

For every protected request:

`authenticated integration`
+
`requested merchant`
+
`active authorization`

must resolve successfully.

Cross-merchant access must be rejected.

---

# 9. Authorization Lifecycle

Future authorization status:

- `active`
- `disabled`
- `revoked`

### Active

Allows operations subject to scopes.

### Disabled

Blocks new protected operations for that merchant.

### Revoked

Blocks new protected operations for that merchant.

Historical transactions remain unchanged.

---

# 10. Merchant Context Protection

Client-supplied merchant identifiers must never override the authenticated
authorization boundary.

If a merchant reference is supplied by the client, it must be checked
against authenticated Integration → Merchant authorization.

Authorization for Merchant A does not authorize Merchant B.

---

# 11. Scope Model

Scopes define permitted operations within an Integration → Merchant
authorization context.

Initial scopes:

- `transactions:create`
- `transactions:read`
- `sandbox:status`

Scopes belong to the authorization context.

The same integration may have different scopes for different merchants.

Example:

Integration X → Merchant A → create + read

Integration X → Merchant B → read only

Read access for Merchant B must not become write access.

---

# 12. Scope Enforcement

Required order:

Authentication
→ Integration Status
→ Merchant Authorization
→ Scope Check
→ Existing Merchant Boundary
→ Existing Transaction Capability

A missing scope rejects the operation.

A scope cannot grant access to a merchant for which no active authorization
exists.

---

# 13. Initial Scope Semantics

## transactions:create

Allows creation of a transaction for an authorized merchant.

The existing Transaction Engine remains authoritative.

No parallel transaction engine is permitted.

## transactions:read

Allows reading transactions belonging to the authorized merchant,
subject to existing merchant isolation.

The existing `transaction_reference` remains canonical.

## sandbox:status

Allows the existing sandbox status operation for an authorized merchant,
subject to existing status-transition rules.

The Integration Layer does not redefine transaction status semantics.

---

# 14. Existing Transaction Boundary

The Integration Layer authenticates and authorizes the request and then
uses the existing transaction capability.

The existing Transaction Engine remains the source of truth for:

- transaction creation
- transaction references
- status
- validation
- merchant isolation
- idempotency
- lifecycle

No second transaction engine is authorized.

---

# 15. Existing Idempotency Boundary

The Integration Layer must not create a parallel idempotency system.

Existing idempotency remains authoritative.

Integration transaction creation must ultimately use the existing
transaction/idempotency path.

The same payment transaction must not receive a competing transaction
identity because it arrived through an integration.

---

# 16. Merchant API Keys

Merchant API Keys remain a separate existing authentication mechanism.

Integration Credentials must not silently become Merchant API Keys.

Merchant API Keys must not silently become Integration Identities.

Credential types remain explicit and non-interchangeable.

---

# 17. Browser Sessions and Merchant Login

Existing Merchant Login remains protected and unchanged.

Existing Browser Sessions remain separate.

An Integration Credential must not become a browser session.

A browser session must not silently authenticate an external integration.

Merchant Login modification or replacement is outside this contract.

---

# 18. Webhook Boundary

Existing webhook semantics remain authoritative.

The Integration Layer does not replace:

- webhook endpoints
- webhook secrets
- webhook signatures
- webhook delivery
- webhook events

Webhook Secrets must not be used as Integration Credentials.

---

# 19. Audit Identity

Future audit records should distinguish:

- `integration_id`
- `merchant_reference`
- credential reference where appropriate
- operation
- scope
- transaction reference where applicable
- outcome
- timestamp

Raw reusable credentials must never appear in audit records.

Audit identity must distinguish:

External Integration
vs
Merchant API
vs
Browser Session
vs
Internal/System operation

---

# 20. Error Model

Future Integration API errors should distinguish:

- missing credential
- invalid credential
- expired credential
- revoked credential
- disabled integration
- missing merchant authorization
- disabled merchant authorization
- revoked merchant authorization
- missing scope
- cross-merchant access
- invalid transaction request
- existing transaction/idempotency error

Error responses must never disclose reusable credentials or protected
credential representations.

---

# 21. Rate Limiting Boundary

Future rate limiting may distinguish:

- integration
- merchant authorization
- operation
- credential
- network context

Rate limiting is an additional control.

It does not replace authentication, authorization, or scope enforcement.

---

# 22. Credential Rotation

Rotation must preserve:

- `integration_id`
- merchant identity
- transaction history
- transaction references

Rotation must not create a new merchant identity.

Any overlap period must have explicitly defined lifecycle rules.

Revoked credentials must cease authenticating new requests.

---

# 23. Authorization Revocation

Revoking an Integration → Merchant authorization blocks new protected
operations for that merchant.

It must not:

- delete transactions
- rewrite transaction history
- change historical merchant ownership
- alter transaction references
- modify Financial Admin records

---

# 24. Provider Neutrality

The Integration Layer is not designed exclusively for FADL AI.

Potential consumers include:

- FADL AI
- another application
- a merchant-owned system
- an authorized third-party platform
- an authorized internal service

All must pass through the same Integration security boundaries.

No provider receives implicit privilege.

---

# 25. Protected Components

The following remain protected:

- Merchant Login
- Browser Sessions
- Merchant API Keys
- Merchant identity
- Transaction Engine
- transaction_reference
- existing idempotency
- webhook semantics
- Payment UI
- Financial Admin
- transaction history

The Integration Layer is additive.

---

# 26. Future Management Boundary

A future management API may support:

- integration creation
- integration disable/revoke
- credential issuance
- credential rotation
- credential revocation
- Integration → Merchant authorization
- authorization disable/revoke
- scope grant/revoke

These are design-only operations.

No management endpoint is created by this contract.

---

# 27. Non-Goals

This contract does not authorize:

- SQLite migration
- CREATE TABLE
- ALTER TABLE
- INSERT / UPDATE / DELETE
- credential generation
- API endpoint creation
- Transaction Engine modification
- Merchant API-Key replacement
- Merchant Login modification or replacement
- Browser Session replacement
- webhook replacement
- Payment UI modification
- Financial Admin modification
- GitHub push
- Render deployment
- external provider connection
- FADL AI connection
- production integration activation

---

# 28. Implementation Preconditions

Before implementation:

1. Credential format must be finalized.
2. Credential transport must be finalized.
3. Credential hashing/protection must be reviewed.
4. Credential lifecycle must be finalized.
5. Integration lifecycle must be finalized.
6. Merchant authorization lifecycle must be finalized.
7. Scope semantics must be finalized.
8. Error contract must be finalized.
9. Rate-limiting policy must be finalized.
10. Audit model must be finalized.
11. Database migration/rollback strategy must be finalized.
12. A fresh SAFE checkpoint must exist immediately before implementation.

This contract alone does not authorize implementation.

---

# 29. Final Security Principle

Authenticate the integration.

→ Identify the integration.

→ Authorize the merchant relationship.

→ Authorize the requested scope.

→ Enforce the existing merchant boundary.

→ Use the existing transaction capability.

→ Preserve existing transaction, idempotency, webhook, Payment UI,
Financial Admin, Browser Session, and Merchant Login semantics.

## Final Status

**DESIGN ONLY — NOT IMPLEMENTED**

No database was modified by this document.
No SQLite operation was performed by this document.
No production application was modified by this document.
No GitHub operation was performed by this document.
No Render deployment was performed by this document.
No UI or Financial Admin was modified by this document.
