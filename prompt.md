# STRATLEARN — MODULE 25: ONLINE STORE & POS
# SCHOOL STORE, INVENTORY, ORDERS & POINT-OF-SALE MANAGEMENT

You are continuing development of StratLearn, a modular school management platform.

IMPORTANT:

Build this module on top of the EXISTING StratLearn codebase.

DO NOT rebuild:

    Authentication
    Role management
    Students
    Parents
    Teachers
    Employees
    Classes
    Sections
    Fees
    Accounts
    Notifications
    Messaging
    Dashboards

Reuse existing models, permissions, school context, users, and UI architecture wherever possible.

This module adds the school's:

    Online Store
    Inventory
    Product Management
    Orders
    POS
    Sales Records

==================================================
1. CORE PURPOSE
==================================================

Create a school commerce system where the school can manage and sell items such as:

    School uniforms
    Books
    Notebooks
    Stationery
    ID cards
    School bags
    Accessories
    Other school-approved products

The system must support BOTH:

    Online ordering

and:

    Physical school-store / POS sales

It should function as a school inventory and commerce module,
NOT as a generic e-commerce marketplace.


==================================================
2. ROLE-BASED ACCESS
==================================================

Use the existing authentication and role system.

ADMIN:

    Manage products
    Manage categories
    Manage inventory
    View orders
    Process orders
    Manage POS
    View sales
    View stock
    Configure store settings

AUTHORIZED STORE STAFF:

    Process POS transactions
    View relevant inventory
    Process orders according to permissions

STUDENT:

    Browse available products
    View product details
    Place orders if enabled
    View own orders

PARENT:

    Browse products
    Purchase items for authorized child/children
    View own orders
    View order status

TEACHER:

    Only provide store functionality if existing school permissions explicitly allow it.

Do not automatically give teachers administrative store permissions.


==================================================
3. SCHOOL ISOLATION
==================================================

Every:

    Product
    Category
    Inventory record
    Order
    Sale
    POS transaction

must belong to the correct school.

School A users must NEVER be able to access School B commerce data.

Enforce this server-side.

Never trust school_id from the frontend.


==================================================
4. PRODUCT MANAGEMENT
==================================================

Admins should be able to create products with:

    Product name
    Description
    Category
    SKU
    Selling price
    Optional purchase/cost price
    Stock quantity
    Low-stock threshold
    Product image
    Status
    Created date
    Updated date


Support:

    Active
    Inactive


Inactive products must not be purchasable.


==================================================
5. CATEGORIES
==================================================

Support categories such as:

    Uniform
    Books
    Stationery
    Accessories
    School Supplies
    Other


Admins should be able to:

    Create category
    Rename category
    Disable category


Do not hardcode categories into the frontend.


==================================================
6. PRODUCT VARIANTS
==================================================

The architecture should support variants where useful.

Examples:

    Shirt → Size S / M / L / XL
    Shoes → Size 6 / 7 / 8
    Notebook → Ruled / Plain


Do not overcomplicate variants.

Only implement a variant model if it fits the existing architecture cleanly.


==================================================
7. PRODUCT AVAILABILITY
==================================================

Products should clearly indicate:

    In Stock
    Low Stock
    Out of Stock
    Unavailable


Do not allow normal users to purchase unavailable products.


==================================================
8. INVENTORY
==================================================

Create proper inventory tracking.

Track:

    Current stock
    Stock added
    Stock removed
    Reason
    Timestamp
    User responsible


Possible stock movement reasons:

    Purchase
    Manual adjustment
    Sale
    Order
    Return
    Damage
    Correction


Do not silently modify stock.


==================================================
9. STOCK MOVEMENT HISTORY
==================================================

Admins should be able to inspect stock history.

Example:

    +50 uniforms
    -2 uniforms sold
    -1 uniform returned
    +10 books received


Every adjustment should have:

    Quantity
    Direction
    Reason
    User
    Timestamp


==================================================
10. LOW STOCK
==================================================

Allow products to have:

    Low-stock threshold


When stock falls below that threshold:

    Show low-stock warning.


Integrate with the existing Notifications system where useful.

Do NOT spam notifications repeatedly for the same stock condition.


==================================================
11. ONLINE STORE
==================================================

Create the student/parent-facing store.

Users should be able to:

    Browse products
    Search products
    Filter by category
    View product details
    Select quantity
    Add to cart
    Review cart
    Place order


Only show products available to the current school.


==================================================
12. PRODUCT SEARCH
==================================================

Support useful search.

Search by:

    Product name
    SKU
    Category


Use server-side querying where appropriate.

Do not load thousands of products unnecessarily.


==================================================
13. PRODUCT DETAILS
==================================================

Product details should contain:

    Image
    Name
    Description
    Price
    Availability
    Variants where applicable


