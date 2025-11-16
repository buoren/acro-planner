# MVP Gap Analysis - Backend APIs and Services

## Summary
After reviewing the codebase, here are the missing pieces needed for a functional MVP:

## ✅ What Exists (Good Coverage)

### Authentication & Users
- ✅ User registration (`POST /users/register`)
- ✅ OAuth login/logout
- ✅ Password reset
- ✅ User management (CRUD)
- ✅ Role management (admin, host, attendee)

### Conventions
- ✅ Convention CRUD (`POST/GET/PUT/DELETE /conventions`)
- ✅ Location management (`POST/GET/PUT /conventions/{id}/locations`)
- ✅ Event slot management (`POST/GET/PUT/DELETE /conventions/{id}/event-slots`)

### Workshops/Events
- ✅ Workshop CRUD (`POST/GET/PUT/DELETE /workshops`)
- ✅ Workshop prerequisites management
- ✅ Workshop equipment management
- ✅ Host availability management
- ✅ Workshop browsing with filters

### Attendees
- ✅ Workshop selection/registration (`POST /attendees/selections`)
- ✅ Schedule viewing (`GET /attendees/schedule`)
- ✅ Selection updates (`PUT /attendees/selections/{id}`)

### Supporting Data
- ✅ Prerequisites/Capabilities CRUD
- ✅ Equipment CRUD

## ❌ Missing Critical MVP Functionality

### 1. Convention Registration Endpoints
**Status:** Manager methods exist (`AttendeeManager.sign_up_for_convention`, `register_for_convention`) but **NO API endpoints**

**Missing:**
- `POST /conventions/{convention_id}/register` - Sign up for convention (before payment)
- `POST /conventions/{convention_id}/complete-registration` - Complete registration after payment
- `GET /conventions/{convention_id}/attendees` - List attendees (admin/host)
- `GET /attendees/my-conventions` - Get my registered conventions

**Impact:** Users cannot register for conventions through the API

### 2. Event-to-Slot Assignment
**Status:** Manager method exists (`EventsManager.assign_event_to_slot`) but **NO API endpoint**

**Missing:**
- `POST /workshops/{workshop_id}/assign-slot` - Assign workshop to an event slot
- `DELETE /workshops/{workshop_id}/unassign-slot/{slot_id}` - Unassign workshop from slot
- `GET /event-slots/{slot_id}/workshop` - Get workshop assigned to a slot
- `GET /workshops/{workshop_id}/slots` - Get all slots for a workshop

**Impact:** Hosts/admins cannot schedule workshops to time slots

### 3. Bulk Slot Creation
**Status:** Manager method exists (`ConventionManager.add_slots_for_convention`) but **NO API endpoint**

**Missing:**
- `POST /conventions/{convention_id}/bulk-slots` - Create multiple slots at once (for multiple days/locations)

**Impact:** Admins must create slots one-by-one, which is inefficient

### 4. Attendee Interest/Registration for Events
**Status:** Manager methods exist (`AttendeeManager.show_interest`, `register_for_event`) but **NO API endpoints**

**Missing:**
- `POST /workshops/{workshop_id}/show-interest` - Show interest in a workshop
- `POST /workshops/{workshop_id}/register` - Register for a workshop
- `GET /workshops/{workshop_id}/attendees` - List attendees (host/admin)

**Impact:** The current `/attendees/selections` endpoint requires `event_slot_id`, but users might want to show interest before slots are assigned

### 5. Query/Filter Endpoints
**Missing:**
- `GET /workshops?available_slots_only=true` - Only workshops with available slots
- `GET /event-slots?available=true` - Only empty slots
- `GET /conventions/{id}/schedule` - Full schedule view for a convention
- `GET /attendees/{id}/capabilities` - Get attendee's fulfilled capabilities

### 6. Host Management
**Status:** Some functionality exists but incomplete

**Missing:**
- `POST /hosts/apply` - Apply to become a host (attendee → host)
- `GET /hosts/pending` - List pending host applications (admin)
- `POST /hosts/{host_id}/approve` - Approve host application (admin)
- `GET /hosts/my-workshops` - Get my workshops (host)

### 7. Data Validation & Business Logic
**Missing:**
- Validation that workshop prerequisites are valid capabilities
- Validation that equipment exists and is available
- Check for slot conflicts when assigning events
- Check for location capacity when assigning events
- Automatic cleanup of selections when workshop is deleted

### 8. Integration Issues
**Problems Found:**
- `ConventionManager.add_slots_for_convention` creates slots without `event_id` (now nullable, but should be None)
- `EventSlot` model has `convention_id` but routes don't always set it
- Some routes use direct DB queries instead of manager classes
- Inconsistent error handling across routes

## 🔧 Recommended Priority Order for MVP

### Priority 1 (Critical - Blocking MVP)
1. **Convention Registration Endpoints** - Users need to register for conventions
2. **Event-to-Slot Assignment** - Workshops need to be scheduled to time slots
3. **Bulk Slot Creation** - Admins need efficient slot setup

### Priority 2 (Important - Better UX)
4. **Attendee Interest/Registration** - Users need simpler ways to interact with workshops
5. **Host Management** - Need workflow for becoming a host
6. **Query/Filter Endpoints** - Better data discovery

### Priority 3 (Nice to Have)
7. **Enhanced Validation** - Better error messages and business rules
8. **Integration Improvements** - Use manager classes consistently

## 📝 Notes

- Manager classes (`AttendeeManager`, `EventsManager`, `ConventionManager`) have good functionality but aren't fully exposed via API
- The codebase has good separation of concerns (managers vs routes)
- Test coverage exists for managers but may need route-level tests
- Some endpoints exist but may need refinement (e.g., `/attendees/selections` is complex)

