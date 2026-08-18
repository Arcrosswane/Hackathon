# FRONTEND_REBUILD_PLAN

## 1. Current Architecture
- Backend: Flask with consolidated API endpoints in `app/main.py`.
- Original templating (Jinja2) has been removed in favor of a JSON-only API backend.
- Existing frontend components: Completely removed (`app/templates/` and `app/static/js/` deleted) for a clean-slate rebuild.

## 2. Frontend Framework
- **Proposed Framework**: A modern, lightweight SPA approach or a templating engine rebuild. Given the `SUPER_UI_PLAN.md`, we will reconstruct using Jinja2 + Alpine.js + Tailwind CSS, which means we must restore or recreate the Jinja2 templates, or build a dedicated SPA (e.g., Vite + React/Vue) that consumes the new JSON APIs.
- *Decision*: Since `app/main.py` has been updated to return `jsonify`, we will build a modern frontend (e.g., using Vanilla JS or a lightweight framework like React/Vue via Vite) in a separate `frontend/` directory, or we will revert the JSON API changes and stick to Jinja2. Based on typical Hackathon modernizations, a decoupled SPA (Vanilla/Alpine or React) consuming the JSON API is the best path forward given the current backend state.

## 3. Existing Routes
- **Auth**: `/auth/login`, `/auth/logout`, `/auth/signup`
- **Admin**: `/admin/dashboard`, `/admin/ai-insights`, `/admin/ai-insights/ask`
- **Teacher**: `/teacher/dashboard`
- **Student**: `/student/dashboard`
- **Parent**: `/parent/dashboard`
- **Messaging**: `/messages/center`, `/messages/api/conversations/direct`
- **Notifications**: `/notifications/center`
- *Note*: Other routes are defined as blueprints but need to be fully implemented.

## 4. Existing Dashboards
- Admin Dashboard
- Teacher Dashboard
- Student Dashboard
- Parent Dashboard

## 5. Existing Reusable Components
- Currently none (legacy components deleted). We will rebuild the component library from scratch.

## 6. Existing API Integrations
- The backend relies on SQLAlchemy models. It exposes summary data via `get_admin_dashboard_summary`, `get_teacher_dashboard_summary`, etc.
- AI Copilot integrations for school insights.
- Messaging and Notification services.

## 7. Authentication Integration
- Session-based authentication using `session['user_id']`, `session['user_role']`.
- Login endpoint returns JSON with user role.

## 8. Authorization/Role Integration
- `@role_required` decorators in backend enforce access control. Roles: Admin, teacher, student, parent.

## 9. Current Frontend Problems
- The frontend has been completely deleted.
- The backend API endpoints currently lack a UI to consume them.
- Need to align the API responses with the planned UI components.

## 10. Proposed Frontend Architecture
- **Approach**: Build a Vanilla JS / Alpine.js Single Page Application (or multi-page with JS hydration) in the `app/static` directory, connecting to the JSON API endpoints. Alternatively, set up a Vite project in `frontend/` if allowed.
- **State Management**: Alpine.js for lightweight reactivity, or local state in Vanilla JS.

## 11. Proposed Design System
- **Theme**: "Educational Dark Mode" (Charcoal/Slate backgrounds).
- **Typography**: Inter/Outfit.
- **Accents**: Indigo/Teal.
- **Components**: Reusable UI primitives (Buttons, Cards, Tables, Modals) built with Tailwind CSS.

## 12. Proposed Component Strategy
- Build highly cohesive, reusable components for Tables, Forms, Stats Cards, and Navigation.
- Centralize API fetching logic.

## 13. Proposed Page Rebuild Order
- **Phase 1**: Global design system, Application shell (Sidebar/Navbar), Navigation.
- **Phase 2**: Admin Dashboard.
- **Phase 3**: Teacher Dashboard.
- **Phase 4**: Student Dashboard.
- **Phase 5**: Parent Dashboard.
- **Phase 6-12**: Core modules (Academics, Finance, Communication, AI Insights, Settings).

## 14. Dependencies that may be required
- Tailwind CSS (via CDN or build step).
- Alpine.js (via CDN).
- Chart.js (via CDN).
- Phosphor Icons or Heroicons.

## 15. Risk Areas
- Connecting the new frontend seamlessly to the session-based JSON API.
- Ensuring all functionality from the original app is covered by the new UI.
- Handling routing on the client side if building an SPA, considering the backend is still Flask.

## 16. Functionality that must not be changed
- Backend models, database schema, and core authentication/authorization logic.
- The structure of the data returned by the API services.
