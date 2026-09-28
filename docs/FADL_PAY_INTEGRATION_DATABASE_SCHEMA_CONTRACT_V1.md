# FADL PAY — Integration Database Schema Contract V1

## Status

**DESIGN CONTRACT — NOT IMPLEMENTED**

This document defines the proposed database boundary for the future
General Integration Layer.

No database migration is authorized by this document.

No SQLite table is created by this document.

---

# 1. Design Objective

The Integration database boundary must provide four distinct capabilities:

1. Integration identity.
2. Integration credential lifecycle.
3. Explicit Integration → Merchant authorization.
4. Explicit integration scopes.

The design must remain additive to the existing FADL PAY database.

---

# 2. Existing Database Boundary — Protected

Existing tables remain authoritative:

- merchants
- customers
- transactions
- transaction_events
- api_keys
- countries
- currencies
- idempotency_keys
- ledger_entries
- merchant_countries
- supported_currencies
- webhook_deliveries
- webhook_endpoints
- merchant_password_setup_tokens

The Integration Layer must not replace or duplicate these tables.

In particular:

- `merchants` remains the merchant identity source.
- `api_keys` remains the Merchant API Key source.
- `transactions` remains the transaction source of truth.
- `transaction_events` remains the transaction event source.
- `idempotency_keys` remains the idempotency source.
- webhook tables remain the webhook source of truth.

---

# 3. Proposed Integration Tables

The proposed Integration boundary contains four logical tables:

    integrations
    integration_credentials
    integration_merchant_authorizations
    integration_scopes

These are design objects only.

---

# 4. integrations

## Purpose

Represents the external integration identity.

Candidate logical fields:

- `id`
- `integration_id`
- `name`
- `status`
- `created_at`
- `updated_at`

## Identity

`integration_id` is the stable public identifier of the integration.

`integration_id` must be unique across all integrations.

It is not:

- merchant_reference
- transaction_reference
- API key
- browser session
- webhook secret

## Status

Candidate states:

- active
- disabled
- revoked

The final status model must be confirmed during implementation.

## Ownership

The `integrations` table identifies the integration itself.

Merchant authorization is deliberately stored separately so one integration
can be explicitly authorized for more than one merchant.

---

# 5. integration_credentials

## Purpose

Stores authentication credentials associated with an integration.

Candidate logical fields:

- `id`
- `credential_id`
- `integration_id`
- `credential_hash`
- `status`
- `created_at`
- `updated_at`
- `expires_at`
- `revoked_at`

Optional fields must be implemented only if required by the final
credential lifecycle.

## Security Rules

Raw credential values must not be stored in plaintext.

The raw secret should be displayed only once at credential issuance, when the final credential design permits it. It must not be recoverable from normal application reads afterward.

Normal API responses must never return the reusable secret.

Logs must not contain raw credential values.

Credential hashes must be protected as sensitive authentication material.

## Lifecycle

The future credential model should support:

- issuance
- activation
- revocation
- rotation
- optional expiration

A revoked credential must not authenticate an integration.

`credential_id` must be unique across all integration credentials.


---

# 6. integration_merchant_authorizations

## Purpose

Represents explicit authorization between an integration and a merchant.

Candidate logical fields:

- `id`
- `integration_id`
- `merchant_reference`
- `status`
- `created_at`
- `updated_at`

## Relationship

One integration may be authorized for multiple merchants.

Conceptually:

    Integration A
       ├── Merchant A
       ├── Merchant B
       └── Merchant C

A merchant may also have multiple authorized integrations.

Conceptually:

    Merchant A
       ├── Integration A
       ├── Integration B
       └── Integration C

This creates a many-to-many authorization boundary.

## Authorization Rule

Authentication of an integration does not automatically authorize access
to every merchant.

Every operation must resolve:

    authenticated integration
              +
    requested merchant
              +
    active authorization

The authorization record is the source of truth for whether the integration
may act for that merchant.

---

# 7. integration_scopes

## Purpose

Represents the capabilities granted to an integration authorization.

Candidate logical fields:

- `id`
- `integration_merchant_authorization_id`
- `scope`
- `created_at`

## Initial Scopes

The initial design recognizes:

    transactions:create
    transactions:read
    sandbox:status

Future scopes may be added without changing the Transaction Engine.

## Important Boundary

Scopes belong to the authorization context.

This means an integration may have different permissions for different
merchants.

Example:

    Integration A → Merchant A
        transactions:create
        transactions:read

    Integration A → Merchant B
        transactions:read

The implementation must enforce the effective scope for the specific
Integration → Merchant authorization. Therefore, the same integration may have different permissions for different merchants.

---

# 8. Relationship Model

Logical relationship:

    integrations
          |
          | 1:N
          v
    integration_credentials


    integrations
          |
          | N:M
          v
    integration_merchant_authorizations
          |
          | 1:N
          v
    integration_scopes


Expanded:

    +----------------------+
    |    integrations      |
    |----------------------|
    | integration_id       |
    | name                 |
    | status               |
    +----------+-----------+
               |
        +------+------+
        |             |
        v             v
credentials    merchant_authorizations
                    |
                    v
                  scopes

Merchant authorization points to the existing:

    merchants.merchant_reference

No duplicate merchant identity is introduced.

---

# 9. Merchant Identity

The existing merchant identity remains authoritative.

The Integration Layer must not create a second merchant identity model.

