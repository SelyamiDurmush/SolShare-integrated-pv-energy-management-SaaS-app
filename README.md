# ☀️ SolShare: Integrated Energy Management & Billing SaaS

[![Python](https://img.shields.io/badge/Python-3.9+-yellow?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5.0-ff3e00?logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0-003b57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

**SolShare** is a full-stack SaaS platform designed for multi-tenant residential and commercial buildings. It enables fair distribution and trading of rooftop solar (PV) energy, real-time usage tracking, and automated, transparent billing and payment.

---

## 🚀 Quick Start (Local Setup)

The fastest way to run SolShare locally without Docker:

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Setup Env & Seed DB
copy .env.example .env     # Linux/Mac: cp .env.example .env
python seed.py

# Start API
uvicorn app.main:app --reload
```
*API: `http://127.0.0.1:8000` | Docs: `http://127.0.0.1:8000/docs`*

### 2. Frontend (SvelteKit)
```bash
cd frontend
npm install
npm run dev
```
*App: `http://localhost:5173`*

---

## 💻 Technology Stack

### **Frontend**
- **Framework**: SvelteKit 5 (Runes) for reactive, high-performance UI.
- **Styling**: Tailwind CSS 4 for a modern, utility-first design system.
- **Visualization**: Chart.js for real-time energy production and consumption graphs.
- **Icons**: Lucide Svelte for accessible, clean iconography.

### **Backend**
- **Framework**: FastAPI (Python) for high-performance Async RESTful APIs.
- **ORM/DB**: SQLAlchemy with SQLite for reliable data persistence and modeling.
- **Security**: JWT (Jose) & Argon2 hashing for secure, role-based authentication.
- **Validation**: Pydantic v2 for robust data schema enforcement.

---

## 🔑 Test Accounts (After Seeding)

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@solshare.com` | `admin123` | Global management & system settings |
| **Property Manager** | `manager@solshare.com` | `manager123` | Assigned properties & residents |
| **Resident** | `resident1@solshare.com` | `resident123` | Personal usage and billing only |

---

## ✨ Key Features

- **Energy Sovereignty**: Track real-time solar production vs. consumption.
- **Fair Distribution**: Automated algorithms to distribute solar energy credits fairly.
- **Role-Based Access (RBAC)**: Distinct dashboards for Admins, Managers, and Residents.
- **Automated Billing**: Generates monthly statements based on actual meter readings.

---

## 🐳 Docker Setup (Optional)
Launch the entire stack with one command:
```bash
docker-compose up --build
```

---

## 📂 Architecture
- `backend/`: FastAPI Application, Models, and DB Migration Logic.
- `frontend/`: SvelteKit Application, UI Components, and Reactive State.
- `nginx/`: Production reverse proxy configuration.

---
*Developed by Selyami Durmus - [SolShare PoC](https://github.com/SelyamiDurmush/SolShare-integrated-pv-energy-management-SaaS-app)*
