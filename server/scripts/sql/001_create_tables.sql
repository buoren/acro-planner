-- Acro Planner Database Schema
-- File: 001_create_tables.sql
-- Description: Create all database tables

-- Users table
CREATE TABLE users (
    id CHAR(26) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Equipment table
CREATE TABLE equipment (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    media JSON
);

-- Locations table
CREATE TABLE locations (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    details JSON,
    equipment_ids JSON COMMENT 'Array of equipment ULIDs'
);

-- Capabilities table
CREATE TABLE capabilities (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    media JSON
);

-- Events table
CREATE TABLE events (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    prerequisite_ids JSON COMMENT 'Array of capability ULIDs',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Event slots table
CREATE TABLE event_slots (
    id CHAR(26) PRIMARY KEY,
    location_id CHAR(26) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    event_id CHAR(26) NOT NULL,
    day_number INT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE RESTRICT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Attendees table
CREATE TABLE attendees (
    id CHAR(26) PRIMARY KEY,
    user_id CHAR(26) NOT NULL,
    event_id CHAR(26) NOT NULL,
    is_registered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_event (user_id, event_id)
);

-- Hosts table
CREATE TABLE hosts (
    id CHAR(26) PRIMARY KEY,
    attendee_id CHAR(26) NOT NULL,
    photos JSON,
    links JSON,
    FOREIGN KEY (attendee_id) REFERENCES attendees(id) ON DELETE CASCADE
);