Do not expose internal:

    Cost price
    Supplier information
    Internal stock-management details

to students/parents.


==================================================
14. CART
==================================================

Users should be able to:

    Add product
    Change quantity
    Remove product
    View subtotal
    Review order


Validate prices and stock on the SERVER when the order is submitted.

Never trust:

    Product price
    Quantity
    Total amount

from the frontend.


==================================================
15. CART SECURITY
==================================================

The backend must recalculate:

    Product price
    Quantity
    Subtotal
    Total


The frontend is only for display/input.

Never accept a client-provided:

    total_price

as authoritative.


==================================================
16. ORDER CREATION
==================================================

When an order is created:

    Validate user
    Validate school
    Validate product availability
    Validate stock
    Recalculate prices
    Create order
    Create order items
    Reserve/deduct stock according to the chosen order policy


Do not allow negative inventory.


==================================================
17. ORDER MODEL
==================================================

An order should contain appropriate fields such as:

    Order ID
    School ID
    Buyer/User ID
    Parent/Student relationship where applicable
    Order number
    Total amount
    Payment status
    Order status
    Created timestamp
    Updated timestamp


Order items should contain:

    Product
    Variant if applicable
    Quantity
    Unit price
    Line total


IMPORTANT:

Store the actual unit price used at the time of purchase.

Do not depend on the current product price to reconstruct historical orders.


==================================================
18. ORDER NUMBER
==================================================

Generate a human-readable order number.

Example:

    ORD-2026-000123


Do not expose sequential database IDs as the only public order identifier.


==================================================
19. ORDER STATUS
==================================================

Support a clear lifecycle such as:

    Pending
    Confirmed
    Preparing
    Ready for Pickup
    Completed
    Cancelled
    Returned


Only implement states that fit the actual school workflow.

Prevent invalid transitions.


==================================================
20. PAYMENT
==================================================

DO NOT build a fake payment gateway.

First inspect the existing project.

If a real payment provider is already integrated:

    Reuse it appropriately.


If no payment provider exists:

    Support a clearly defined school payment workflow such as:

        Pay at School
        Cash
        Existing Fee/Payment system where appropriate


Do not claim an online payment succeeded unless an actual payment provider confirms it.


==================================================
21. FEES INTEGRATION
==================================================

Do NOT automatically merge store purchases into the Fees module.

A store order is a commerce transaction.

If the existing financial architecture supports a clean integration:

    Record the appropriate financial transaction.


Do not duplicate accounting records.


==================================================
22. ACCOUNTS INTEGRATION
==================================================

Where appropriate, completed sales should integrate with the existing Accounts/Finance module.

Avoid double-counting revenue.

The store should create a clean transaction/reference that the finance module can understand.


==================================================
23. POS
==================================================

Create a physical school-store POS interface.

Authorized staff should be able to:

    Search products
    Scan/enter SKU
    Add items
    Change quantities
    Remove items
    Calculate total
    Complete sale
    View transaction summary


Optimize the POS workflow for speed.


==================================================
24. POS CUSTOMER
==================================================

A POS transaction may optionally be associated with:

    Student
    Parent
    Teacher
    Staff
    Walk-in customer


Do not require a student/parent account for every physical purchase unless school policy requires it.


==================================================
25. POS STOCK
==================================================

When a POS sale is completed:

    Validate stock
    Record sale
    Update inventory
    Create financial transaction if configured


These operations should be consistent and protected against partial failure.


==================================================
26. POS DUPLICATE TRANSACTIONS
==================================================

Prevent accidental duplicate sales caused by:

    Double clicking
    Network retry
    Duplicate API request


Use appropriate transaction/idempotency mechanisms where necessary.


==================================================
27. RECEIPTS
==================================================

After a successful sale/order:

    Provide a receipt/order summary.


Receipt should contain:

    School
    Order/transaction number
    Date/time
    Items
    Quantity
    Unit price
    Total
    Payment status


Do not expose unnecessary personal information.


==================================================
28. ORDER HISTORY
==================================================

Students/parents should be able to view:

    Their orders
    Order number
    Date
    Items
    Total
    Status


They must NOT see other users' orders.


==================================================
29. ADMIN ORDER MANAGEMENT
==================================================

Admins/store staff should be able to:

    Search orders
    Filter orders
    View order details
    Change valid order status
    Process cancellations
    Process returns where implemented


Every status change should be permission-checked.


==================================================
30. RETURNS
==================================================

Architect for returns.

If implemented:

    Validate original transaction
    Validate quantity
    Record return
    Update inventory
    Update financial records appropriately


Do not simply delete the original sale.


==================================================
31. SALES HISTORY
==================================================

Admin should be able to view:

    Today's sales
    Sales by date
    Sales by product
    Sales by category
    POS sales
    Online orders


