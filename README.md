# StratLearn — School Management & Learning Platform

**StratLearn** is a modular, enterprise-grade school management and learning platform built with **Python Flask**, **Flask-SQLAlchemy**, **MySQL**, **Jinja2**, and **Tailwind CSS**.

---

## 📋 Comprehensive Modules & Functionality Guide

---

### 🔑 Module 1 — Authentication & Role Management

#### Core Objective
Provides secure, role-based access control and user account management across four primary school user roles: **Admin**, **Teacher**, **Student**, and **Parent/Guardian**.

#### Detailed Functionality
- **Universal Sign-In Portal (`/auth/login`)**:
  - Centralized login interface for all user roles.
  - Validates credentials against hashed passwords stored in the database.
  - Automatically redirects users to their role-specific dashboard upon successful authentication (`/admin/dashboard`, `/teacher/dashboard`, `/student/dashboard`, `/parent/dashboard`).
- **Universal Sign-Up Portal (`/auth/signup`)**:
  - Self-registration interface supporting Students, Staff/Teachers, and Parents.
  - Allows registration code matching (e.g. matching registration numbers like `4838` or `PAR001`) to automatically link new portal user accounts to existing student or guardian entities.
- **Server-Side Session Security & RBAC**:
  - Implements custom Python decorators `@login_required` and `@role_required(*roles)`.
  - Protects administrative routes against unauthorized access, throwing custom 403 Forbidden errors if a student, parent, or non-admin attempts unauthorized route access.
  - Password hashing handled securely via `werkzeug.security`.

---

### 🏫 Module 2 — School Setup & General Settings

#### Core Objective
Establishes the foundational school identity, manages multi-year academic sessions, and provides a centralized system configuration store.

#### Detailed Functionality
- **School Profile Setup (`/admin/school`)**:
  - Manages school branding name, tagline, official email, phone numbers, website URL, affiliation board (e.g. CBSE, ICSE, State Board), and physical postal address.
  - Supports custom school logo image uploads (`/static/uploads/logos/`) which dynamically inject into master application navigation layouts and document headers.
- **Academic Session Management (`/admin/settings/sessions`)**:
  - Enables creation and configuration of academic sessions (e.g. `2025–2026`, `2026–2027`).
  - Designates the active academic session system-wide. All class enrollments, timetables, homework assignments, behaviour records, and fee structures filter automatically against the selected active session.
- **System Settings Key-Value Store**:
  - Centralized service (`Setting` model and `setting_service.py`) for managing global platform key-value settings.

---

### 🎒 Module 3 — Classes & Sections

#### Core Objective
Structures the academic grade hierarchy and section allocations for organizing student groups.

#### Detailed Functionality
- **Academic Classes Catalog (`/admin/academics/classes`)**:
  - Manages grade levels (e.g. Grade 1 through Grade 12, Pre-Primary).
  - Configures numeric sorting order (`numeric_order`), class descriptions, and active/archived operational statuses.
- **Section Allocation**:
  - Creates and manages sections attached to classes (e.g. Grade 9 — Section A, Section B).
  - Configures section display names, student capacity limits, and assigns primary **Class Teachers** from the staff directory.
- **Class Hierarchy Integrity**:
  - Prevents orphaned sections and preserves historical class structures even when sections are updated.

---

### 📚 Module 4 — Subjects & Subject Assignment

#### Core Objective
Defines academic subject offerings and maps subject responsibilities to classes and teachers.

#### Detailed Functionality
- **Master Subject Catalog (`/admin/academics/subjects`)**:
  - Creates and manages subjects (e.g., Mathematics, Physics, Chemistry, English Literature, World History, Physical Education).
  - Assigns unique subject codes (e.g. `MATH-101`, `PHY-201`), subject types (`Theory`, `Practical`, `Co-Curricular`), and pass mark criteria.
- **Subject-to-Class Allocations (`/admin/academics/subjects/assignments`)**:
  - Junction mapping (`subject_classes` table) connecting subjects to specific classes and sections.
  - Assigns primary subject teachers to each class-subject pairing along with weekly credit hours.

---

### 👨‍🏫 Module 5 — Employees & Staff Management

