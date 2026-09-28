# FADL PAY — General Integration API Contract V1

**Status:** DESIGN-ONLY / NOT IMPLEMENTED
**Version:** V1
**Provider model:** Provider-neutral
**Authority:** General Integration Contract V1 + Integration Database Schema Contract V1 + Authentication & Authorization Contract V1

---

## 1. Purpose

This document defines the design boundary for a future General FADL PAY Integration API.

It does **not** implement routes, database structures, credentials, external-provider connections, or transaction processing.

The API is intended to allow an authorized external integration to operate against an existing FADL PAY merchant account while preserving the existing Transaction Engine as the sole transaction-processing authority.

---

## 2. Provider Neutrality

The Integration API is provider-neutral.

It MUST NOT be designed around:

- FADL AI specifically
- a single external provider
- provider-specific credentials
- provider-specific transaction models
- provider-specific webhook semantics

External providers may be connected in a future phase through a separate provider adapter/integration boundary.

---

## 3. Integration Identity

Every integration request is associated with a dedicated:

- `integration_id`
- integration credential
- Integration → Merchant authorization context
- scope set

`integration_id` is NOT:

- `merchant_reference`
- `transaction_reference`
- Merchant API key
- browser session
- webhook secret

The Integration Identity is a separate authentication domain.

---

## 4. Candidate API Surface

The following routes are DESIGN CANDIDATES only.

### 4.1 Create Transaction

**POST**

`/api/v1/integrations/transactions`

Required authorization scope:

`transactions:create`

Expected request fields conceptually include:

- `merchant_reference`
- `amount`
- `currency`
- `customer_reference`
- `payment_method`
- `idempotency_key`

The final implementation MUST reuse the existing Transaction Engine.

No parallel transaction creation engine may be introduced.

---

### 4.2 Read Transaction

**GET**

`/api/v1/integrations/transactions/{transaction_reference}`

Required authorization scope:

`transactions:read`

`transaction_reference` remains the canonical transaction identifier.

The implementation MUST enforce Integration → Merchant authorization before returning transaction data.

---

### 4.3 Sandbox Transaction Status

**POST**

`/api/v1/integrations/transactions/{transaction_reference}/sandbox/status`

Required authorization scope:

`sandbox:status`

The implementation MUST reuse the existing sandbox status semantics and existing Transaction Engine.

No alternative status-transition model may be introduced.

---

## 5. Authentication Sequence

A future implementation should conceptually perform:

1. Receive integration credential.
2. Authenticate the integration credential.
3. Resolve `integration_id`.
4. Verify integration is active and not revoked.
5. Resolve the Integration → Merchant authorization.
6. Verify that authorization is active and not revoked.
7. Verify the required scope.
8. Verify merchant isolation.
9. Invoke the existing Transaction Engine.
10. Return the normalized API response.

Failure MUST stop before transaction processing.

---

## 6. Merchant Authorization

Integration authorization to merchants is separate from authentication.

An integration MUST NOT gain merchant access merely because the integration is authenticated.

The request must have an active Integration → Merchant authorization for the target merchant.

Cross-merchant access MUST be rejected.

The existing merchant identity remains authoritative.

No second merchant identity model may be introduced.

---

## 7. Scope Enforcement

The initial scope vocabulary is:

- `transactions:create`
- `transactions:read`
- `sandbox:status`

Scope checks MUST occur before the protected operation.

A request without the required scope MUST NOT invoke the Transaction Engine.

Future scopes may be introduced only through an explicit contract revision.

---

## 8. Transaction Engine Boundary

The Integration API MUST NOT create a second transaction engine.

All transaction creation must ultimately use the existing:

`create_transaction(...)`

All transaction reads must ultimately use the existing transaction retrieval mechanism.

Sandbox status changes must ultimately use the existing status-transition mechanism.

The existing transaction lifecycle remains authoritative.

---

## 9. Idempotency

Transaction creation MUST preserve the existing FADL PAY idempotency model.

The integration layer MUST NOT introduce an independent idempotency system.

A future implementation must preserve:

- `Idempotency-Key`
- request-hash behavior
- same-key/same-request replay behavior
- same-key/different-request rejection

The canonical transaction remains the existing `transaction_reference`.

---

## 10. Webhook Boundary