Use existing reporting infrastructure where possible.


==================================================
32. DASHBOARD INTEGRATION
==================================================

ADMIN DASHBOARD:

Provide appropriate store metrics such as:

    Today's sales
    Pending orders
    Low-stock products
    Recent transactions


STUDENT DASHBOARD:

Provide:

    Store
    My Orders


PARENT DASHBOARD:

Provide:

    Store
    My Orders


TEACHER DASHBOARD:

Only show store access if permitted by existing role permissions.


Do not redesign existing dashboards.


==================================================
33. NOTIFICATION INTEGRATION
==================================================

Use Module 23 Notifications.

Useful events:

    Order placed
    Order confirmed
    Order ready for pickup
    Order completed
    Order cancelled
    Low stock


Do not generate unnecessary notifications.


==================================================
34. AUDIT LOGGING
==================================================

Important administrative actions should be auditable.

Examples:

    Product created
    Product edited
    Stock adjusted
    Order status changed
    POS sale completed
    Return processed


Use the project's existing audit infrastructure if available.

Do not create duplicate audit systems.


==================================================
35. PERMISSIONS
==================================================

Explicitly enforce:

    Product management
    Inventory management
    Order management
    POS access
    Financial access
    Return processing


Do not assume:

    Admin = unrestricted access

if the project already has granular permissions.


==================================================
36. API DESIGN
==================================================

Follow existing project conventions.

Potential APIs:

    GET    /api/store/products
    POST   /api/store/products
    GET    /api/store/products/{id}
    PATCH  /api/store/products/{id}

    GET    /api/store/categories
    POST   /api/store/categories

    GET    /api/store/cart
    POST   /api/store/cart/items
    PATCH  /api/store/cart/items/{id}
    DELETE /api/store/cart/items/{id}

    POST   /api/store/orders
    GET    /api/store/orders
    GET    /api/store/orders/{id}

    PATCH  /api/store/orders/{id}/status

    GET    /api/store/inventory
    POST   /api/store/inventory/adjust

    POST   /api/store/pos/sales
    GET    /api/store/pos/sales

Adapt these to the existing backend architecture.

Do not duplicate existing routes.


==================================================
37. DATABASE DESIGN
==================================================

Create clean relational models for concepts such as:

    StoreProduct
    StoreCategory
    ProductVariant
    InventoryMovement
    StoreOrder
    StoreOrderItem
    POSSale
    POSSaleItem


Do not create every possible table just because it is listed.

Reuse existing entities for:

    User
    Student
    Parent
    School
    Class
    Section


Use foreign keys and appropriate indexes.


==================================================
38. DATA INTEGRITY
==================================================

Protect against:

    Negative stock
    Invalid quantities
    Invalid prices
    Deleted products in historical orders
    Duplicate orders
    Cross-school access
    Unauthorized inventory changes


Historical transactions must remain understandable even if a product later becomes inactive.


==================================================
39. CONCURRENCY
==================================================

Handle the case where:

    Two users attempt to buy the last item simultaneously.


Stock updates must be atomic.

Do not allow:

    Stock = -1


Use the database's transaction/locking capabilities appropriately.


==================================================
40. PRODUCT DELETION
==================================================

Do not hard-delete products that appear in historical orders unless the existing data model safely supports it.

Prefer:

    Inactive / archived


for products with transaction history.


==================================================
41. UI RESEARCH
==================================================

DO NOT design the UI yourself.

Use available tools:

    StitchMCP
    Mobbin MCP
    Chrome DevTools MCP
    Modern Web Guidance


Research:

    School store interfaces
    Education commerce portals
    POS interfaces
    Inventory dashboards
    Mobile product browsing


Use the tools to determine:

    Product layout
    POS workflow
    Inventory interface
    Order interface
    Responsive behavior


Do not copy another product directly.


==================================================
42. MOBILE
==================================================

The online store must work on:

    Desktop
    Tablet
    Mobile


The POS should prioritize the device types actually used by school staff.


==================================================
43. ACCESSIBILITY
==================================================

Use:

    Chrome DevTools MCP
    a11y-debugging skill
    modern-web-guidance skill


Test:

    Product cards
    Search
    Filters
    Cart
    Forms
    POS controls
    Buttons
    Tables
    Status indicators
    Keyboard navigation
    Focus states
    Touch targets
    Contrast


==================================================
44. LOADING STATES
==================================================

Handle:

    Product loading
    Cart updates
    Order creation
    POS transaction
    Inventory updates
    Order status changes


Prevent duplicate submissions.


==================================================
45. ERROR STATES
==================================================

Handle:

    Product unavailable
    Insufficient stock
    Invalid quantity
    Order failure
    Payment failure
    POS failure
    Network failure
    Unauthorized action


Give useful user-facing messag
