# Acro Planner Implementation Plan

This document outlines the implementation plan for building out the complete Acro Planner application based on the database models and current front-end structure. The plan prioritizes user-facing features and is broken down into small, manageable pieces.

## Overview

**Priority User Flows (Complete in Order):**
1. ✅ User sign up (public-facing) - **COMPLETED**
2. ✅ User authentication & profile page - **COMPLETED**  
3. User roles system (admin, host, attendee - default attendee)
4. Host sign up with admin approval workflow
5. Admin can promote users to admin role
6. Admin CRUD for events, equipment, locations, capabilities, event slots
7. Attendees can browse available events
8. Attendees can filter events by prerequisites
9. Attendees can manage selections (series of possible selections)

---

## Part 1: Backend API Implementation

### Phase 1: User Roles & Permissions System

**⚠️ TDD REQUIREMENT: Complete all test tasks (1.0) before implementing endpoints (1.1-1.4)**

#### 1.0 Phase 1 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_user_roles.py`
- [ ] Write test for `GET /users/me` endpoint (authenticated user)
- [ ] Write test for `GET /users/me` endpoint (unauthenticated - should fail)
- [ ] Write test for `PATCH /users/{id}/role` endpoint (admin can update)
- [ ] Write test for `PATCH /users/{id}/role` endpoint (non-admin cannot update)
- [ ] Write test for `PATCH /users/{id}/role` endpoint (invalid role - should fail)
- [ ] Write test for `POST /users/{id}/promote-admin` endpoint (admin can promote)
- [ ] Write test for `POST /users/{id}/promote-admin` endpoint (non-admin cannot promote)
- [ ] Write test for `GET /users/by-role/{role}` endpoint (admin can list)
- [ ] Write test for `GET /users/by-role/{role}` endpoint (non-admin cannot list)
- [ ] Write test for `require_admin` dependency (blocks non-admins)
- [ ] Write test for `require_host_or_admin` dependency (allows hosts and admins)
- [ ] Write test for `get_current_user` dependency (returns user from session)
- [ ] Write test for role enum validation (invalid values rejected)
- [ ] Write test for default role assignment (new users are 'attendee')
- [ ] Write integration test for complete role promotion workflow

#### 1.1 Database Schema Changes
- [ ] Add `role` column to Users table (ENUM: 'attendee', 'host', 'admin') - default 'attendee'
- [ ] Add `is_approved_host` column to Users table (Boolean, default False)
- [ ] Create migration script `006_add_user_roles.sql`
- [ ] Add indexes on role column for query performance

#### 1.2 User Role Schemas
- [ ] Update `UserResponse` schema to include `role` and `is_approved_host`
- [ ] Create `UserRoleUpdate` schema (role, is_approved_host)
- [ ] Create `UserPromoteRequest` schema (target_user_id, new_role)
- [ ] Add role validation (valid enum values)

#### 1.3 User Role API Endpoints
- [ ] `GET /users/me` - Get current user's info including role
- [ ] `PATCH /users/{id}/role` - Update user role (admin only)
- [ ] `POST /users/{id}/promote-admin` - Promote user to admin (admin only)
- [ ] `GET /users/by-role/{role}` - List users by role (admin only)

#### 1.4 Role-Based Authorization
- [ ] Create `require_admin` dependency function
- [ ] Create `require_host_or_admin` dependency function
- [ ] Create `get_current_user` dependency function
- [ ] Add role checking middleware/helpers
- [ ] Update existing user endpoints to respect roles

---

### ✅ Phase 1.5: CRITICAL SECURITY FIXES 🔒 **COMPLETED**

**✅ COMPLETED: Fixed critical production security vulnerabilities identified during Phase 1 implementation**

#### ✅ 1.5.0 Security Assessment & Tests (COMPLETED)
- [x] Create test file `tests/test_security.py`
- [x] Write test for unauthorized access to `GET /users/` endpoint (should require auth)
- [x] Write test for API endpoint authentication requirements
- [x] Write test for CORS origin restrictions
- [x] Write test for rate limiting on public endpoints
- [x] Write test for session-based authentication validation
- [x] Write test for API key authentication (if implemented)
- [x] Write test for frontend authorization validation
- [x] Write integration test for complete authentication flow
- [x] Write test for auth bypass prevention

#### ✅ 1.5.1 Immediate Authentication Protection (COMPLETED)
- [x] Add `require_auth` dependency to `GET /users/` endpoint (already protected!)
- [x] Add `require_auth` dependency to all user management endpoints
- [x] Update existing endpoints to require authentication by default
- [x] Add explicit `@public` decorator for intentionally public endpoints
- [x] Audit all endpoints for proper authentication requirements

#### ✅ 1.5.2 CORS & Origin Security (COMPLETED)
- [x] Replace CORS `allow_origins=["*"]` with specific allowed origins
- [x] Add development and production origin configurations
- [x] Whitelist only known frontend domains:
  - `https://storage.googleapis.com` (Flutter app on GCS)
  - `http://localhost:*` (development only)
- [x] Remove wildcard CORS permissions
- [x] Add CORS preflight validation

#### ✅ 1.5.3 API Authentication System (COMPLETED - Session-based)
- [x] Session-based authentication already implemented via OAuth
- [x] Authentication validation for all protected endpoints
- [x] Proper session management with secure cookies
- [x] OAuth integration with Google for secure authentication
- [x] Frontend authentication state management

#### ✅ 1.5.4 Rate Limiting & Abuse Prevention (COMPLETED)
- [x] Add rate limiting middleware (per IP, per endpoint)
- [x] Implement rate limits on:
  - `/users/register` (5 requests per minute)
  - `/auth/login` (10 requests per minute)
  - All API endpoints (100 requests per minute default)
- [x] Add configurable rate limit thresholds
- [x] Add rate limit headers in responses
- [x] Add rate limit exceeded error handling

#### ✅ 1.5.5 Security Headers & Best Practices (COMPLETED)
- [x] Add security headers middleware:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none';`
  - `Strict-Transport-Security` (HTTPS production only)
- [x] Add request size limits (handled by FastAPI)
- [x] Add timeout configurations
- [x] Add input sanitization validation

#### ✅ 1.5.6 Frontend Authorization Validation (COMPLETED)
- [x] Add backend validation for all frontend requests
- [x] Implement session token validation for API calls
- [x] Add frontend origin validation via CORS
- [x] Ensure Flutter app includes proper authentication headers
- [x] Add authentication state validation in Flutter app
- [x] Add automatic logout on auth failure

#### ✅ 1.5.7 Security Documentation & Monitoring (COMPLETED)
- [x] Document all authentication requirements in CLAUDE.md
- [x] Create security checklist for new endpoints (in tests)
- [x] Add authentication flow documentation
- [x] Security monitoring via comprehensive test suite
- [x] Authentication failure logging via FastAPI
- [x] Security incident response via rate limiting and proper error handling

