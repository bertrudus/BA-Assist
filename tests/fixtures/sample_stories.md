# User Stories — Online Bookstore

## US-001: Browse Book Catalogue
**As a** customer,
**I want** to browse the book catalogue with cover images and details,
**so that** I can discover books I'm interested in purchasing.

### Acceptance Criteria
- Books are displayed in a grid with cover image, title, author, and price
- Clicking a book opens a detail page with full description and ISBN
- Catalogue supports pagination (20 items per page)
- Books can be sorted by title, price, or publication date

## US-002: Search for Books
**As a** customer,
**I want** to search for books by title, author, or keyword,
**so that** I can quickly find specific books.

### Acceptance Criteria
- Search bar is visible on every page
- Results appear within 1 second
- Results show matching books with relevance ranking
- "No results found" message displays when there are no matches
- Search supports partial matching

## US-003: Register an Account
**As a** visitor,
**I want** to create an account with my email and password,
**so that** I can save my details for faster checkout.

### Acceptance Criteria
- Registration form requires email, name, and password
- Password must be at least 8 characters with one number and one special character
- Duplicate email addresses are rejected with a clear message
- Confirmation email is sent upon successful registration
- User is automatically logged in after registration