The logical relationship is:

    integration_merchant_authorizations.merchant_reference
                              |
                              v
                     existing merchants
                              |
                              v
                     merchant_reference

The exact foreign-key implementation must be verified against the existing
database conventions before migration.

---

# 10. Credential Isolation

Integration credentials are separate from:

### Merchant API Keys

Existing:

    api_keys

Purpose:

    Merchant API authentication.

### Browser Sessions

Existing merchant session mechanisms remain separate.

Purpose:

    Browser authentication.

### Webhook Secrets

Existing:

    webhook_secret

Purpose:

    Webhook signing and verification.

### Integration Credentials

Future:

    integration_credentials

Purpose:

    External Integration Layer authentication.

No credential type may silently substitute for another.

---

# 11. Transaction Boundary

The new tables must not duplicate:

- transactions
- transaction_events
- idempotency_keys
- ledger_entries

The Integration Layer authenticates and authorizes a request, then passes
the authorized request into the existing transaction capabilities, including the existing transaction creation path.

Logical flow:

    integration credential
            |
            v
    integration authorization
            |
            v
    scope check
            |
            v
    existing merchant boundary
            |
            v
    existing Transaction Engine

---

# 12. Transaction Identity

The existing:

    transaction_reference

remains the canonical transaction identifier.

The Integration Layer must not introduce a second transaction identifier
for the same payment transaction.

`integration_id` identifies the external integration.

`merchant_reference` identifies the merchant.

`transaction_reference` identifies the transaction.

Each identifier has a distinct purpose.

---

# 13. Idempotency Boundary

Existing idempotency behavior remains authoritative.

The Integration Layer must not create a parallel idempotency system.

The request must ultimately use the existing:

    idempotency_key

and existing transaction-engine request-hash behavior.

Merchant isolation remains part of idempotency semantics.

---

# 14. Uniqueness Requirements

The final schema should enforce logical uniqueness where appropriate.

Candidate requirements:

### Integration

`integration_id` must be unique.

### Credential

`credential_id` must be unique.

### Integration → Merchant

An active authorization should not have duplicate identical
Integration → Merchant relationships.

Candidate logical uniqueness:

    integration_id + merchant_reference

### Scope

A scope should not be duplicated within the same authorization.

Candidate logical uniqueness:

    integration_merchant_authorization_id + scope

Exact SQLite constraints must be designed and reviewed before migration.

---

# 15. Status and Revocation

The final implementation must distinguish between:

- active
- disabled
- revoked

where the lifecycle requires those distinctions.

A disabled integration must not authenticate new requests.

A revoked credential must not authenticate requests.

A disabled merchant authorization must not authorize transaction operations.

Existing transactions are not deleted or modified merely because an
integration or authorization is disabled.

---

# 16. Auditability

Future Integration operations should be attributable to:

- integration_id
- merchant_reference
- operation
- scope
- credential identity without exposing raw secret
- transaction_reference when applicable
- timestamp
- outcome

Audit storage must not duplicate transaction history.

Transaction lifecycle remains in the existing transaction event system.

---

# 17. Security Invariants

The implementation must guarantee:

1. Raw integration credentials are never stored in plaintext.
2. Revoked credentials cannot authenticate.
3. Disabled integrations cannot authenticate new requests.
4. Disabled merchant authorizations cannot authorize operations.
5. Scope checks occur before protected transaction operations.
6. Merchant ownership is enforced server-side.
7. Client-supplied merchant identifiers cannot override authorization.
8. Cross-merchant transaction access is rejected.
9. Existing transaction idempotency remains authoritative.
10. Existing transaction_reference remains canonical.
11. Existing webhook secrets remain separate.
12. Browser sessions remain separate.
13. Merchant API Keys remain separate.

---

# 18. Database Migration Boundary

No SQLite migration is authorized by this contract.

When implementation is eventually approved:

- existing tables must remain intact
- existing data must remain intact
- migration must be additive
- migration must be reversible where practical
- schema changes must be backed up
- migration must be tested against a copy before production
- production database writes require explicit approval

No migration is authorized by this document.

---

# 19. Non-Goals

This schema contract does not authorize:

- SQLite migration
- CREATE TABLE execution
- ALTER TABLE execution
- INSERT / UPDATE / DELETE
- credential generation
- API endpoint creation
- transaction engine modification
- merchant API-key replacement
- Merchant Login modification or replacement
- webhook replacement
- Payment UI modification
- Financial Admin modification
- GitHub push
- Render deployment
- external provider connection

---

# 20. Implementation Prerequisites

Before schema implementation:

1. Contract V2 must remain approved.
2. Credential format must receive a dedicated security review.
3. Integration status lifecycle must be finalized.
4. Merchant authorization lifecycle must be finalized.
5. Scope semantics must be finalized.
6. SQLite foreign-key behavior must be verified.
7. Existing database conventions must be reviewed.
8. Migration and rollback strategy must be designed.
9. A fresh SAFE checkpoint must exist before migration.
10. Existing Payment UI and Financial Admin must remain unchanged.

---

# 21. Final Design Principle

The Integration database stores the identity and authorization boundary.

It does not become a second payment database.

It does not become a second merchant database.

It does not become a second transaction engine.

It answers:

    Which integration is this?
    Which credentials authenticate it?
    Which merchants authorized it?
    What scopes does it have for each merchant?

After authorization, the request continues through the existing FADL PAY
transaction capabilities.

**Status: DESIGN ONLY — NOT IMPLEMENTED**
