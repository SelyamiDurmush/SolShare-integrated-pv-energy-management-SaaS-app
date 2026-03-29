# Shared Building Supply Energy Distribution and Payment Integration System

## Project Understanding

**Core Objective**: Build a system that manages shared rooftop PV (solar panel) systems in multifamily buildings, distributing energy fairly among individual apartments and handling transparent billing + online payments.

**Target Users**: Property managers and HOAs managing small-to-mid multifamily buildings (5-100 units) with rooftop solar installations.

## Key Functions

* **Energy Distribution**: Track and allocate solar energy production across individual apartment units
* **Transparent Billing**: Generate accurate monthly/yearly bills based on actual energy consumption
* **Payment Processing**: Handle online payments for energy bills
* **Real-time Monitoring**: Dashboard showing energy production, distribution, and consumption
* **Fair Allocation**: Ensure equitable energy distribution among building residents

## System Scope

* Shared PV array on building rooftop
* Individual apartment metering/consumption tracking
* Energy co-op model where residents share the solar generation
* Multi-building support for property managers managing multiple properties

## Architecture \& Core Components

* **Creating Bills**: Generate transparent monthly/yearly bills based on energy distribution
* **Auth/Authorization**: Google OAuth + Email/Password + standardized IDPs (OpenID Connect)
* **Alerts**: System reminders, abnormal consumption detection
* **APIs**: Connectors to inverter/meter vendors for real-time data ingestion
* **Data Storage**: PostgreSQL + TimescaleDB for energy readings and billing data
* **UI/Visualization**: Energy usage dashboards with interactive graphs and maps
* **Legal/Compliance**: Support for regulations and billing compliance
* **On-demand/Regular Billing**: Flexible billing schedules

## Tech Stack (Confirmed)

* **Backend**: FastAPI + pvlib-python (solar calculations) + SQLAlchemy ORM
* **Database**: PostgreSQL + TimescaleDB extension (for time-series energy data)
* **Frontend**: Svelte (Tailwind CSS) + Recharts/Victory (graphs) + Leaflet/Google Maps
* **Auth**: FastAPI-Users or Authlib for OAuth + email/password
* **APIs**: Connectors for inverter/meter vendors

## Project Status \& Approach

* **Stage**: MVP (Minimum Viable Product) - Prototype for demonstration
* **Market**: Germany
* **Regulatory Framework**: Energy Communities \& Shared Building Supply (Gemeinschaftliche Gebäudeversorgung)

### Key Points

* ✓ Architecture defined (FastAPI + Svelte (Tailwind CSS) + SQLAlchemy ORM + PostgreSQL + TimescaleDB)
* ✓ Bill calculation logic - TBD (placeholder ready for future integration)
* ✓ Payment processing - TBD (Stripe integration ready for future)
* ✓ Meter/Inverter connectors - TBD (API framework ready for vendors)
* ✓ Compliance - TBD (prototype stage, full compliance in production)

### Approach

* Build scalable, maintainable architecture with clear separation of concerns
* Create interfaces/abstractions for bill calculation, payment processing, and vendor APIs
* Implement core MVP features (user management, energy tracking, basic dashboards)
* Ensure easy integration points for future modules
* Write comprehensive tests for existing functionality

## Key Regulatory Insight: Shared Building Supply Model

* **Legal Basis**: Energy Industry Act, Section 42b (April 2024 amendments)
* **Core Concept**: Solar electricity from rooftop PV distributed among apartment residents without passing through public grid
* **Operator Exemptions**: Largely exempt from traditional energy supplier obligations (no transparency requirements, no electricity labeling, minimal consumer protection obligations)
* **Required Obligations**: Must inform consumers about allocation formula and residual electricity; must notify DSO about allocation method
* **15-minute meter intervals**: Smart meter data every 15 minutes (mandatory from 2025 for >6,000 kWh/year consumers)
* **Two allocation methods**:

  * **Static**: Fixed share per apartment per quarter-hour
  * **Dynamic**: Pro-rata allocation based on real-time consumption
* **Quarterly billing**: Bills issued every 3 months
* **Residual electricity**: Separate billing for non-solar consumption
* **Voluntary participation**: Residents can opt-in/opt-out freely; max 2-year contract terms

## Implementation Phases

### Phase 1: Refactor backend

* PostgreSQL + TimescaleDB for 15-minute meter readings
* Building electricity usage contract management
* Allocation formula engine (static \& dynamic - placeholders ready for integration)
* Quarterly billing period management
* Consumer participation tracking

### Phase 2: Build Frontend

* Building \& apartment management
* Meter reading visualization (15-minute intervals)
* Allocation formula configuration
* Consumer dashboard (allocated vs. residual electricity)
* Quarterly billing preview

### Phase 3: Testing \& Documentation

* Comprehensive pytest tests
* Compliance audit trail
* DSO reporting templates

## Component Checklist

* Database Models - User, Building, Apartment, MeterReading, Contracts, Allocation, etc.
* Pydantic Schemas - Request/response validation
* Authentication Service - Password hashing, JWT, Google OAuth
* Allocation Engine - Static \& dynamic allocation algorithms
* FastAPI Routes - All API endpoints
* Frontend - Dashboard, management pages, visualizations
* Tests - pytest coverage
* Documentation - Architecture, deployment, compliance guide

