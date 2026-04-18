# Security Policy

## 🛡️ SolShare Security Vision
SolShare is committed to ensuring the security and privacy of energy data for both residents and providers. We follow a "Security by Design" approach, integrating automated testing and role-based isolation at the core of our infrastructure.

## 🚀 Supported Versions

Currently, the following versions of SolShare are receiving security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## 🔒 Implemented Security Features
As part of our commitment to safety, this repository includes:
*   **Role-Based Access Control (RBAC):** Strict isolation between Admin, Property Manager, and Resident views.
*   **Data Isolation:** Ownership verification in the API ensures users can only access their own energy readings.
*   **Automated Quality Gate:** A GitHub Actions CI pipeline that runs security tests on every Pull Request.
*   **Defensive Testing:** E2E Playwright tests covering token hijacking defense and logout persistence.

## 🐛 Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability within this project, please report it via one of the following methods:
1.  **Email:** Security reports should be sent to [security@solshare.com](mailto:security@solshare.com).
2.  **Acknowledgement:** You will receive an acknowledgement of your report within 48 hours.
3.  **Disclosure:** We follow a responsible disclosure policy. We ask that you do not disclose the vulnerability publicly until we have had a reasonable amount of time to address it.

## 🛡️ Secure Development Practices
This project uses the following tools to maintain security:
*   **Pytest:** For backend logic and math verification.
*   **Playwright:** For frontend E2E security flows.
*   **JWT (JSON Web Tokens):** For secure, stateless authentication.
*   **Argon2:** For industrial-strength password hashing.
