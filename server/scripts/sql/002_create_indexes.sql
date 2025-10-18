-- Acro Planner Database Indexes
-- File: 002_create_indexes.sql
-- Description: Create database indexes for performance optimization

-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Equipment table indexes
CREATE INDEX idx_equipment_name ON equipment(name);

-- Locations table indexes
CREATE INDEX idx_locations_name ON locations(name);

-- Capabilities table indexes
CREATE INDEX idx_capabilities_name ON capabilities(name);

-- Events table indexes
CREATE INDEX idx_events_name ON events(name);
CREATE INDEX idx_events_created_at ON events(created_at);

-- Event slots table indexes
CREATE INDEX idx_event_slots_location_id ON event_slots(location_id);
CREATE INDEX idx_event_slots_event_id ON event_slots(event_id);
CREATE INDEX idx_event_slots_start_time ON event_slots(start_time);
CREATE INDEX idx_event_slots_end_time ON event_slots(end_time);
CREATE INDEX idx_event_slots_day_number ON event_slots(day_number);

-- Attendees table indexes
CREATE INDEX idx_attendees_user_id ON attendees(user_id);
CREATE INDEX idx_attendees_event_id ON attendees(event_id);
CREATE INDEX idx_attendees_is_registered ON attendees(is_registered);

-- Hosts table indexes
CREATE INDEX idx_hosts_attendee_id ON hosts(attendee_id);