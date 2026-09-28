# FADL PAY — Integration Credential Transport Contract V1

## Status

**Version:** V1
**Status:** IMPLEMENTATION-READY TRANSPORT CONTRACT
**Provider model:** Provider-neutral

This document finalizes the HTTP transport boundary for the
General FADL PAY Integration Credential.

## 1. Canonical Transport

Authorization: Bearer <integration_credential_secret>
X-Integration-ID: <integration_id>
X-Credential-ID: <credential_id>
X-Merchant-Reference: <merchant_reference>

For transaction creation only:

Idempotency-Key: <idempotency_key>

## 2. Credential Secret Rules

The reusable integration credential MUST be transported through
the Authorization header using the HTTP Bearer authentication scheme.

The raw credential:
- MUST NOT be placed in a URL.
- MUST NOT be placed in a query parameter.
- MUST NOT be placed in the transaction JSON body.
- MUST NOT be written to application logs.
- MUST NOT be written to audit records.
- MUST NOT be returned in normal API responses.

## 3. Integration Identity

X-Integration-ID identifies the Integration Identity.
The supplied identifier MUST NOT by itself authenticate the request.

The server MUST resolve and validate the corresponding Integration
record before protected operations proceed.

## 4. Credential Identity

X-Credential-ID identifies the dedicated Integration Credential record.
The credential MUST belong to the authenticated Integration Identity.

The credential identifier is not itself a secret.

## 5. Merchant Authorization

X-Merchant-Reference identifies the requested merchant context.

The supplied merchant reference MUST be checked against the active
Integration to Merchant authorization.

An integration authorized for Merchant A MUST NOT gain access to
Merchant B merely by changing X-Merchant-Reference.

Cross-merchant access MUST be rejected.

## 6. Authorization Order

Integration Credential
-> Integration Identity
-> Integration Status
-> Merchant Authorization
-> Required Scope
-> Existing Transaction Engine

Authentication and authorization MUST occur before protected
transaction operations.

## 7. Initial Scopes

transactions:create
transactions:read
sandbox:status

The required scope is determined by the requested operation.
Clients MUST NOT grant themselves scopes through request data.

## 8. Transaction Creation

POST /api/v1/integrations/transactions

Required headers:
Authorization: Bearer <integration_credential_secret>
X-Integration-ID: <integration_id>
X-Credential-ID: <credential_id>
X-Merchant-Reference: <merchant_reference>
Idempotency-Key: <idempotency_key>

JSON body:
amount
currency
customer_reference
payment_method

Required scope: transactions:create

## 9. Transaction Read

GET /api/v1/integrations/transactions/{transaction_reference}

Required headers:
Authorization: Bearer <integration_credential_secret>
X-Integration-ID: <integration_id>
X-Credential-ID: <credential_id>
X-Merchant-Reference: <merchant_reference>

Required scope: transactions:read

Merchant authorization MUST be established before transaction data
is returned.

## 10. Sandbox Status

POST /api/v1/integrations/transactions/{transaction_reference}/sandbox/status

Required headers:
Authorization: Bearer <integration_credential_secret>
X-Integration-ID: <integration_id>
X-Credential-ID: <credential_id>
X-Merchant-Reference: <merchant_reference>

Required scope: sandbox:status

Merchant ownership MUST be checked before the status operation.

## 11. Credential Domain Separation

Integration Credentials remain separate from:
- Merchant API Keys
- Browser Sessions
- Webhook Secrets
- Transaction References
- Merchant Identity

No credential type may silently substitute for another.

## 12. Transaction Engine Boundary

The Integration API is an additional authorization and access layer.

It MUST NOT replace or modify the existing Transaction Engine.

After successful authentication, Integration status validation,
merchant authorization, and scope enforcement, the operation is
delegated to the existing Transaction Engine using the authorized
merchant_reference.

## 13. Storage Boundary

This transport contract does not change the database schema.

The reusable secret MUST NOT be stored in plaintext.

The dedicated storage field is:
integration_credentials.credential_hash

Integration Credentials remain separate from:
api_keys.key_hash

## 14. Audit and Logging

Raw reusable credentials MUST NEVER appear in logs or audit records.

Permitted non-secret audit identity may include:
- integration_id
- credential_id
- merchant_reference
- operation
- scope
- transaction_reference where applicable
- timestamp

The raw Authorization header MUST NOT be logged.

## 15. Compatibility Boundary

This contract does not modify:
- Merchant API Key authentication
- Merchant browser authentication
- Merchant Login
- Financial Admin
- Payment UI
- Webhooks
- Existing Transaction Engine
- Existing transaction ownership rules
- Existing idempotency mechanism

The Integration API is additive.

## 16. Final Contract

Canonical protected request transport:

Authorization: Bearer <integration_credential_secret>
X-Integration-ID: <integration_id>
X-Credential-ID: <credential_id>
X-Merchant-Reference: <merchant_reference>

Create operation additionally requires:

Idempotency-Key: <idempotency_key>

This document finalizes the transport boundary for subsequent
Integration V2 runtime implementation.
