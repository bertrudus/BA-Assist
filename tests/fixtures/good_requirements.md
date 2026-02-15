# Online Bookstore — Requirements Document

## 1. Business Context

The company needs an online bookstore platform to expand sales channels beyond physical retail locations. Current online revenue is zero; the target is to capture 20% of total sales through the online channel within 12 months of launch.

## 2. Scope

### 2.1 In Scope
- Product catalogue browsing and search
- User registration and authentication
- Shopping cart and checkout
- Payment processing (credit card, PayPal)
- Order tracking
- Basic reporting dashboard for administrators

### 2.2 Out of Scope
- Mobile native applications (web responsive only for Phase 1)
- International shipping
- E-book / digital content delivery
- Loyalty programme

## 3. Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| Head of Retail | Sponsor | Revenue growth, brand consistency |
| Marketing Manager | Key User | Promotions, SEO, analytics |
| Warehouse Team | Operational | Fulfilment, inventory accuracy |
| Customers | End User | Easy browsing, fast checkout, reliable delivery |
| IT Operations | Support | System uptime, security, maintainability |

## 4. Functional Requirements

### REQ-F001: Product Catalogue
The system shall display a catalogue of books with title, author, ISBN, price, cover image, and description.

### REQ-F002: Search
The system shall allow users to search for books by title, author, ISBN, or keyword.

### REQ-F003: User Registration
The system shall allow new users to register with email, name, and password.

### REQ-F004: Shopping Cart
The system shall allow authenticated users to add, remove, and update quantities of items in a shopping cart.

### REQ-F005: Checkout
The system shall guide users through a checkout process including delivery address, payment, and order confirmation.

### REQ-F006: Payment Processing
The system shall process payments via credit card and PayPal, confirming successful transactions before creating orders.

### REQ-F007: Order Tracking
The system shall allow users to view their order history and current order status.

### REQ-F008: Admin Dashboard
The system shall provide administrators with a dashboard showing sales, inventory levels, and order metrics.

## 5. Non-Functional Requirements

### REQ-NF001: Performance
Pages shall load within 2 seconds under normal load (up to 500 concurrent users).

### REQ-NF002: Availability
The system shall maintain 99.5% uptime measured monthly.

### REQ-NF003: Security
All user data shall be encrypted in transit (TLS 1.2+) and at rest. Passwords shall be hashed using bcrypt.

### REQ-NF004: Accessibility
The system shall comply with WCAG 2.1 Level AA.

## 6. Constraints
- Budget: £150,000
- Timeline: 6 months to MVP launch
- Must integrate with existing warehouse management system (WMS) via REST API

## 7. Assumptions
- Existing WMS API is stable and documented
- Payment gateway provider will be selected during design phase
- Content (book descriptions, images) will be supplied by the marketing team

## 8. Dependencies
- WMS API availability for inventory sync
- Payment gateway contract finalisation
- SSL certificate provisioning

## 9. Acceptance Criteria
- All functional requirements pass user acceptance testing
- Performance benchmarks met under load testing
- Security audit passed with no critical findings
- Stakeholder sign-off from Head of Retail and IT Operations