#### Core Objective
Maintains the complete staff directory, teacher profiles, department structures, and employee portal user accounts.

#### Detailed Functionality
- **Staff Directory (`/admin/employees`)**:
  - Roster of all school employees with real-time text search and department filtering.
- **Comprehensive Staff Profiles**:
  - Stores first name, middle name, last name, employee ID / code, department (Academic, Administration, Sports, Science, Accounts), designation (Senior Teacher, Head of Department, Principal, Lab Assistant), and employment type (Full-time, Part-time, Contract).
  - Captures contact details, alternate phone numbers, email addresses, residential address, city, state, country, and postal code.
  - Supports staff avatar photo uploads (`/static/uploads/employees/`).
- **Teacher Classification & Portal User Mapping**:
  - Flags staff members as active teachers (`is_teacher = True`), enabling them to be assigned to classes, subjects, timetables, homework, and behaviour assessments.
  - Admin credentials interface to generate or reset staff portal login credentials.

---

### 🎓 Module 6 — Students & Student Management

#### Core Objective
Manages complete student profiles, admission records, academic enrollment history, and student portal credentials.

#### Detailed Functionality
- **Student Directory (`/admin/students`)**:
  - Roster of all enrolled students with search by name or registration number, and filtering by Class and Section.
- **Detailed Student Profile (`/admin/students/<id>`)**:
  - Captures full student demographic information: registration number, admission date, date of birth, gender, blood group, medical notes, home address, city, state, postal code, and guardian contact details.
  - Supports student profile photo avatar uploads (`/static/uploads/students/`).
- **Historical Academic Enrollments (`student_enrollments` table)**:
  - Tracks historical student placements across academic sessions, classes, sections, and roll numbers (`is_current = True/False`).
  - Preserves past academic placement history when students are promoted or transferred to new sections.
- **Student Portal Credentials Manager**:
  - Admin tools on student directory cards and profile pages to view, generate, or reset student portal login credentials (`username` / `password`).
  - Displays a visual **Portal Account Badge** (`Registered` vs. `No Login`) on student directory cards.

---

### 👨‍👩‍👧 Module 7 — Parent & Guardian Management

#### Core Objective
Maintains guardian records and links parents to their enrolled children for family portal monitoring.

#### Detailed Functionality
- **Guardian Directory (`/admin/guardians`)**:
  - Roster of all registered parents and guardians with contact details and active statuses.
- **Guardian Profiles**:
  - Captures guardian full name, registration code (e.g. `PAR001`), occupation, primary mobile phone, alternate phone, email address, home address, city, state, and postal code.
- **Guardian-Student Relationships (`guardian_students` table)**:
  - Multi-child linking enabling a single parent account to be connected to multiple students (e.g. a parent with children in Grade 6 and Grade 9).
  - Assigns relationship types (Father, Mother, Legal Guardian, Local Guardian) and primary contact flags.
- **Parent Portal Credentials Manager**:
  - Admin tools on parent directory cards and profile pages (`/admin/guardians/<id>`) to generate or reset parent portal login credentials (`username` / `password`).
  - Displays a visual **Portal Account Status Badge** (`Registered` vs `No Login Account`) on parent profile and directory cards.

---

### 📅 Module 8 — Timetable Management

#### Core Objective
Provides an interactive weekly schedule matrix builder with real-time conflict detection and period time slot management.

#### Detailed Functionality
- **Period Time Slot Manager (`/admin/academics/timetables/periods`)**:
  - Defines daily period time slots per academic session (e.g., Period 1: 08:00–08:45, Period 2: 08:45–09:30, Recess: 12:00–12:45).
  - Configures period names, order numbers, start/end times, and period types (`CLASS`, `BREAK`, `ASSEMBLY`, `LAB`).
- **Weekly Schedule Matrix Grid (`/admin/academics/timetables`)**:
  - Interactive grid displaying Monday through Saturday timetable slots for any selected class and section.
- **Real-Time Conflict Detection Engine**:
  - Server-side algorithm (`check_conflicts()`) that automatically checks three conflict types before saving any timetable slot:
    1. **Teacher Conflict**: Prevents a teacher from being assigned to two different classes at the same day and period.
    2. **Room Conflict**: Prevents room double-booking for the same time slot.
    3. **Class Overlap**: Prevents assigning multiple subjects to the same class section simultaneously.
