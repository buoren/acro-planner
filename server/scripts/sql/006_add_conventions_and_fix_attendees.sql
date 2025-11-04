-- Migration: Add Conventions table and fix Attendees table
-- File: 006_add_conventions_and_fix_attendees.sql
-- Description: Add Conventions table and update Attendees to reference conventions instead of events

-- Add Conventions table
CREATE TABLE IF NOT EXISTS conventions (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add convention_id to events table
ALTER TABLE events 
ADD COLUMN convention_id CHAR(26),
ADD FOREIGN KEY (convention_id) REFERENCES conventions(id) ON DELETE SET NULL;

-- Update attendees table to reference conventions instead of events
-- First, drop the foreign key constraint
ALTER TABLE attendees DROP FOREIGN KEY attendees_ibfk_2;

-- Drop the unique constraint
ALTER TABLE attendees DROP KEY unique_user_event;

-- Add convention_id column 
ALTER TABLE attendees 
ADD COLUMN convention_id CHAR(26),
ADD FOREIGN KEY (convention_id) REFERENCES conventions(id) ON DELETE SET NULL;

-- Make event_id nullable (since we're changing the relationship model)
ALTER TABLE attendees MODIFY event_id CHAR(26) NULL;

-- Remove event_id column entirely (attendees should link to conventions, not events)
ALTER TABLE attendees DROP COLUMN event_id;

-- Add created_at and updated_at columns to attendees if they don't exist
ALTER TABLE attendees 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Add user_id column to hosts table for direct reference
ALTER TABLE hosts 
ADD COLUMN user_id CHAR(26),
ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add created_at and updated_at to admins table if they don't exist
CREATE TABLE IF NOT EXISTS admins (
    id CHAR(26) PRIMARY KEY,
    user_id CHAR(26) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);