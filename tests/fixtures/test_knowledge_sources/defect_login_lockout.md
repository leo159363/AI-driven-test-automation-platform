# Defect: Login Lockout Counter Reset

source_type: defect

Observed issue:

The failed-login counter was not reset after a successful login.
Users who previously failed several attempts could be locked immediately after one later failure.

Regression checks:

- A successful login resets the failure counter.
- Lockout is calculated per account, not globally.
- Lockout audit logs include account id, client ip, and timestamp.
