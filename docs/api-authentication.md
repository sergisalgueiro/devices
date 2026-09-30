# Technical Proposal: API Authentication & Access Control Architecture

> **Document Type**: Architecture & Engineering Specification  
> **Status**: Proposed  
> **Scope**: User Identity Management, Role-Based Access Control (RBAC), and IoT Edge Device Ingestion Authentication  
> **Target Systems**: FastAPI Async Core, PostgreSQL 17, Redis, Edge Hardware Fleet

---

## Table of Contents

- [Technical Proposal: API Authentication \& Access Control Architecture](#technical-proposal-api-authentication--access-control-architecture)
  - [Table of Contents](#table-of-contents)
  - [1. Executive Summary \& Architectural Scope](#1-executive-summary--architectural-scope)
  - [2. User Plane: Dual-Token Architecture (JWT + Refresh Token)](#2-user-plane-dual-token-architecture-jwt--refresh-token)
    - [2.1 Leveraging JWT Payload Claims](#21-leveraging-jwt-payload-claims)
    - [2.2 Authentication \& Token Lifecycle](#22-authentication--token-lifecycle)
    - [2.3 Role-Based Access Control (RBAC)](#23-role-based-access-control-rbac)
  - [3. Device Plane: Pre-Shared Device API Keys](#3-device-plane-pre-shared-device-api-keys)
    - [3.1 Ingestion Pipeline (`X-Device-Token`)](#31-ingestion-pipeline-x-device-token)
    - [3.2 Request Context Enrichment](#32-request-context-enrichment)

---

## 1. Executive Summary & Architectural Scope

This specification defines the authentication and authorization architecture for the IoT Fleet Management API. The system operates on two decoupled planes that enforce distinct operational guarantees:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                IDENTITY PLANES                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

     HUMAN / USER PLANE                                      DEVICE / FLEET PLANE
┌───────────────────────────────┐                       ┌───────────────────────────────┐
│ Web Dashboard / Mobile Client │                       │ Autonomous IoT Hardware Node  │
└───────────────┬───────────────┘                       └───────────────┬───────────────┘
                │                                                       │
   OAuth2 / Bearer JWT + Cookie                            Header: X-Device-Token
                ▼                                                       ▼
┌───────────────────────────────┐                       ┌───────────────────────────────┐
│ User Auth Middleware / Guard  │                       │ Device Ingestion Guard        │
│ - Signature Verification      │                       │ - Key Hash Lookup (Redis/DB)  │
│ - Scope & RBAC Enforcement    │                       │ - Context Enrichment          │
└───────────────┬───────────────┘                       └───────────────┬───────────────┘
                │                                                       │
                ▼                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI APPLICATION CORE                                 │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

1. **User Plane**: Manages human operators, fleet administrators, and customers. Employs a **Dual-Token Architecture (Short-Lived JWT Access Token + Long-Lived Rotating Refresh Token)**.
2. **Device Plane**: Manages autonomous hardware sensors streaming time-series measurements. Employs **Pre-Shared Device API Keys (`X-Device-Token`)** with server-side context enrichment.

---

## 2. User Plane: Dual-Token Architecture (JWT + Refresh Token)

Human users (customers and administrators) authenticate using a dual-token model:
- **Access Token (JWT)**: A short-lived token (15 minutes) sent in the `Authorization: Bearer <token>` header with every API request.
- **Refresh Token**: A long-lived token (30 days) stored securely in an `HttpOnly` cookie, used exclusively to renew the Access Token without requiring the user to re-enter credentials.

### 2.1 Leveraging JWT Payload Claims

Rather than treating the access token as an opaque reference, we embed essential identity and authorization data directly into the **JWT payload claims**:

- **User Identity (`sub`)**: The unique UUID of the authenticated user.
- **Tenant Context (`customer_id`)**: The ID of the customer account they belong to.
- **Roles & Permissions (`roles`)**: The user's assigned role (`platform_admin`, `fleet_operator`, `customer_user`).

**Key Architectural Benefit**:  
Because the JWT is cryptographically signed by our authentication service, downstream API endpoints can trust and extract these claims directly from the token. Endpoints know immediately who the caller is, what permissions they have, and which customer tenant they belong to **without querying the database or cache on every single request**.

### 2.2 Authentication & Token Lifecycle

- **Authentication (`POST /api/v1/auth/login`)**:
  - The client submits user credentials (email and password).
  - The server verifies credentials against the stored password hash (Argon2id).
  - On success, the server returns the short-lived JWT in the response body and sets a long-lived Refresh Token in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie.
- **Silent Renewal (`POST /api/v1/auth/refresh`)**:
  - When the Access Token expires, the client calls the refresh endpoint with the cookie attached.
  - The server validates the refresh token, performs **Refresh Token Rotation (RTR)** (issuing a new refresh token and invalidating the previous one), and returns a fresh Access Token.
  - If a previously used refresh token is presented, the server detects a potential replay attack and immediately revokes all sessions for that user.
- **Termination (`POST /api/v1/auth/logout`)**:
  - The server marks the active refresh token as revoked and clears the client cookie.

### 2.3 Role-Based Access Control (RBAC)

Endpoints inspect the `roles` claim embedded in the token to authorize operations:
- `platform_admin`: Unrestricted platform access; device provisioning, customer lifecycle management.
- `fleet_operator`: Read/write access to operational telemetry, device state, and diagnostic routines.
- `customer_user`: Scoped access restricted strictly to devices owned by the customer.

---

## 3. Device Plane: Pre-Shared Device API Keys

### 3.1 Ingestion Pipeline (`X-Device-Token`)

Physical hardware devices authenticate directly using unique **Pre-Shared API Keys** attached to the HTTP header:

```http
POST /api/v1/devices/550e8400-e29b-41d4-a716-446655440000/measurements HTTP/1.1
Host: api.fleet.domain.com
X-Device-Token: dev_sec_7f9c3b8a1e2d4f5a6b0c9e8d7a6f5e4d
Content-Type: application/json

{
  "measured_at": "2026-09-30T17:30:00Z",
  "measurements": [
    {"type": "temperature", "value": 21.4, "unit": "celsius"}
  ]
}
```

1. **Provisioning**: Each device is assigned a unique, high-entropy secret key during manufacturing or registration.
2. **Secure Hashed Storage**: The database never stores plaintext keys—only a secure keyed hash (`HMAC-SHA256`).
3. **High-Speed Cache**: Active key hashes are cached in Redis to validate incoming measurements in sub-milliseconds without database overhead.

### 3.2 Request Context Enrichment

When a valid `X-Device-Token` is received, the authentication dependency automatically injects an immutable `VerifiedDeviceContext` into the request:

$$\text{VerifiedDeviceContext} = \{\text{device\_id}, \text{serial\_number}, \text{device\_type}, \text{customer\_id}, \text{is\_active}\}$$

Downstream command handlers consume this verified context directly, recording measurements without needing secondary database queries to look up device attributes.
