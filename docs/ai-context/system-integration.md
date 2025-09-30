# System Integration – Authentication & Security

This document records how the Voicerec backend secures user accounts and protects API access. It focuses on the authentication stack built in Part 2 of the roadmap and how other components should integrate with it.

## Authentication Architecture

| Component | Responsibility |
| --- | --- |
| `AuthService` (`backend/app/services/auth.py`) | Handles user registration and login. Applies bcrypt hashing and issues JWT access tokens. |
| Auth API (`backend/app/api/auth.py`) | Exposes `/auth/register` and `/auth/login` endpoints. Performs request validation and converts service responses to HTTP schemas. |
| Auth dependency (`backend/app/api/dependencies/auth.py`) | Validates `Authorization: Bearer` headers, decodes JWTs, and loads the associated user. Shared by all protected routes. |
| Settings (`backend/app/core/settings.py`) | Provides environment-driven secrets (JWT signing key, algorithm, expiry) and ensures safe defaults. |

All database access flows through repository classes (`UserRepository`, `MeetingRepository`, `TranscriptRepository`), maintaining a clean separation between HTTP handlers and persistence.

## User Lifecycle

1. **Registration (`POST /auth/register`)**
   - Accepts email and password (8–128 characters). Emails must be unique.
   - Passwords are hashed with `bcrypt` before storage. The hash (not the raw password) is persisted in the `users` table.
   - The service commits the transaction and returns the new user identifier and email.

2. **Login (`POST /auth/login`)**
   - Verifies credentials by comparing the supplied password to the stored bcrypt hash.
   - On success, returns a JWT access token and the `bearer` token type.
   - On failure, responds with HTTP 401.

User accounts are currently **managed internally**; there is no third-party SSO integration. Future migrations (e.g., SSO) should preserve these contracts or provide a compatibility layer.

## JWT Access Tokens

Tokens are created via `create_access_token` in `backend/app/core/security.py`.

- **Signing algorithm**: Configurable via `AUTH_TOKEN_ALGORITHM` (default `HS256`).
- **Secret key**: Must be provided through `AUTH_SECRET_KEY`. It is loaded from the `.env` file or environment variables and must be at least 16 characters long.
- **Lifetime**: Controlled by `AUTH_TOKEN_EXPIRE_MINUTES` (default 60). Tokens include `iat` and `exp` claims to enforce expiration.
- **Claims**:
  - `sub`: UUID of the authenticated user (required).
  - `email`: Included as an additional claim for convenience.
  - Standard JWT timestamps (`iat`, `exp`).

The backend does not issue refresh tokens. Clients must prompt the user to log in again when the access token expires.

## Request Authentication Flow

1. Protected endpoints (e.g., `/api/meeting/*`) depend on `get_current_user`.
2. FastAPI's `HTTPBearer` extracts the token. If the header is missing or malformed, the request fails with HTTP 401.
3. The dependency decodes the token using the configured secret and algorithm, validating expiration.
4. The `sub` claim is parsed as a UUID and used to load the user from the database.
5. If the user record no longer exists, the request fails with HTTP 403. Otherwise, the `User` model instance is returned to the route handler.

This flow ensures that token validation and authorization decisions are centralized. Service-layer code can assume the `current_user` is a valid domain object.

## Password Handling

- Password hashing uses `bcrypt.gensalt()` with automatically managed salts. No additional pepper is applied at this stage.
- Verification leverages `bcrypt.checkpw` and defensively guards against invalid hashes.
- Password hashes are stored as UTF-8 strings in the database.

**Do not store raw passwords** anywhere (logs, analytics, or temporary files). Logging is limited to high-level events; sensitive fields must be redacted if additional logging is introduced.

## Operational Guidelines

- **Transport security**: Deploy the API behind HTTPS in any environment that leaves local development. JWTs must never traverse unencrypted channels.
- **Secret management**: Store `AUTH_SECRET_KEY` (and future secrets) in a secure vault or managed secret store. Rotate secrets periodically; rotating requires reissuing tokens because previously signed tokens become invalid.
- **Token scope**: A single token currently grants access to all user-owned meetings. If fine-grained permissions are required, extend the payload with custom claims and enforce them in service logic.
- **Session invalidation**: Revocation is not implemented. To force logout, rotate the signing key or introduce a denylist table.
- **Timeout tuning**: Increase or decrease `AUTH_TOKEN_EXPIRE_MINUTES` based on UX and security policies. Shorter lifetimes reduce risk but require more frequent logins.

## Integration Checklist for New Features

- Protect any new user-specific endpoint with `Depends(get_current_user)`.
- Avoid duplicating password or token logic; always use utilities from `app.core.security`.
- When introducing background jobs or websockets, forward the same bearer token and validate it server-side.
- Update this document whenever authentication flows, token semantics, or security posture change.

