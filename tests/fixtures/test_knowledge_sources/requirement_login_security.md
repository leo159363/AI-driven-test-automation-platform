# Requirement: Login Security Controls

source_type: requirement

The login module must support username and password authentication.
After five consecutive failed attempts within ten minutes, the account should be temporarily locked.
The system must return a readable error message without exposing whether the username exists.

Testing focus:

- Successful login with valid credentials.
- Invalid password and empty credential handling.
- Lockout threshold and lockout recovery.
- Error message consistency and audit logging.
