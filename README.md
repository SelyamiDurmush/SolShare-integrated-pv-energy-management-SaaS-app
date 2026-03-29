# SolShare Energy Management Application (PoC)

An integrated energy management platform built for multi-tenant buildings to share solar PV production equitably and distribute energy bills fairly based on static or dynamic allocation algorithms.

## 🚀 Technology Stack

- **Frontend**: SvelteKit 5 (Runes), Tailwind CSS, Chart.js, Lucide Icons
- **Backend**: FastAPI (Python), SQLAlchemy, SQLite (default)
- **Architecture**: Decoupled Client-Server architecture with REST API

---

## 💻 Local Development Setup

Follow these steps to get the SolShare project running on your local machine.

### 1. Backend Setup (FastAPI)

The backend runs on Python and provides all the REST APIs and database modeling. It uses a local SQLite database by default (`solshare.db`), so no external database server is required.

Make sure you have **Python 3.9+** installed.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the Python dependencies
pip install -r requirements.txt

# Seed the database with demo values
# This creates the tables and inserts a property manager, 5 residents, and 30 days of simulated energy readings.
python seed.py

# Run the development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API will run at `http://127.0.0.1:8000`. 
*Tip: You can view the automatically generated interactive Swagger API documentation at `http://127.0.0.1:8000/docs`.*

### 2. Frontend Setup (SvelteKit)

The frontend is a SvelteKit application built with reactive Runes.

Make sure you have **Node.js (v18+)** installed.

```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```
The client application will be instantly accessible at `http://localhost:5173`.

---

## 🔑 Default Test Accounts (After Seeding)

Once you've run the `seed.py` script on the backend, the following default accounts are available to test the Role-Based Access Control (RBAC):

**1. System Administrator**
- **Email**: `admin@solshare.com`
- **Password**: `admin123`
- **Access**: Full global access to all buildings, system alerts, user management, and billing statements across the entire platform.

**2. Property Manager**
- **Email**: `manager@solshare.com`
- **Password**: `manager123`
- **Access**: Restricted to their assigned properties. Can manage apartments, view building-scoped alerts, and browse specialized billing.

**3. Resident**
- **Email**: `resident1@solshare.com` (available up to `resident5@solshare.com`)
- **Password**: `resident123`
- **Access**: Strictly restricted. Can only view energy usage, alerts, and billing statements associated with their personal apartment.

---

## 🏗️ Core Directory Structure

```text
SolShare/
├── backend/                 # Python/FastAPI Application
│   ├── app/
│   │   ├── api/v1/          # Route controllers (Billing, Analytics, Alerts, Users)
│   │   ├── core/            # Configuration, JWT Security auth, Database session
│   │   ├── models/          # SQLAlchemy Database Models (Buildings, Apartments, Users, Meters, Alerts)
│   │   └── schemas/         # Pydantic data validation schemas
│   ├── seed.py              # Generates dummy data and historical meter readings
│   └── requirements.txt     # Python dependencies list
└── frontend/                # Node/SvelteKit Application
    ├── src/
    │   ├── lib/             # UI Components (Cards, Buttons), Utils, Shared State Stores (e.g. user.svelte.ts)
    │   └── routes/          # SvelteKit App pages
    │       ├── (app)/       # Authenticated layout wrapper (Sidebar, Header)
    │       │   ├── dashboard/ 
    │       │   ├── buildings/ 
    │       │   ├── billing/ 
    │       │   └── alerts/  
    │       └── login/       # Public unauthenticated route
    ├── tailwind.config.ts   # Tailwind styling configurations
    └── package.json         # Node.js dependencies list
```