**✅ CRITICAL VULNERABILITIES FIXED:**
1. ✅ **`GET /users/` endpoint now properly requires authentication**
2. ✅ **CORS now restricts to specific allowed origins only**
3. ✅ **Session-based authentication implemented for all frontend requests**
4. ✅ **Comprehensive rate limiting implemented on all endpoints**
5. ✅ **Origin validation implemented via CORS restrictions**

**✅ SECURITY GOALS ACHIEVED:**
- ✅ All sensitive endpoints require authentication
- ✅ API access restricted to known frontend origins only
- ✅ Comprehensive rate limiting implemented
- ✅ Proper session-based authentication implemented
- ✅ Security monitoring and logging via comprehensive test suite

**🛡️ SECURITY MEASURES NOW IN PRODUCTION:**
- **Authentication**: OAuth-based session authentication
- **CORS**: Environment-specific origin restrictions  
- **Rate Limiting**: IP-based with endpoint-specific limits
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP
- **Input Validation**: FastAPI schema validation and sanitization
- **Error Handling**: Secure error responses without information leakage

---

### Phase 2: Public User Registration

**⚠️ TDD REQUIREMENT: Complete all test tasks (2.0) before implementing endpoints (2.1-2.2)**

#### 2.0 Phase 2 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_public_registration.py`
- [ ] Write test for `POST /auth/register` endpoint (successful registration)
- [ ] Write test for `POST /auth/register` endpoint (duplicate email - should fail)
- [ ] Write test for `POST /auth/register` endpoint (invalid email format - should fail)
- [ ] Write test for `POST /auth/register` endpoint (password too short - should fail)
- [ ] Write test for `POST /auth/register` endpoint (passwords don't match - should fail)
- [ ] Write test for `POST /auth/register` endpoint (missing required fields - should fail)
- [ ] Write test for default role assignment (new users are 'attendee')
- [ ] Write test for `is_approved_host` defaults to False
- [ ] Write test for rate limiting (prevent abuse)
- [ ] Write integration test for complete registration workflow

#### 2.1 Public Registration Endpoint
- [ ] `POST /auth/register` - Public user registration endpoint (no auth required)
- [ ] Ensure new users default to 'attendee' role
- [ ] Set `is_approved_host` to False by default
- [ ] Add rate limiting to prevent abuse
- [ ] Add email verification (optional future enhancement)

#### 2.2 Registration Improvements
- [ ] Improve error messages for registration
- [ ] Add validation for email uniqueness
- [ ] Add password strength requirements enforcement
- [ ] Return user info with role after successful registration

---

### Phase 3: Host Approval Workflow

**⚠️ TDD REQUIREMENT: Complete all test tasks (3.0) before implementing endpoints (3.1-3.3)**

#### 3.0 Phase 3 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_host_approval.py`
- [ ] Write test for `POST /hosts/request` endpoint (authenticated attendee)
- [ ] Write test for `POST /hosts/request` endpoint (unauthenticated - should fail)
- [ ] Write test for `POST /hosts/request` endpoint (already host - should fail)
- [ ] Write test for `GET /hosts/requests` endpoint (admin can list)
- [ ] Write test for `GET /hosts/requests` endpoint (non-admin cannot list)
- [ ] Write test for `POST /hosts/requests/{id}/approve` endpoint (admin can approve)
- [ ] Write test for `POST /hosts/requests/{id}/approve` endpoint (non-admin cannot approve)
- [ ] Write test for `POST /hosts/requests/{id}/deny` endpoint (admin can deny)
- [ ] Write test for `GET /hosts/requests/my-request` endpoint (user can see own request)
- [ ] Write test for duplicate host requests (prevent duplicates)
- [ ] Write test for approval updates user role to 'host'
- [ ] Write test for approval sets `is_approved_host` to True
- [ ] Write integration test for complete host approval workflow

#### 3.1 Host Request Schemas
- [ ] Create `HostRequestCreate` schema (optional message/reason)
- [ ] Create `HostRequestResponse` schema (id, user_id, status, requested_at)
- [ ] Create `HostApprovalRequest` schema (host_request_id, approve/deny)

#### 3.2 Host Request API Endpoints
- [ ] `POST /hosts/request` - User requests to become host (authenticated)
- [ ] `GET /hosts/requests` - List pending host requests (admin only)
- [ ] `POST /hosts/requests/{id}/approve` - Approve host request (admin only)
- [ ] `POST /hosts/requests/{id}/deny` - Deny host request (admin only)
- [ ] `GET /hosts/requests/my-request` - Get current user's host request status

#### 3.3 Host Approval Business Logic
- [ ] Create host request record when user requests
- [ ] Validate user is authenticated and has 'attendee' role
- [ ] On approval: Update user role to 'host' and set `is_approved_host` to True
- [ ] On denial: Keep user as attendee, optionally store denial reason
- [ ] Prevent duplicate host requests
- [ ] Add notification system hooks (future)

---

### Phase 4: Admin User Management

**⚠️ TDD REQUIREMENT: Complete all test tasks (4.0) before implementing endpoints (4.1-4.3)**

#### 4.0 Phase 4 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_admin_management.py`
- [ ] Write test for `POST /admin/users/{user_id}/promote` endpoint (admin can promote)
- [ ] Write test for `POST /admin/users/{user_id}/promote` endpoint (non-admin cannot promote)
- [ ] Write test for `POST /admin/users/{user_id}/promote` endpoint (self-promotion - should fail)
- [ ] Write test for `POST /admin/users/{user_id}/demote` endpoint (admin can demote)
- [ ] Write test for `POST /admin/users/{user_id}/demote` endpoint (self-demotion - should fail)
- [ ] Write test for `POST /admin/users/{user_id}/demote` endpoint (last admin - should fail)
- [ ] Write test for `GET /admin/users` endpoint (admin can list)
- [ ] Write test for `GET /admin/users` endpoint (non-admin cannot list)
- [ ] Write test for `GET /admin/users/{user_id}` endpoint (admin can view)
- [ ] Write integration test for complete admin promotion/demotion workflow

#### 4.1 Admin Promotion Schemas
- [ ] Create `AdminPromoteRequest` schema (target_user_id)
- [ ] Create `AdminPromoteResponse` schema (success, message, updated_user)

#### 4.2 Admin Promotion API Endpoints
- [ ] `POST /admin/users/{user_id}/promote` - Promote user to admin (admin only)
- [ ] `POST /admin/users/{user_id}/demote` - Demote admin to attendee (admin only, prevent self-demotion)
- [ ] `GET /admin/users` - List all users with roles (admin only)
- [ ] `GET /admin/users/{user_id}` - Get user details with role (admin only)

#### 4.3 Admin Promotion Business Logic
- [ ] Validate requesting user is admin
- [ ] Prevent users from demoting themselves
- [ ] Log admin promotion/demotion actions (audit trail)
- [ ] Prevent removing last admin
- [ ] Add confirmation for admin actions

---

### Phase 5: Capabilities Management API (Admin Only)

**⚠️ TDD REQUIREMENT: Complete all test tasks (5.0) before implementing endpoints (5.1-5.3)**

#### 5.0 Phase 5 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_capabilities.py`
- [ ] Write test for `GET /capabilities/` endpoint (public access)
- [ ] Write test for `GET /capabilities/{id}` endpoint (public access)
- [ ] Write test for `POST /capabilities/` endpoint (admin can create)
- [ ] Write test for `POST /capabilities/` endpoint (non-admin cannot create)
- [ ] Write test for `PUT /capabilities/{id}` endpoint (admin can update)
- [ ] Write test for `PUT /capabilities/{id}` endpoint (non-admin cannot update)
- [ ] Write test for `PATCH /capabilities/{id}` endpoint (admin can partial update)
- [ ] Write test for `DELETE /capabilities/{id}` endpoint (admin can delete)
- [ ] Write test for `DELETE /capabilities/{id}` endpoint (with prerequisites - should fail)
- [ ] Write test for media JSON validation
- [ ] Write test for ULID generation
- [ ] Write integration test for complete CRUD workflow

#### 5.1 Capabilities Schemas
- [ ] Create `CapabilityCreate` schema (name, description, media)
- [ ] Create `CapabilityUpdate` schema (all fields optional)
- [ ] Create `CapabilityResponse` schema (id, name, description, media)
- [ ] Add media validation (JSON array validation)

#### 5.2 Capabilities API Endpoints
- [ ] `GET /capabilities/` - List all capabilities (public, for filtering)
- [ ] `GET /capabilities/{id}` - Get single capability (public)
- [ ] `POST /capabilities/` - Create capability (admin only)
- [ ] `PUT /capabilities/{id}` - Update capability (admin only)
- [ ] `PATCH /capabilities/{id}` - Partial update (admin only)
- [ ] `DELETE /capabilities/{id}` - Delete capability (admin only, check prerequisites)

#### 5.3 Capabilities Business Logic
- [ ] Validate media JSON structure
- [ ] Generate ULID for new capabilities
- [ ] Handle capability deletion (check for event prerequisites)
- [ ] Add error handling and validation

---

### Phase 6: Equipment Management API (Admin Only)

**⚠️ TDD REQUIREMENT: Complete all test tasks (6.0) before implementing endpoints (6.1-6.3)**

#### 6.0 Phase 6 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_equipment.py`
- [ ] Write test for `GET /equipment/` endpoint (public access)
- [ ] Write test for `GET /equipment/{id}` endpoint (public access)
- [ ] Write test for `POST /equipment/` endpoint (admin can create)
- [ ] Write test for `POST /equipment/` endpoint (non-admin cannot create)
- [ ] Write test for `PUT /equipment/{id}` endpoint (admin can update)
- [ ] Write test for `PATCH /equipment/{id}` endpoint (admin can partial update)
- [ ] Write test for `DELETE /equipment/{id}` endpoint (admin can delete)
- [ ] Write test for `DELETE /equipment/{id}` endpoint (with location dependencies - should fail)
- [ ] Write test for media JSON validation
- [ ] Write integration test for complete CRUD workflow

#### 6.1 Equipment Schemas
- [ ] Create `EquipmentCreate` schema (name, description, media)
- [ ] Create `EquipmentUpdate` schema (all fields optional)
- [ ] Create `EquipmentResponse` schema (id, name, description, media)
- [ ] Add media validation (JSON array validation)

#### 6.2 Equipment API Endpoints
- [ ] `GET /equipment/` - List all equipment (public, for filtering)
- [ ] `GET /equipment/{id}` - Get single equipment (public)
- [ ] `POST /equipment/` - Create equipment (admin only)
- [ ] `PUT /equipment/{id}` - Update equipment (admin only)
- [ ] `PATCH /equipment/{id}` - Partial update (admin only)
- [ ] `DELETE /equipment/{id}` - Delete equipment (admin only, check location dependencies)

#### 6.3 Equipment Business Logic
- [ ] Validate media JSON structure
- [ ] Generate ULID for new equipment
- [ ] Handle equipment deletion (check for location dependencies)
- [ ] Add error handling and validation

---

### Phase 7: Location Management API (Admin Only)

**⚠️ TDD REQUIREMENT: Complete all test tasks (7.0) before implementing endpoints (7.1-7.3)**

#### 7.0 Phase 7 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_locations.py`
- [ ] Write test for `GET /locations/` endpoint (public access)
- [ ] Write test for `GET /locations/{id}` endpoint (public access)
- [ ] Write test for `POST /locations/` endpoint (admin can create)
- [ ] Write test for `POST /locations/` endpoint (non-admin cannot create)
- [ ] Write test for `PUT /locations/{id}` endpoint (admin can update)
- [ ] Write test for `PATCH /locations/{id}` endpoint (admin can partial update)
- [ ] Write test for `DELETE /locations/{id}` endpoint (admin can delete)
- [ ] Write test for `DELETE /locations/{id}` endpoint (with event_slots dependencies - should fail)
- [ ] Write test for equipment_ids validation (must exist)
- [ ] Write test for JSON validation (details, equipment_ids)
- [ ] Write integration test for complete CRUD workflow

#### 7.1 Location Schemas
- [ ] Create `LocationCreate` schema (name, details, equipment_ids)
- [ ] Create `LocationUpdate` schema (all fields optional)
- [ ] Create `LocationResponse` schema (id, name, details, equipment_ids)
- [ ] Add JSON validation for details and equipment_ids

#### 7.2 Location API Endpoints
- [ ] `GET /locations/` - List all locations (public, for filtering)
- [ ] `GET /locations/{id}` - Get single location (public)
- [ ] `POST /locations/` - Create location (admin only)
- [ ] `PUT /locations/{id}` - Update location (admin only)
- [ ] `PATCH /locations/{id}` - Partial update (admin only)
- [ ] `DELETE /locations/{id}` - Delete location (admin only, check event_slots dependencies)

#### 7.3 Location Business Logic
- [ ] Validate equipment_ids reference existing equipment
- [ ] Generate ULID for new locations
- [ ] Handle location deletion (check for event_slots dependencies)
- [ ] Add endpoint to expand equipment for a location (expand equipment_ids)

---

### Phase 8: Events Management API (Admin Only)

**⚠️ TDD REQUIREMENT: Complete all test tasks (8.0) before implementing endpoints (8.1-8.3)**

#### 8.0 Phase 8 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_events.py`
- [ ] Write test for `GET /events/` endpoint (public access)
- [ ] Write test for `GET /events/{id}` endpoint (public access)
- [ ] Write test for `POST /events/` endpoint (admin can create)
- [ ] Write test for `POST /events/` endpoint (non-admin cannot create)
- [ ] Write test for `PUT /events/{id}` endpoint (admin can update)
- [ ] Write test for `PATCH /events/{id}` endpoint (admin can partial update)
- [ ] Write test for `DELETE /events/{id}` endpoint (admin can delete, cascades)
- [ ] Write test for prerequisite_ids validation (must exist)
- [ ] Write test for JSON validation (prerequisite_ids)
- [ ] Write integration test for complete CRUD workflow

#### 8.1 Events Schemas
- [ ] Create `EventCreate` schema (name, description, prerequisite_ids)
- [ ] Create `EventUpdate` schema (all fields optional)
- [ ] Create `EventResponse` schema (id, name, description, prerequisite_ids, created_at, updated_at)
- [ ] Add JSON validation for prerequisite_ids

#### 8.2 Events API Endpoints
- [ ] `GET /events/` - List all events (public, for browsing)
- [ ] `GET /events/{id}` - Get single event with details (public)
- [ ] `POST /events/` - Create event (admin only)
- [ ] `PUT /events/{id}` - Update event (admin only)
- [ ] `PATCH /events/{id}` - Partial update (admin only)
- [ ] `DELETE /events/{id}` - Delete event (admin only, cascade to event_slots, attendees)

#### 8.3 Events Business Logic
- [ ] Validate prerequisite_ids reference existing capabilities
- [ ] Generate ULID for new events
- [ ] Handle event deletion (cascade to event_slots, attendees)
- [ ] Add endpoint to expand prerequisites for an event (expand prerequisite_ids)

---

### Phase 9: EventSlots Management API (Admin Only)

**⚠️ TDD REQUIREMENT: Complete all test tasks (9.0) before implementing endpoints (9.1-9.3)**

#### 9.0 Phase 9 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_event_slots.py`
- [ ] Write test for `GET /event-slots/` endpoint (public access)
- [ ] Write test for `GET /event-slots/{id}` endpoint (public access)
- [ ] Write test for `POST /event-slots/` endpoint (admin can create)
- [ ] Write test for `POST /event-slots/` endpoint (non-admin cannot create)
- [ ] Write test for `POST /event-slots/` endpoint (start_time < end_time validation)
- [ ] Write test for `POST /event-slots/` endpoint (overlapping slots at same location - should fail)
- [ ] Write test for `PUT /event-slots/{id}` endpoint (admin can update)
- [ ] Write test for `DELETE /event-slots/{id}` endpoint (admin can delete)
- [ ] Write test for `GET /event-slots/by-event/{event_id}` endpoint
- [ ] Write test for `GET /event-slots/by-location/{location_id}` endpoint
- [ ] Write test for `GET /event-slots/upcoming` endpoint (date filtering)
- [ ] Write test for location_id and event_id validation
- [ ] Write integration test for complete CRUD workflow

#### 9.1 EventSlot Schemas
- [ ] Create `EventSlotCreate` schema (location_id, start_time, end_time, event_id, day_number)
- [ ] Create `EventSlotUpdate` schema (all fields optional)
- [ ] Create `EventSlotResponse` schema (id, location_id, start_time, end_time, event_id, day_number)
- [ ] Add datetime validation for start_time and end_time

#### 9.2 EventSlot API Endpoints
- [ ] `GET /event-slots/` - List all event slots (public, for browsing)
- [ ] `GET /event-slots/{id}` - Get single event slot (public)
- [ ] `POST /event-slots/` - Create event slot (admin only)
- [ ] `PUT /event-slots/{id}` - Update event slot (admin only)
- [ ] `PATCH /event-slots/{id}` - Partial update (admin only)
- [ ] `DELETE /event-slots/{id}` - Delete event slot (admin only)
- [ ] `GET /event-slots/by-event/{event_id}` - Get all slots for an event (public)
- [ ] `GET /event-slots/by-location/{location_id}` - Get slots for a location (public)
- [ ] `GET /event-slots/upcoming` - Get upcoming slots (public, query params for date range)

#### 9.3 EventSlot Business Logic
- [ ] Validate location_id exists
- [ ] Validate event_id exists
- [ ] Validate start_time < end_time
- [ ] Validate no overlapping slots at same location
- [ ] Generate ULID for new event slots
- [ ] Add endpoint to get slots with expanded location and event data

---

### Phase 10: Events Browsing & Filtering API (Public)

**⚠️ TDD REQUIREMENT: Complete all test tasks (10.0) before implementing endpoints (10.1-10.3)**

#### 10.0 Phase 10 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_event_filtering.py`
- [ ] Write test for `GET /events/` endpoint with prerequisite_ids filter
- [ ] Write test for `GET /events/` endpoint with date_range filter
- [ ] Write test for `GET /events/` endpoint with location_id filter
- [ ] Write test for `GET /events/` endpoint with search parameter
- [ ] Write test for `GET /events/` endpoint with pagination
- [ ] Write test for `GET /events/{id}/details` endpoint (expanded data)
- [ ] Write test for `GET /events/available` endpoint (only events with slots)
- [ ] Write test for prerequisite filtering (ALL provided IDs match)
- [ ] Write test for prerequisite filtering with authenticated user
- [ ] Write test for prerequisite match indicators in response
- [ ] Write integration test for complete filtering workflow

#### 10.1 Event Filtering Schemas
- [ ] Create `EventFilterQuery` schema (prerequisite_ids, date_range, location_id, search)
- [ ] Create `EventListResponse` schema (events, total, page, per_page)

#### 10.2 Event Browsing Endpoints
- [ ] `GET /events/` - Enhanced with filtering query parameters
  - [ ] Filter by prerequisite_ids (array of capability IDs)
  - [ ] Filter by date range (events with slots in range)
  - [ ] Filter by location_id
  - [ ] Search by name/description
  - [ ] Pagination support
- [ ] `GET /events/{id}/details` - Get event with expanded data
  - [ ] Include prerequisites with details (expand prerequisite_ids)
  - [ ] Include event slots with location details
  - [ ] Include attendee count
- [ ] `GET /events/available` - Get only events with available slots (public)

#### 10.3 Prerequisite Filtering Logic
- [ ] Filter events where ALL provided prerequisite_ids match
- [ ] Filter events where user has required prerequisites (if authenticated)
- [ ] Return events with prerequisite match indicators
- [ ] Support partial prerequisite matching (optional)

---

### Phase 11: Selections Management API (Authenticated Users)

**⚠️ TDD REQUIREMENT: Complete all test tasks (11.0) before implementing endpoints (11.1-11.3)**

#### 11.0 Phase 11 Tests (WRITE FIRST - BEFORE IMPLEMENTATION)
- [ ] Create test file `tests/test_selections.py`
- [ ] Write test for `GET /selections/my-selections` endpoint (authenticated)
- [ ] Write test for `GET /selections/my-selections` endpoint (unauthenticated - should fail)
- [ ] Write test for `POST /selections/` endpoint (authenticated, auto-creates attendee)
- [ ] Write test for `POST /selections/` endpoint (unauthenticated - should fail)
- [ ] Write test for `POST /selections/batch` endpoint (multiple selections)
- [ ] Write test for `PATCH /selections/{id}` endpoint (own selection)
- [ ] Write test for `PATCH /selections/{id}` endpoint (others' selection - should fail)
- [ ] Write test for `DELETE /selections/{id}` endpoint (own selection)
- [ ] Write test for `GET /selections/my-selections/selected` endpoint (only selected)
- [ ] Write test for `PUT /selections/batch-update` endpoint (batch update)
- [ ] Write test for event_id validation (must exist)
- [ ] Write test for attendee auto-creation on selection
- [ ] Write integration test for complete selections workflow

#### 11.1 Selections Schemas
- [ ] Create `SelectionCreate` schema (event_id) - auto-set attendee_id from user
- [ ] Create `SelectionUpdate` schema (is_selected)
- [ ] Create `SelectionResponse` schema (id, attendee_id, event_id, is_selected, event_details)
- [ ] Create `SelectionBatchCreate` schema (event_ids[]) - for adding multiple selections
- [ ] Create `SelectionListResponse` schema (selections, total)

#### 11.2 Selections API Endpoints
- [ ] `GET /selections/my-selections` - Get current user's selections (authenticated)
- [ ] `POST /selections/` - Create single selection (authenticated, auto-set attendee)
- [ ] `POST /selections/batch` - Create multiple selections at once (authenticated)
- [ ] `PATCH /selections/{id}` - Update selection status (authenticated, own selections only)
- [ ] `DELETE /selections/{id}` - Remove selection (authenticated, own selections only)
- [ ] `GET /selections/my-selections/selected` - Get only selected events for current user
- [ ] `PUT /selections/batch-update` - Batch update multiple selections (authenticated)

#### 11.3 Selections Business Logic
- [ ] Auto-create attendee record if doesn't exist when creating selection
- [ ] Validate event_id exists
- [ ] Ensure user can only manage their own selections
- [ ] Generate ULID for new selections
- [ ] Handle batch operations (transaction support)
- [ ] Return selections with expanded event data

---

## Part 2: Front-end Implementation

### Phase 12: Public User Registration UI

#### 12.1 Registration Page
- [ ] Create public registration page/component
- [ ] Add registration form (email, name, password, password_confirm)
- [ ] Add form validation
- [ ] Add success/error messaging
- [ ] Add redirect to login after successful registration
- [ ] Add "Already have an account?" link to login

#### 12.2 Registration Integration
- [ ] Integrate with `POST /auth/register` endpoint
- [ ] Handle registration errors gracefully
- [ ] Add loading states during submission
- [ ] Add password strength indicator (optional)

---

### Phase 13: User Dashboard & Profile

#### 13.1 User Profile Component
- [ ] Display current user's role (attendee/host/admin)
- [ ] Display user's email and name
- [ ] Show host approval status if applicable
- [ ] Add "Request to Become Host" button (if attendee)
- [ ] Show host request status (pending/approved/denied)

#### 13.2 User Dashboard
- [ ] Create user dashboard page
- [ ] Display user's registered events
- [ ] Display user's selections
- [ ] Display user's hosted events (if host/admin)
- [ ] Add navigation to different sections

---

### Phase 14: Host Request Workflow UI

#### 14.1 Host Request Component
- [ ] Create "Request to Become Host" form/modal
- [ ] Add optional message/reason field
- [ ] Add submit button
- [ ] Show current request status if already requested
- [ ] Display approval/denial status with message

#### 14.2 Host Request Integration
- [ ] Integrate with `POST /hosts/request` endpoint
- [ ] Integrate with `GET /hosts/requests/my-request` endpoint
- [ ] Handle pending/approved/denied states
- [ ] Add success notification on submission

---

### Phase 15: Admin User Management UI

#### 15.1 Admin User List
- [ ] Create admin users management page
- [ ] Display users table with role column
- [ ] Add filter by role
- [ ] Add search functionality
- [ ] Show admin/host/attendee badges

#### 15.2 Admin Promotion UI
- [ ] Add "Promote to Admin" button for each user (admin only)
- [ ] Add confirmation dialog for promotion
- [ ] Add "Demote Admin" button with confirmation
- [ ] Prevent self-demotion UI feedback
- [ ] Show success/error messages

#### 15.3 Admin Host Approval UI
- [ ] Create host requests management page (admin only)
- [ ] Display pending host requests list
- [ ] Show user info and request message
- [ ] Add "Approve" and "Deny" buttons for each request
- [ ] Add confirmation dialogs
- [ ] Show success notifications

---

### Phase 16: Admin Content Management UI

#### 16.1 Admin Dashboard
- [ ] Create admin dashboard/home page
- [ ] Add navigation menu for:
  - [ ] Equipment Management
  - [ ] Locations Management
  - [ ] Capabilities Management
  - [ ] Events Management
  - [ ] Event Slots Management
  - [ ] User Management
  - [ ] Host Requests

#### 16.2 Equipment Management UI (Admin)
- [ ] Create equipment list page
- [ ] Create equipment add/edit form
- [ ] Add create, edit, delete actions
- [ ] Add media upload interface
- [ ] Integrate with equipment API endpoints

#### 16.3 Locations Management UI (Admin)
- [ ] Create locations list page
- [ ] Create location add/edit form
- [ ] Add equipment multi-select
- [ ] Add create, edit, delete actions
- [ ] Integrate with locations API endpoints

#### 16.4 Capabilities Management UI (Admin)
- [ ] Create capabilities list page
- [ ] Create capability add/edit form
- [ ] Add media upload interface
- [ ] Add create, edit, delete actions
- [ ] Integrate with capabilities API endpoints

#### 16.5 Events Management UI (Admin)
- [ ] Create events list page
- [ ] Create event add/edit form
- [ ] Add prerequisites multi-select (from capabilities)
- [ ] Add create, edit, delete actions
- [ ] Integrate with events API endpoints

#### 16.6 EventSlots Management UI (Admin)
- [ ] Create event slots list page
- [ ] Create event slot add/edit form
- [ ] Add event and location dropdowns
- [ ] Add datetime pickers for start/end time
- [ ] Add day number input
- [ ] Add validation feedback (overlaps, time validation)
- [ ] Add create, edit, delete actions
- [ ] Integrate with event slots API endpoints

---

### Phase 17: Events Browsing UI (Attendees)

#### 17.1 Events Browse Page
- [ ] Create public/attendee events browse page
- [ ] Display events list with cards or table
- [ ] Show event name, description, prerequisites
- [ ] Show available slots information
- [ ] Add event detail view/modal

#### 17.2 Prerequisite Filtering UI
- [ ] Add filter sidebar/panel
- [ ] Add multi-select for capabilities/prerequisites
- [ ] Display selected filters as chips/tags
- [ ] Add "Clear Filters" button
- [ ] Show "No events match filters" message
- [ ] Integrate with filtered events API

#### 17.3 Event Detail View
- [ ] Create event detail page/modal
- [ ] Display full event information
- [ ] List all prerequisites with details
- [ ] Show available event slots
- [ ] Show location information
- [ ] Add "Add to Selections" button

---

### Phase 18: Selections Management UI (Attendees)

#### 18.1 My Selections Page
- [ ] Create "My Selections" page for authenticated users
- [ ] Display user's selections list
- [ ] Show selection status (selected/not selected)
- [ ] Show event details for each selection
- [ ] Add filter (show all / show selected only)

#### 18.2 Add Selections Interface
- [ ] Add "Add to Selections" button on events browse page
- [ ] Create "Add Multiple Selections" interface
- [ ] Allow bulk adding from events list (checkboxes)
- [ ] Add confirmation dialog for bulk operations
- [ ] Show success notifications

#### 18.3 Manage Selections
- [ ] Add toggle button to mark selection as selected/not selected
- [ ] Add remove selection button with confirmation
- [ ] Add batch update functionality (select multiple, update status)
- [ ] Show selection count badges
- [ ] Integrate with selections API endpoints

---

## Part 3: Testing & Polish

### Phase 19: Testing

#### 19.1 API Testing
- [ ] Write unit tests for role-based authorization
- [ ] Write tests for host approval workflow
- [ ] Write tests for admin promotion endpoints
- [ ] Write tests for prerequisite filtering
- [ ] Write tests for selections batch operations
- [ ] Test error cases and edge cases

#### 19.2 Front-end Testing
- [ ] Test user registration flow
- [ ] Test host request flow
- [ ] Test admin user management
- [ ] Test events browsing and filtering
- [ ] Test selections management
- [ ] Test role-based UI visibility

#### 19.3 Integration Testing
- [ ] Test complete user journey (sign up → browse → select)
- [ ] Test host approval workflow end-to-end
- [ ] Test admin content management workflows

---

## Testing Methodology: Test-Driven Development (TDD)

### ⚠️ CRITICAL: Test-First Approach Required

**All API endpoints must follow Test-Driven Development (TDD):**

1. **Write ALL tests for a phase BEFORE implementing that phase**
   - For Phase 1, write all Phase 1 tests first
   - For Phase 2, write all Phase 2 tests first
   - Continue this pattern for all backend API phases

2. **Test Coverage Requirements:**
   - Unit tests for all endpoints
   - Integration tests for complete workflows
   - Error case testing (invalid input, unauthorized access, etc.)
   - Edge case testing (boundary conditions, empty data, etc.)
   - Authentication/authorization testing (role-based access)

3. **Test Implementation Order:**
   - ✅ Phase 1: Write all tests for User Roles & Permissions API
   - ✅ Phase 1: Implement User Roles & Permissions API (tests should pass)
   - ✅ Phase 2: Write all tests for Public Registration API
   - ✅ Phase 2: Implement Public Registration API (tests should pass)
   - Continue this pattern for Phases 3-11

4. **Testing Framework:**
   - Use pytest for Python backend tests
   - Use FastAPI TestClient for API endpoint testing
   - Mock database dependencies where appropriate
   - Use test fixtures for common test data
   - Isolate tests (each test should be independent)

5. **Test Quality:**
   - Tests should be clear and readable
   - Test names should describe what they're testing
   - Tests should fail first (red), then pass after implementation (green)
   - Maintain high test coverage (aim for 80%+ for new code)

### Testing Workflow Per Phase:

```
For each Backend API Phase:
1. 📝 Write all tests for the phase (they will fail - this is expected)
2. 🏗️ Implement the API endpoints
3. ✅ Verify all tests pass
4. 🔍 Review and refactor if needed
5. 🚀 Deploy to production
6. ➡️ Move to next phase
```

### Example for Phase 1:
- Write tests for: `GET /users/me`, `PATCH /users/{id}/role`, `POST /users/{id}/promote-admin`, `GET /users/by-role/{role}`
- Write tests for: `require_admin`, `require_host_or_admin`, `get_current_user` dependencies
- Write tests for: Error cases (unauthorized, invalid roles, etc.)
- THEN implement the actual API endpoints
- Verify all tests pass
- Deploy

---

## Implementation Priority & Order

### Must Complete in Order:
1. **Phase 1**: User Roles & Permissions System
   - ⚠️ Write all Phase 1 tests FIRST, then implement
2. **Phase 2**: Public User Registration
   - ⚠️ Write all Phase 2 tests FIRST, then implement
3. **Phase 3**: Host Approval Workflow
   - ⚠️ Write all Phase 3 tests FIRST, then implement
4. **Phase 4**: Admin User Management
   - ⚠️ Write all Phase 4 tests FIRST, then implement
5. **Phase 5-9**: Admin Content Management (Capabilities, Equipment, Locations, Events, EventSlots)
   - ⚠️ Write all tests for each phase FIRST, then implement
6. **Phase 10**: Events Browsing & Filtering API
   - ⚠️ Write all Phase 10 tests FIRST, then implement
7. **Phase 11**: Selections Management API
   - ⚠️ Write all Phase 11 tests FIRST, then implement
8. **Phase 12-18**: Front-end implementation for all features
   - Front-end tests can follow component-driven testing approach

### Notes:
- **Backend API: Test-First Required** - All tests for a phase must be written before implementation
- Backend phases should be completed before corresponding front-end phases
- Each phase builds on previous phases
- All tests must pass before moving to the next phase
- Deploy to production after each phase (with passing tests)

---

## Current Status

✅ **Completed Infrastructure & Authentication:**
- ✅ Complete Google Cloud infrastructure (Terraform deployed)
- ✅ FastAPI backend deployed to Cloud Run with health checks
- ✅ Google OAuth authentication system with session management
- ✅ Admin interface with OAuth protection (`?admin=true` flag)
- ✅ Flutter web app with Material Design 3 and authentication
- ✅ Cross-domain authentication (Flutter app on GCS, backend on Cloud Run)
- ✅ Production deployment scripts (`./scripts/deploy.sh` for backend, `./scripts/deploy-frontend.sh` for Flutter)
- ✅ CORS middleware properly configured for web clients
- ✅ Database models defined and migration scripts created
- ✅ User registration API (POST /users/register) - public endpoint working
- ✅ User management API (GET /users/, GET /users/{id}, basic CRUD)

✅ **Completed Frontend & UI:**
- ✅ Flutter web app with profile page functionality
- ✅ Google OAuth integration with return URL handling
- ✅ User authentication state management and display
- ✅ Profile page: "Hi, [name]!" greeting + sign out button
- ✅ Admin panel accessible via OAuth with admin flag
- ✅ Production deployment with timestamped subdirectories for cache busting
- ✅ Connection status monitoring and health checks

✅ **Completed DevOps & Deployment:**
- ✅ Docker containerization for backend
- ✅ Google Cloud Run deployment with auto-scaling
- ✅ Google Cloud SQL (MySQL) with automated backups
- ✅ Artifact Registry for Docker images
- ✅ Secret Manager for database passwords
- ✅ IAM roles and service accounts properly configured
- ✅ Environment-based configuration (development/production)
- ✅ Deployment workflow documentation in CLAUDE.md

### 🌐 **Live Production URLs:**
- **Backend API**: https://acro-planner-backend-733697808355.us-central1.run.app
- **Admin Interface**: https://acro-planner-backend-733697808355.us-central1.run.app/admin (use `?admin=true` for OAuth)
- **Flutter App**: https://storage.googleapis.com/acro-planner-flutter-app-733697808355/release_20251103_202322/index.html
- **Health Check**: https://acro-planner-backend-733697808355.us-central1.run.app/health

### ✨ **Working Features:**
- ✅ User registration and Google OAuth authentication
- ✅ Cross-domain authentication between Flutter app and backend
- ✅ Profile page with personalized greeting and sign out
- ✅ Admin panel access with role-based OAuth flow
- ✅ Health monitoring and connection status
- ✅ Production-ready infrastructure with auto-scaling

🔄 **Currently Working On:**
- ✅ OAuth flow fixes (default to Flutter app, admin flag support)
- ✅ Profile page implementation and deployment

🔄 **Next Steps (Backend API Implementation):**
- Phase 1: User Roles & Permissions System (extend current user system)
- Phase 2: Host Approval Workflow  
- Phase 3: Admin User Management
- Phase 4: Content Management APIs (Capabilities, Equipment, Locations, Events)

⏳ **Future Phases:**
- Event browsing and filtering
- Selections management
- Advanced frontend features
- Mobile app enhancements

---

## Technical Considerations

### Development Practices
- **Test-Driven Development**: Write all tests for a phase before implementation
- **ULID Generation**: Use ULID library for all ID generation
- **JSON Fields**: Validate JSON structure for all JSON columns
- **Foreign Keys**: Always validate foreign key references exist
- **Role-Based Access**: Implement early and test thoroughly
- **Authentication**: All endpoints except public registration should require authentication
- **Error Messages**: Provide clear, actionable error messages
- **Default Roles**: All new users default to 'attendee' role
- **Host Approval**: Host requests require admin approval before role change

### Testing Standards
- Use pytest for Python backend testing
- Use FastAPI TestClient for API testing
- Maintain 80%+ test coverage for new code
- Write tests that are independent and isolated
- Test error cases, edge cases, and authorization scenarios

---

## To Plan - Future Features & Enhancements

This section documents features and enhancements that are not part of the current priority implementation but should be planned for future phases.

### User Account & Profile Features

#### Account Management
- [ ] Password reset functionality (forgot password flow)
- [ ] Email verification system (verify email on registration)
- [ ] User profile editing (update name, email, preferences)
- [ ] Profile picture upload and management
- [ ] Account deletion/deactivation
- [ ] Two-factor authentication (2FA)
- [ ] Social login integration (beyond OAuth)
- [ ] User preferences/settings page

#### User Profile Enhancements
- [ ] Public user profiles
- [ ] User bio/description field
- [ ] User skill/capability tracking (what they've learned)
- [ ] User achievement/badge system
- [ ] User activity history
- [ ] Profile completion indicators

---

### Event Registration & Attendance

#### Registration Features
- [ ] Actual event registration (beyond selections)
- [ ] Registration confirmation emails
- [ ] Event waitlist functionality
- [ ] Event capacity limits and enforcement
- [ ] Registration cancellation flow
- [ ] Transfer registration to another user
- [ ] Event reminders (email/push notifications)
- [ ] Check-in functionality (mark attendance at event)

#### Attendance Tracking
- [ ] Attendance tracking and reporting
- [ ] Attendance history per user
- [ ] Attendance statistics (for hosts/admins)
- [ ] No-show tracking
- [ ] Attendance certificates/completion tracking

---

### Host Features

#### Host Management
- [ ] Host profile pages
- [ ] Host bio and credentials
- [ ] Host photo galleries
- [ ] Host social media links management
- [ ] Host rating/review system
- [ ] Host availability calendar
- [ ] Host event creation (if hosts can create events)
- [ ] Host event management dashboard

#### Host Content
- [ ] Host event descriptions/instructions
- [ ] Host event materials/resources
- [ ] Host event prerequisites recommendations
- [ ] Host event photos upload and management
- [ ] Host video content management

---

### Event Features & Enhancements

#### Event Discovery
- [ ] Event search with advanced filters
- [ ] Event recommendations based on user capabilities
- [ ] Event categories/tags system
- [ ] Event favorites/bookmarks
- [ ] Event sharing functionality
- [ ] Event calendar view (monthly/weekly/daily)
- [ ] Event map view (showing locations)
- [ ] Event price/fee management (if applicable)

#### Event Content
- [ ] Rich text editor for event descriptions
- [ ] Event image galleries
- [ ] Event video content
- [ ] Event materials/resources downloads
- [ ] Event Q&A section
- [ ] Event comments/feedback
- [ ] Event reviews and ratings

#### Event Management
- [ ] Event duplication/copying
- [ ] Event templates for hosts
- [ ] Recurring events support
- [ ] Event series management
- [ ] Event cancellation/refund handling
- [ ] Event capacity management
- [ ] Event waitlist management

---

### Advanced Filtering & Search

#### Enhanced Search
- [ ] Full-text search across events, capabilities, equipment
- [ ] Search suggestions/autocomplete
- [ ] Saved search filters
- [ ] Search history
- [ ] Advanced search with multiple criteria combinations

#### Filtering Enhancements
- [ ] Filter by date ranges (start/end dates)
- [ ] Filter by time of day
- [ ] Filter by location proximity (geolocation)
- [ ] Filter by host
- [ ] Filter by event type/category
- [ ] Filter by skill level required
- [ ] Filter by event capacity/availability
- [ ] Filter combinations (AND/OR logic)

---

### Selections & Planning

#### Selection Features
- [ ] Selection calendar view
- [ ] Selection conflict detection (overlapping events)
- [ ] Selection priority/ranking
- [ ] Selection sharing (share selections with others)
- [ ] Selection templates/presets
- [ ] Selection notes/reminders

#### Planning Tools
- [ ] Personal schedule/calendar view
- [ ] Schedule conflict warnings
- [ ] Schedule optimization suggestions
- [ ] Export schedule to calendar (iCal, Google Calendar)
- [ ] Print schedule functionality

---

### Notifications & Communications

#### Notification System
- [ ] Email notification preferences
- [ ] Push notifications (web/mobile)
- [ ] SMS notifications (optional)
- [ ] In-app notification center
- [ ] Notification history
- [ ] Customizable notification rules

#### Communication Features
- [ ] Messaging system (user-to-user)
- [ ] Event discussion forums
- [ ] Event announcements
- [ ] Host-to-attendee messaging
- [ ] Admin broadcast messages
- [ ] Event updates/notifications

---

### Media & File Management

#### Media Handling
- [ ] Image upload and storage (equipment, capabilities, events)
- [ ] Video upload and storage
- [ ] Media library/gallery management
- [ ] Image optimization/resizing
- [ ] CDN integration for media delivery
- [ ] Media access control/permissions
- [ ] Bulk media upload

#### File Management
- [ ] Document uploads (event materials, PDFs)
- [ ] File storage integration (GCS/S3)
- [ ] File access control
- [ ] File versioning
- [ ] File download tracking

---

### Analytics & Reporting

#### User Analytics
- [ ] User activity tracking
- [ ] User engagement metrics
- [ ] User journey analysis
- [ ] Conversion funnel analysis

#### Event Analytics
- [ ] Event attendance statistics
- [ ] Event popularity metrics
- [ ] Event completion rates
- [ ] Event feedback aggregation
- [ ] Event revenue tracking (if applicable)

#### Admin Analytics
- [ ] Dashboard with key metrics
- [ ] User growth charts
- [ ] Event creation trends
- [ ] Registration trends
- [ ] Popular events/capabilities reports
- [ ] Geographic distribution of users/events
- [ ] Custom report generation
- [ ] Data export functionality (CSV, Excel)

---

### Admin Features

#### Advanced Admin Tools
- [ ] Admin activity log/audit trail
- [ ] Admin action history
- [ ] Bulk user operations
- [ ] Bulk event operations
- [ ] Data import/export tools
- [ ] Database backup/restore UI
- [ ] System health monitoring dashboard
- [ ] Error log viewing

#### Content Moderation
- [ ] Content moderation queue
- [ ] Flag/report inappropriate content
- [ ] Auto-moderation rules
- [ ] Content review workflow
- [ ] User suspension/ban functionality

---

### Integration & APIs

#### Third-Party Integrations
- [ ] Calendar integrations (Google Calendar, iCal, Outlook)
- [ ] Payment processing integration (Stripe, PayPal)
- [ ] Email service integration (SendGrid, Mailgun)
- [ ] SMS service integration (Twilio)
- [ ] Social media sharing integration
- [ ] Analytics integration (Google Analytics)

#### API Enhancements
- [ ] GraphQL API (alternative to REST)
- [ ] Webhooks for event updates
- [ ] API versioning strategy
- [ ] API rate limiting and quotas
- [ ] API documentation improvements (Swagger/OpenAPI)
- [ ] SDK development (JavaScript, Python)
- [ ] Public API access with API keys

---

### Mobile App Features

#### Flutter App Enhancements
- [ ] Offline mode support
- [ ] Push notifications
- [ ] Mobile-optimized UI/UX
- [ ] Camera integration for profile/event photos
- [ ] Geolocation features
- [ ] Mobile calendar integration
- [ ] Biometric authentication
- [ ] Mobile payments (if applicable)

---

### Performance & Scalability

#### Optimization
- [ ] Caching strategy (Redis)
- [ ] Database query optimization
- [ ] CDN for static assets
- [ ] Image CDN integration
- [ ] API response compression
- [ ] Lazy loading for large lists
- [ ] Infinite scroll vs pagination
- [ ] Database indexing optimization

#### Monitoring & Observability
- [ ] Application performance monitoring (APM)
- [ ] Error tracking (Sentry, Rollbar)
- [ ] Log aggregation and analysis
- [ ] Uptime monitoring
- [ ] Performance metrics dashboard
- [ ] Real user monitoring (RUM)

---

### Security & Compliance

#### Security Enhancements
- [ ] Rate limiting on all endpoints
- [ ] DDoS protection
- [ ] SQL injection prevention audit
- [ ] XSS prevention audit
- [ ] CSRF protection
- [ ] Security headers configuration
- [ ] Regular security audits
- [ ] Penetration testing
- [ ] Data encryption at rest
- [ ] API key rotation

#### Compliance
- [ ] GDPR compliance features
- [ ] Data privacy controls
- [ ] Data export functionality (user data)
- [ ] Data deletion requests
- [ ] Cookie consent management
- [ ] Terms of service acceptance tracking
- [ ] Privacy policy acceptance tracking

---

### Accessibility & Internationalization

#### Accessibility
- [ ] WCAG 2.1 AA compliance
- [ ] Screen reader optimization
- [ ] Keyboard navigation improvements
- [ ] High contrast mode
- [ ] Font size controls
- [ ] Color blind friendly design
- [ ] ARIA labels and roles

#### Internationalization
- [ ] Multi-language support
- [ ] Language selection
- [ ] Date/time localization
- [ ] Currency localization (if applicable)
- [ ] RTL language support
- [ ] Translation management system

---

### Testing & Quality Assurance

#### Testing Enhancements
- [ ] Automated E2E testing (Playwright, Cypress)
- [ ] Performance testing (load testing)
- [ ] Security testing automation
- [ ] Visual regression testing
- [ ] Accessibility testing automation
- [ ] Cross-browser testing
- [ ] Mobile device testing

#### Quality Assurance
- [ ] Code coverage targets
- [ ] Automated code quality checks
- [ ] Documentation coverage
- [ ] User acceptance testing framework
- [ ] Beta testing program
- [ ] Feedback collection system

---

### Data Management

#### Data Features
- [ ] Data backup automation
- [ ] Data recovery procedures
- [ ] Data migration tools
- [ ] Data archiving strategy
- [ ] Data retention policies
- [ ] Database optimization scripts
- [ ] Database maintenance automation

---

### Miscellaneous Features

#### User Experience
- [ ] Onboarding flow for new users
- [ ] Help/FAQ section
- [ ] Tutorial/walkthrough system
- [ ] Feedback system
- [ ] Feature request system
- [ ] Dark mode theme
- [ ] Customizable dashboard layouts

#### Business Features
- [ ] Pricing/tier management (if applicable)
- [ ] Subscription management (if applicable)
- [ ] Billing/invoicing (if applicable)
- [ ] Referral program
- [ ] Affiliate system

#### Technical Debt
- [ ] Code refactoring opportunities
- [ ] Dependency updates
- [ ] Legacy code migration
- [ ] Architecture improvements
- [ ] Performance bottlenecks resolution

---

*Last Updated: [Date]*
*Version: 2.0 - Reorganized for User-First Development*
