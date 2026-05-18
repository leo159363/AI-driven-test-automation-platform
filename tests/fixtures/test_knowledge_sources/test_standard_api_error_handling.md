# Test Standard: API Error Handling

source_type: test_standard

API tests should cover status code, response schema, error code, error message, and trace id.
Security-sensitive APIs must avoid leaking internal exception details.

Checklist:

- Validate mandatory field errors.
- Validate invalid enum and boundary values.
- Validate authentication and authorization failures.
- Validate idempotency for repeated requests where applicable.
