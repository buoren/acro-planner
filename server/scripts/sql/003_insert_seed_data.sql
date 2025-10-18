-- Acro Planner Seed Data
-- File: 003_insert_seed_data.sql
-- Description: Insert initial/seed data into the database

-- Sample users (password: 'admin123' - change in production!)
INSERT INTO users (id, email, name, password_hash, salt) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0X3', 'admin@acro-planner.com', 'Admin User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvysKU6EkQEMc7y', 'randomsalt123'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0X4', 'instructor@acro-planner.com', 'Jane Smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvysKU6EkQEMc7y', 'randomsalt124'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0X5', 'student@acro-planner.com', 'John Doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvysKU6EkQEMc7y', 'randomsalt125');

-- Sample equipment
INSERT INTO equipment (id, name, description, media) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0E1', 'Yoga Mats', 'High-quality yoga mats for floor work', '[]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0E2', 'Crash Pads', 'Safety crash pads for aerial work', '[]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0E3', 'Balance Blocks', 'Wooden blocks for handstand practice', '[]');

-- Sample locations
INSERT INTO locations (id, name, details, equipment_ids) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0L1', 'Main Studio', '{"address": "123 Acro St", "capacity": 20}', '["01J8X7F9E2P8Q3R6S9T4V7W0E1", "01J8X7F9E2P8Q3R6S9T4V7W0E2"]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0L2', 'Outdoor Park', '{"address": "Central Park Area", "capacity": 15}', '["01J8X7F9E2P8Q3R6S9T4V7W0E1"]');

-- Sample capabilities
INSERT INTO capabilities (id, name, description, media) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0C1', 'Forward Roll', 'Basic forward rolling movement', '[]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0C2', 'Cartwheel', 'Side-ways wheel movement', '[]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0C3', 'Handstand', 'Inverted position on hands', '[]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0C4', 'Backflip', 'Backward somersault', '[]');

-- Sample events
INSERT INTO events (id, name, description, prerequisite_ids) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0V1', 'Beginner Acro Workshop', 'Introduction to basic acrobatic movements', '["01J8X7F9E2P8Q3R6S9T4V7W0C1"]'),
    ('01J8X7F9E2P8Q3R6S9T4V7W0V2', 'Advanced Flow Session', 'Connecting movements into flowing sequences', '["01J8X7F9E2P8Q3R6S9T4V7W0C2", "01J8X7F9E2P8Q3R6S9T4V7W0C3"]');

-- Sample event slots
INSERT INTO event_slots (id, location_id, start_time, end_time, event_id, day_number) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0S1', '01J8X7F9E2P8Q3R6S9T4V7W0L1', '2024-01-15 18:00:00', '2024-01-15 19:30:00', '01J8X7F9E2P8Q3R6S9T4V7W0V1', 1),
    ('01J8X7F9E2P8Q3R6S9T4V7W0S2', '01J8X7F9E2P8Q3R6S9T4V7W0L1', '2024-01-16 19:00:00', '2024-01-16 20:15:00', '01J8X7F9E2P8Q3R6S9T4V7W0V2', 1);

-- Sample attendees
INSERT INTO attendees (id, user_id, event_id, is_registered) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0A1', '01J8X7F9E2P8Q3R6S9T4V7W0X5', '01J8X7F9E2P8Q3R6S9T4V7W0V1', TRUE),
    ('01J8X7F9E2P8Q3R6S9T4V7W0A2', '01J8X7F9E2P8Q3R6S9T4V7W0X5', '01J8X7F9E2P8Q3R6S9T4V7W0V2', FALSE);

-- Sample hosts
INSERT INTO hosts (id, attendee_id, photos, links) VALUES 
    ('01J8X7F9E2P8Q3R6S9T4V7W0H1', '01J8X7F9E2P8Q3R6S9T4V7W0A1', '[]', '{"instagram": "@acroinstructor"}');