- **Draft vs. Published Workflow**:
  - Allows admins to build timetables in `DRAFT` status before publishing.
  - Published timetables (`PUBLISHED`) become visible on Student and Teacher dashboards.

---

### 📝 Module 9 — Homework Management

#### Core Objective
Facilitates teacher assignment creation, student task submissions, material file uploads, and automated AI answer grading.

#### Detailed Functionality
- **Teacher Assignment Manager (`/homework/manage`)**:
  - Teachers create homework assignments specifying Title, Description / Questions, Class, Section, Subject, Assigned Date, Due Date, and Maximum Marks.
  - Supports uploading learning materials and solution attachments (`/static/uploads/homework/attachments/`) in PDF, DOCX, PPTX, PNG, JPG, and ZIP formats (up to 10MB).
- **Student Submission Portal (`/homework/student`)**:
  - Students view eligible assignments assigned to their class and section.
  - Students submit work by typing text answers and/or uploading solution files (`/static/uploads/homework/submissions/`).
  - **Submission Lock Guard**: Assignments already submitted by a student automatically hide the submission form and display a **"✓ Homework Already Submitted"** status panel displaying their submitted text, attachment download link, and evaluation status.
- **Dual Evaluation Modes (`MANUAL` vs `AI`)**:
  - Teachers select whether an assignment is graded manually or automatically by AI during assignment creation.
- **Google Gemini AI Evaluation Engine**:
  - Integrated with **Google Gemini 1.5 Flash REST API**.
  - When set to `AI` mode or when the teacher clicks **"🤖 Run AI Auto-Grading"**, the service sends the assignment question, teacher rubric/answer key, student text response, and solution file metadata to Gemini.
  - Gemini evaluates the submission against pedagogical rubrics, assigns a numerical mark out of `max_marks`, writes detailed feedback for the student, and provides staff reasoning explaining why those marks were awarded.
  - Includes intelligent offline fallback scoring if API limits are reached.
- **Parent Homework Tracker (`/homework/parent`)**:
  - Allows parents to monitor upcoming, submitted, reviewed, and overdue/missing assignments for all linked children.

---

### 🌟 Module 10 — Behaviour & Skills Management

#### Core Objective
Records, monitors, and evaluates non-academic student growth, conduct observations, and core skill competencies independently from academic marks and attendance.

#### Detailed Functionality
- **Non-Academic Student Growth Focus**:
  - Operates completely separate from academic marks, exams, and attendance to foster holistic student development.
- **Configurable Behaviour Categories (`/behaviour-skills/categories`)**:
  - Admin interface to create and archive custom observation categories (e.g. Positive Conduct, Classroom Participation, Teamwork, Respect, Punctuality, Discipline) without hardcoded frontend restrictions.
- **Behaviour Observations Roster & Builder (`/behaviour-skills/behaviour`)**:
  - Staff record student observations classified into three structured types: `POSITIVE` (e.g. helping peers), `OBSERVATION` (general conduct), or `IMPROVEMENT` (constructive growth areas).
  - Supports impact severity ratings (`LOW`, `MEDIUM`, `HIGH`) and detailed observation context notes.
- **Configurable Skill Definitions (`/behaviour-skills/skills`)**:
  - Admin interface to define core non-academic skills grouped by domain (e.g., Communication, Social/Teamwork, Thinking/Analytical, Self-Management).
- **Single & Class Bulk Skill Assessments (`/behaviour-skills/assessments`)**:
  - Staff rate student competency levels on a standardized 1 to 5 scale:
    - `1 — Needs Significant Improvement`
    - `2 — Developing`
    - `3 — Satisfactory`
    - `4 — Good`
    - `5 — Excellent`
  - **Class Bulk Rating Portal (`/behaviour-skills/assessments/bulk`)**: Teachers can select a class and skill criteria to rate an entire class roster on a single screen efficiently.
