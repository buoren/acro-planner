-- Acro Planner Database Migration
-- File: 005_add_selections_indexes.sql
-- Description: Add indexes for hosts.user_id and selections table

-- Hosts table indexes
CREATE INDEX idx_hosts_user_id ON hosts(user_id);

-- Selections table indexes
CREATE INDEX idx_selections_attendee_id ON selections(attendee_id);
CREATE INDEX idx_selections_event_id ON selections(event_id);
CREATE INDEX idx_selections_is_selected ON selections(is_selected);

