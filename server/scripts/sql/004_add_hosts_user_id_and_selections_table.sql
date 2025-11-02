-- Acro Planner Database Migration
-- File: 004_add_hosts_user_id_and_selections_table.sql
-- Description: Add user_id column to hosts table and create selections table

-- Add user_id column to hosts table
ALTER TABLE hosts 
ADD COLUMN user_id CHAR(26) NOT NULL,
ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Create selections table
CREATE TABLE selections (
    id CHAR(26) PRIMARY KEY,
    attendee_id CHAR(26) NOT NULL,
    event_id CHAR(26) NOT NULL,
    is_selected BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (attendee_id) REFERENCES attendees(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