The Integration API MUST NOT replace or redefine existing webhook behavior.

Transaction status changes remain governed by the existing webhook/event system.

Webhook secrets remain separate from integration credentials.

The integration layer must not expose, replace, or reinterpret webhook secrets.

---

## 11. Error Model

A future implementation should normalize errors into a stable API structure.

Conceptual categories include:

- authentication failure
- integration inactive/revoked
- merchant authorization failure
- scope denied
- merchant isolation failure
- validation failure
- idempotency conflict
- transaction not found
- unsupported operation
- rate limit exceeded
- internal processing failure

The final HTTP status mapping must be defined during implementation.

This document does not authorize endpoint creation.

---

## 12. Rate Limiting

Integration requests MUST have a rate-limiting boundary separate from browser-session behavior.

Rate limiting MUST NOT bypass:

- integration authentication
- merchant authorization
- scope enforcement
- merchant isolation

Exact limits are implementation-phase decisions and are not defined by this design-only contract.

---

## 13. Audit Identity

Future Integration API activity must remain attributable to:

- `integration_id`
- target merchant
- requested operation
- transaction reference where applicable
- authorization/scope context where applicable

Raw credentials MUST NOT be written to logs or audit records.

Existing transaction/event identity remains authoritative for transaction history.

---

## 14. Credential Protection

Integration credentials MUST follow the Database Schema Contract and Authorization Contract.

Requirements include:

- raw reusable credentials are not stored in plaintext
- raw secret is displayed only at issuance where applicable
- normal reads must not recover the reusable secret
- raw credentials must not appear in logs
- integration credentials remain separate from Merchant API Keys
- integration credentials remain separate from browser sessions
- integration credentials remain separate from webhook secrets

Credential rotation/revocation is a future management concern.

---

## 15. Protected Existing Components

The future Integration API MUST NOT replace or modify the authority of:

- Existing Transaction Engine
- Existing Transaction API semantics
- Existing Idempotency mechanism
- Existing Webhook semantics
- Merchant API Key authentication
- Merchant browser sessions
- Merchant Login
- Payment UI
- Financial Admin

Integration is an additional authorization/access layer, not a replacement architecture.

---

## 16. Database Boundary

This contract does not authorize:

- SQLite migration
- CREATE TABLE
- ALTER TABLE
- INSERT
- UPDATE
- DELETE
- database writes
- credential generation
- schema deployment

The logical integration structures are defined separately by the authoritative Database Schema Contract V1.

---

## 17. Management API Boundary

Future management operations such as:

- integration creation
- credential issuance
- credential rotation
- credential revocation
- merchant authorization
- scope assignment
- integration disable/re-enable

require a separate implementation and authorization boundary.

They are NOT implemented by this contract.

---

## 18. External Provider Boundary

No external provider is connected by this contract.

Specifically:

- no FADL AI API
- no external API key
- no webhook registration
- no OAuth connection
- no provider adapter
- no external network integration

Provider connection is a future phase.

---

## 19. Non-Goals

This contract does NOT authorize:

- FastAPI route implementation
- endpoint creation
- database migration
- SQL execution
- SQLite modification
- transaction engine modification
- transaction schema modification
- Merchant API Key replacement
- Merchant Login modification
- browser-session replacement
- Payment UI modification
- Financial Admin modification
- webhook replacement
- GitHub push
- Render deployment
- external provider connection
- FADL AI connection

---

## 20. Implementation Preconditions

Implementation may begin only after explicit authorization and a separate implementation plan covering at minimum:

1. integration database migration
2. credential generation/storage protection
3. integration authentication
4. Integration → Merchant authorization
5. scope enforcement
6. merchant isolation
7. API route implementation
8. rate limiting
9. audit identity
10. integration management boundary
11. regression testing against protected components
12. rollback/checkpoint strategy

Implementation must begin from verified SAFE checkpoints.

---

## 21. Final Principle

The General Integration API is an additional controlled access layer.

It must preserve:

**Integration Identity → Authentication → Merchant Authorization → Scope Enforcement → Existing Transaction Engine**

while keeping:

**Merchant API Keys, Browser Sessions, Webhooks, Payment UI, Financial Admin, and Merchant Login**

as separate protected domains.

**Status: DESIGN COMPLETE / IMPLEMENTATION NOT AUTHORIZED**