- **Server-Side Visibility Permissions & IDOR Security**:
  - Supports four visibility levels: `INTERNAL` (staff-only private notes), `STUDENT_VISIBLE`, `PARENT_VISIBLE`, and `BOTH`.
  - Server-side role filtering guarantees that private staff notes (`INTERNAL`) are completely hidden from Student and Parent views.
  - Server-side IDOR validation verifies `GuardianStudent` links (parents can only view their own child's records) and teacher-class assignments.
- **Student Development Summary Profile Card (`/behaviour-skills/summary/<id>`)**:
  - Visual summary profile displaying observation totals, positive vs. improvement breakdown counts, recent history timeline, average skill ratings, and historical competency progress over time.

---

### 💵 Module 11 — Fees & Fee Management

#### Core Objective
Builds a complete school Fee Management system for defining fee structures, issuing student invoices, recording payments, generating receipts, tracking dues, and providing parents and students with read-only visibility into their fee accounts.

#### Detailed Functionality
- **School Fees Scope & Boundaries**:
  - Manages school fees, fee structures, student fee assignments, invoice demands, payment recording, official receipt generation, and collection metrics.
  - Operates independently from general accounting ledgers and employee payroll (which belong to future modules), while structuring payment records so future accounting modules can consume them cleanly.
- **Configurable Fee Types (`/fees/types`)**:
  - Admins configure global fee types (e.g., Tuition Fee, Admission Fee, Examination Fee, Library Fee, Activity Fee, Transport Fee, Computer Fee, Sports Fee, Miscellaneous Fee).
- **Fee Structures & Components Catalog (`/fees/structures`)**:
  - Defines expected annual/term fees per class and academic session.
  - Attaches line components (`FeeComponent`) specifying component amounts, due dates, and frequencies (`YEARLY`, `HALF_YEARLY`, `QUARTERLY`, `MONTHLY`, `ONE_TIME`).
- **Immutable Fee Invoices & Demands (`/fees/invoices`)**:
  - Generates student fee invoices with unique human-readable numbers (e.g. `INV-2026-000123`).
  - Preserves exact line items (`FeeInvoiceItem`), subtotals, discounts, and total payable upon issuance. When an admin later updates a fee structure, previously issued invoices remain intact without altering historical financial data.
  - Supports **Single Student Invoice Generation** and **Batch Class Invoice Generation**.
- **Discount & Concession Engine**:
  - Supports approved fee discounts and concessions (e.g. Merit Scholarships, Sibling Concessions, Staff-Child Concessions).
  - Captures discount amounts, reasons, and staff approver records.
- **Full, Partial & Self-Service Online Payments (`/fees/pay/<invoice_id>`)**:
  - **Student & Parent Self-Service Payment Gateway**: Students and Parents can pay their pending fee invoices directly from their dashboard (`/fees/my-account`, `/fees/child/<student_id>`) via UPI, Credit/Debit Card, Net Banking, or Online Portal.
  - **Admin Offline Payment Recording**: Admins generate invoices and record manual offline cash/cheque counter payments (`/fees/payments/record`).
  - Automatically updates invoice `paid_amount` and calculates status (`PARTIALLY_PAID` vs `PAID`).
- **Server-Side Overpayment & Balance Protection**:
  - All balance calculations (`payable = subtotal - discount`, `outstanding = payable - paid_amount`) are enforced strictly server-side.
  - Payments exceeding the outstanding balance or attempted on paid/cancelled invoices are rejected.
- **Supported Payment Methods & References**:
  - Supports `CASH`, `CARD`, `BANK_TRANSFER`, `UPI`, `ONLINE`, and `OTHER` payment methods.
  - Stores transaction reference identifiers (e.g. UPI Transaction ID, Cheque Number, Bank Transfer Ref).
- **Official Printable Receipts (`/fees/receipt/<id>`)**:
  - Generates a unique, human-readable receipt number (e.g. `REC-2026-000421`) upon recording a successful payment.
  - Printable receipt document displaying school name, receipt number, student name, class, section, issue date, invoice reference, payment method, amount paid, remaining balance, and staff receiver.
- **Student & Parent Fee Accounts (`/fees/my-account`)**:
  - Read-only student fee ledger displaying total billed, total discounts, total payable, total paid, outstanding dues, overdue flags, and printable payment receipts.
  - Server-side IDOR security checks guarantee parents (`/fees/child/<student_id>`) can only view financial records for their linked children (`GuardianStudent`).
- **Fee Collection Summary Dashboard (`/fees/payments`)**:
  - Financial collection metrics for admin/finance staff (Total Billed, Total Collected, Total Outstanding, Overdue Dues, Paid/Partial/Unpaid counts, and daily collection summary).

---

### 📊 Module 12 — Accounts & Finance

#### Core Objective
Builds a school-level Accounts & Finance management system allowing authorized administrators/finance staff to track income, operational expenses, financial categories, payment references, supporting document attachments, and server-side net balance metrics, with automatic integration of student fee payments.

#### Detailed Functionality
- **School Financial Management Scope**:
  - Centralized accounting ledger managing all school financial transactions, non-fee revenue, operational expenditures, category classification, transaction references, and supporting document uploads.
  - Consumes Module 11 student fee payments as financial income cleanly without duplicating payment records.
- **Configurable Financial Categories (`/accounts/categories`)**:
  - Admins create, edit, and toggle activation for income and expense categories.
  - Category types (`INCOME` vs `EXPENSE`) enforce validation so expense categories cannot be used for income entries and vice versa.
  - Deactivation (`is_active = False`) preserves historical financial transaction records without breaking references.
- **Unified Financial Transaction Model (`/accounts/transactions`)**:
  - Central `FinancialTransaction` model recording unique transaction numbers (`TXN-2026-XXXXXX`), exact decimal amounts (`DECIMAL(12,2)`), transaction date, payment method (`CASH`, `UPI`, `CARD`, `BANK_TRANSFER`, `CHEQUE`, `ONLINE`, `OTHER`), reference numbers, vendor or payer names, source type, and status (`COMPLETED`, `CANCELLED`).
- **Module 11 Fee Payment Integration & Uniqueness Protection**:
  - Successful student fee payments recorded in Module 11 automatically produce derived financial income records under the **"Student Fees"** category (`source_type = 'FEE_PAYMENT'`, `source_id = payment.id`).
  - Strict duplicate protection enforces uniqueness on `(source_type, source_id)` so no payment can create duplicate income entries.
  - Fee payment cancellations or refunds automatically update derived transaction status to `CANCELLED`.
- **Manual Income Recording (`/accounts/income/create`)**:
  - Finance users record non-fee school revenue (e.g. event sponsorships, donations, transport income, grant funding) with category selection, date, payment method, reference ID, and supporting document attachments.
- **Operational Expense Recording (`/accounts/expenses/create`)**:
  - Finance users record school expenditures (e.g. electricity bills, maintenance, stationery supplies, bus fuel, event costs) with vendor name, bill number, notes, and file attachments.
- **Supporting Document Storage & IDOR Protection (`/accounts/attachments/<id>`)**:
  - Supports uploading bill receipts and invoices (PDF, PNG, JPG, JPEG, WEBP, DOC, DOCX up to 10MB) stored securely in `static/uploads/finance/`.
  - Download route is authorization-protected with server-side tenant isolation (`school_id`).
- **Authoritative Server-Side Financial Dashboard (`/accounts/dashboard`)**:
  - Real-time financial metrics computed using SQL aggregation (`func.sum()`): Total Income, Total Expenses, Net Balance (`Total Income - Total Expenses`), Today's Income/Expenses, Current Month Income/Expenses, Income & Expense Category breakdowns, and Recent Financial Activity log.
- **Filterable Financial Ledger & CSV Export (`/accounts/export/csv`)**:
  - Filter transactions by date presets (Today, This Week, This Month, This Year, Custom Date Range), category, type, payment method, or search query.
  - Download full filtered ledger reports in CSV format with proper totals.

---

### 💼 Module 13 — Salary & Payroll

#### Core Objective
Builds a school Employee Salary & Payroll Management system allowing authorized administrators/finance staff to define salary components, configure pay grade structures, assign structures to employees, generate monthly payrolls, calculate gross and net salaries, issue printable salary slips, provide employees with read-only self-service access to personal salary statements, and integrate completed salary payments into Module 12 Accounts & Finance as expense transactions.

#### Detailed Functionality
- **School Employee Payroll Scope**:
  - Reuses Module 5's existing `Employee` model to manage staff compensation, component allowances, statutory deductions, monthly payroll generation, payment disbursements, and official salary slips.
- **Configurable Salary Components (`/payroll/components`)**:
  - Admins configure earning allowances (e.g. Basic Salary, HRA, Transport Allowance, Medical Allowance, Special Allowance, Bonuses) and deduction rules (e.g. Professional Tax, Advance Recovery).
  - Supports `FIXED_AMOUNT` (fixed rupee values) and `PERCENTAGE` (calculated percentage of Basic Salary).
- **Salary Structures Catalog (`/payroll/structures`)**:
  - Defines reusable pay grade structures (e.g. Senior Academic Staff Grade A, Support Staff Grade B) by attaching line components with specific default values and rates.
- **Employee Salary Assignment (`/payroll/assignments`)**:
  - Connects employees to specific salary structures with effective start dates and notes.
- **Immutable Historical Payroll Snapshots (`/payroll/generate`)**:
  - Generating monthly payroll (`payroll_period = "2026-08"`) creates immutable component snapshots (`PayrollItem`).
  - **Historical Snapshot Guarantee**: Updating an employee's salary structure in future months will **NEVER** rewrite, corrupt, or alter previously generated historical payroll records or salary slips.
- **Controlled Workflow & Payment Processing (`/payroll/roster`)**:
  - State transitions: `GENERATED` $\rightarrow$ `APPROVED` $\rightarrow$ `PAID`.
  - Recording salary payment records payment date, payment method (`BANK_TRANSFER`, `CASH`, `UPI`, `CHEQUE`, `OTHER`), and transaction reference (Bank UTR / Cheque #).
- **Module 12 Accounts & Finance Expense Integration**:
  - Marking a payroll record as `PAID` automatically creates an expense transaction in Module 12 under the **"Salaries"** category (`source_type = 'PAYROLL_PAYMENT'`, `source_id = payroll.id`).
  - Enforces duplicate protection so re-syncing or viewing paid records will never create duplicate financial expense entries.
- **Printable Official Salary Slips (`/payroll/<id>/slip`)**:
  - Printable document featuring school branding, employee registration details, department, designation, itemized earnings breakdown, itemized deductions breakdown, gross salary, total deductions, net payable salary, payment method, transaction reference number, and unique slip identifier (`PAY-2026-08-000123`).
- **Employee Self-Service Portal (`/payroll/my-salary`)**:
  - Teachers and staff can sign in to view their personal salary history, active pay grade, and download official salary slips.
  - Server-side IDOR security checks guarantee employees can **ONLY** access their own salary records, and completely block Students/Parents.

---

### 📋 Module 14 — Attendance Management

#### Core Objective
Builds a school Attendance Management system supporting daily student attendance (class-based, bulk marking with default helpers) and employee/teacher staff attendance, with role-based access control for Admins, Teachers, Students, and Parents.

#### Detailed Functionality
- **Dual Scope Attendance Support**:
  - Upgrades `Attendance` model to cleanly track daily attendance for both **Students** (linked to class, section, academic session, student) and **Employees/Staff** (linked to employee, school).
- **Daily Class Student Attendance (`/attendance/class`)**:
  - Teachers and Admins select Class, Section, and Attendance Date (`YYYY-MM-DD`).
  - Displays enrolled students with status radio buttons (`PRESENT`, `ABSENT`, `LATE`, `HALF_DAY`), roll numbers, and remarks inputs.
  - Includes **"Mark All Present"** and **"Mark All Absent"** quick action helpers for fast class marking.
  - **Atomic Transaction & Duplicate Protection**: Bulk submission updates existing attendance records if already present for the `(student_id, attendance_date, session_id)`, preventing duplicate database entries.
- **Monthly Class Attendance Matrix & Low Attendance Alerts (`/attendance/class/matrix`)**:
  - Renders student-by-student monthly attendance matrix grid for selected class/section.
  - Highlights students with low attendance (< 75%) in a prominent alert section for proactive teacher intervention.
- **Daily Staff & Teacher Attendance (`/attendance/employees`)**:
  - Admins select date and record daily attendance for all active school employees/staff with quick status controls and notes.
- **Student & Parent Attendance Portals (`/attendance/my-attendance`, `/attendance/child/<id>`)**:
  - Students can view their personal attendance statistics (Attendance %, Present Days, Absences, Late, Half Day) and historical ledger.
  - Parents can view linked child attendance records with `GuardianStudent` IDOR verification.
- **Employee Self-Service Portal (`/attendance/my-staff-attendance`)**:
  - Staff members and teachers can view their own working days attendance ledger and attendance rate.

---

## 🎨 Navigation & Menu UI Architecture

- **Expandable Dark-Themed Left Sidebar**:
  - Styled in StratLearn's dark theme (`bg-slate-950 text-slate-300 border-r border-slate-800/80`).
- **`menu` Header & Live Real-Time Search**:
  - Features a lowercase `menu` header and a live `[🔍 Search menu...]` input box that filters sidebar links in real time as you type.
- **Expandable Menu Groups with `+` / `—` Toggles**:
  - Top-level menu categories (e.g. *Dashboard*, *General Settings*, *Classes*, *Subjects*, *Students*, *Employees*, *Timetable*, *Homework*, *Behaviour & Skills*, *Fees & Collection*) act as interactive accordions.
  - Collapsed groups display a `+` toggle; expanded groups reveal a `—` toggle along with a **vertical connecting guide line** leading to nested sub-tabs (`All Employees`, `Fee Invoices`, `Record Payment`, `Fee Structures`, `Fee Types`, etc.).
- **Active State Highlights**:
  - Active tabs and parent menu groups highlight automatically in cyan brand colors (`border-l-4 border-brand-500 bg-brand-500/10 text-brand-400 font-bold`).

---

## 📁 Repository Directory Structure

```text
stratlearn/
│
├── app/
│   ├── __init__.py          # Flask Application Factory, Context Processors & Auto-Seeding
│   ├── config.py            # Environment configuration loader (.env)
│   │
│   ├── models/              # SQLAlchemy Database Schema Models
│   │   ├── __init__.py      # Model registry & exports
│   │   ├── institute.py     # Institute profile model
│   │   ├── school.py        # School profile model [MODULE 2]
│   │   ├── academic_session.py # Academic Session model [MODULE 2]
│   │   ├── setting.py       # Key-value system settings model [MODULE 2]
│   │   ├── school_class.py  # Academic Classes model [MODULE 3]
│   │   ├── section.py       # Sections model [MODULE 3]
│   │   ├── subject.py       # Subjects Catalog model [MODULE 4]
│   │   ├── subject_class.py # Subject-Class allocation model [MODULE 4]
│   │   ├── employee.py      # Employee & Staff model [MODULE 5]
│   │   ├── student.py       # Student model [MODULE 6]
│   │   ├── student_enrollment.py # Student Academic Placement model [MODULE 6]
│   │   ├── guardian.py           # Guardian profile model [MODULE 7]
│   │   ├── guardian_student.py   # Guardian-Student junction model [MODULE 7]
│   │   ├── period.py             # Period time slot model [MODULE 8]
│   │   ├── timetable.py          # Weekly Timetable schedule model [MODULE 8]
│   │   ├── homework.py           # Homework & Submissions model [MODULE 9]
│   │   ├── behaviour_skills.py   # Behaviour & Skills Management models [MODULE 10]
│   │   ├── fee_management.py     # Fees & Fee Management models [MODULE 11]
│   │   └── user.py               # User portal credentials & role links
│   │
│   ├── services/            # Service Abstractions & Business Logic
│   │   ├── __init__.py
│   │   ├── academic_service.py # Academic session management [MODULE 2]
│   │   ├── setting_service.py  # System settings management [MODULE 2]
│   │   ├── class_service.py    # Classes & sections management [MODULE 3]
│   │   ├── subject_service.py  # Subjects & assignments management [MODULE 4]
│   │   ├── employee_service.py # Staff directory management [MODULE 5]
│   │   ├── student_service.py  # Students & enrollments management [MODULE 6]
│   │   ├── guardian_service.py # Guardians & family links management [MODULE 7]
│   │   ├── timetable_service.py # Timetable matrix & conflict engine [MODULE 8]
│   │   ├── homework_service.py  # Homework & Gemini AI Evaluation engine [MODULE 9]
│   │   ├── behaviour_skills_service.py # Behaviour & Skills service [MODULE 10]
│   │   └── fee_service.py       # Fees & Fee Management service [MODULE 11]
│   │
│   ├── routes/              # Flask Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py          # Sign In & Sign Up (/auth/*) [MODULE 1]
│   │   ├── admin.py         # Admin Dashboard (/admin/*)
│   │   ├── teacher.py       # Teacher Dashboard (/teacher/*)
│   │   ├── student.py       # Student Dashboard (/student/*)
│   │   ├── parent.py        # Parent Dashboard (/parent/*)
│   │   ├── settings.py      # Module 2 Settings (/admin/settings)
│   │   ├── classes.py       # Module 3 Classes (/admin/academics/classes)
│   │   ├── school.py        # Module 2 School Setup (/admin/school)
│   │   ├── subjects.py      # Module 4 Subjects (/admin/academics/subjects)
│   │   ├── employees.py     # Module 5 Employees (/admin/employees)
│   │   ├── students.py      # Module 6 Students (/admin/students)
│   │   ├── guardians.py     # Module 7 Guardians (/admin/guardians)
│   │   ├── timetables.py    # Module 8 Timetables (/admin/academics/timetables)
│   │   ├── homework.py      # Module 9 Homework (/homework/*)
│   │   ├── behaviour_skills.py # Module 10 Behaviour & Skills (/behaviour-skills/*)
│   │   └── fees.py          # Module 11 Fees & Fee Management (/fees/*)
│   │
│   ├── utils/               # Utilities & Decorators
│   │   ├── decorators.py    # Authorization decorators (@login_required, @role_required)
│   │   └── navigation.py    # Centralized expandable menu structure
│   │
│   └── templates/           # Jinja2 HTML Templates
│       ├── base.html        # Master Layout (Dark Sidebar, Search, Top Header, Alerts)
│       ├── fees/            # Module 11 Fee Management Templates
│       │   ├── types.html
│       │   ├── structures_list.html
│       │   ├── structure_form.html
│       │   ├── invoices_list.html
│       │   ├── generate_invoices.html
│       │   ├── invoice_detail.html
│       │   ├── payment_form.html
│       │   ├── payments_list.html
│       │   ├── student_fee_account.html
│       │   └── receipt.html
│       ├── behaviour_skills/# Module 10 Behaviour & Skills Templates
│       ├── homework/        # Module 9 Homework Templates
│       ├── timetables/      # Module 8 Timetable Templates
│       ├── students/        # Student Directory & Credentials Templates
│       └── auth/            # Sign In & Universal Sign Up Templates
│
├── seed.py                  # Database auto-migration & seeding script (Modules 1–11)
├── run.py                   # Application entrypoint script
└── README.md                # Detailed project documentation
```

---

## 🚀 Setup & Installation Guide

1. **Start XAMPP MySQL**: Ensure Apache & MySQL services are active in the XAMPP Control Panel.
2. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run Database Initialization & Seeding**:
   ```bash
   python seed.py
   ```
   *(Creates `stratlearn` MySQL database, applies schema ALTER column migrations, builds all database tables, and seeds demo accounts, school setup, classes, sections, subjects, staff directory, student rosters, guardian links, period time slots, weekly timetables, homework assignments, behaviour categories, skill definitions, fee types, fee structures, invoices, payments, and receipts).*
4. **Launch Application Server**:
   ```bash
   python run.py
   ```
5. Open your browser and navigate to `http://127.0.0.1:5000`

---

## 🔐 Default Demo Accounts

| Role | Username | Password | Default Portal View |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Overview Dashboard (`/admin/dashboard`) |
| **Teacher** | `teacher` | `Teacher@123` | Teacher Dashboard (`/teacher/dashboard`) |
| **Student** | `student` | `Student@123` | Student Dashboard (`/student/dashboard`) |
| **Parent** | `parent` | `Parent@123` | Parent Dashboard (`/parent/dashboard`) |
