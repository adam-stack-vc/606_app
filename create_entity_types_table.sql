-- Create entity_types table
-- This table will store venue information with their entity types

CREATE TABLE IF NOT EXISTS entity_types (
    id SERIAL PRIMARY KEY,
    venue_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) NOT NULL,
    description TEXT,
    parent_organization VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_entity_types_venue_name ON entity_types(venue_name);
CREATE INDEX IF NOT EXISTS idx_entity_types_entity_type ON entity_types(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_types_parent_org ON entity_types(parent_organization);

-- Add comments for documentation
COMMENT ON TABLE entity_types IS 'Maps venues to their entity types (Broker, ATS, EXCH)';
COMMENT ON COLUMN entity_types.venue_name IS 'Canonical venue name as it appears in the main data';
COMMENT ON COLUMN entity_types.entity_type IS 'Type of entity: Broker, ATS, or EXCH';
COMMENT ON COLUMN entity_types.description IS 'Description of the entity type';
COMMENT ON COLUMN entity_types.parent_organization IS 'Parent organization (e.g., CBOE, Nasdaq, NYSE)';
