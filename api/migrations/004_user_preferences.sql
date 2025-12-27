-- Sprint 5.4: User Preferences Table
-- Migration: 004
-- Description: Add user_preferences table for storing UI settings and theme choices

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Display Settings
    theme VARCHAR(50) DEFAULT 'light',
    tooltips_enabled BOOLEAN DEFAULT TRUE,
    show_advanced_options BOOLEAN DEFAULT FALSE,
    decimal_places INTEGER DEFAULT 1 CHECK (decimal_places BETWEEN 0 AND 5),
    number_format VARCHAR(20) DEFAULT 'us',  -- 'us', 'european', 'international'
    currency_symbol VARCHAR(10) DEFAULT '$',
    
    -- Chart Settings
    chart_theme VARCHAR(50) DEFAULT 'plotly_white',
    default_chart_type VARCHAR(20) DEFAULT 'line',
    color_palette VARCHAR(50) DEFAULT 'default',
    legend_position VARCHAR(20) DEFAULT 'top',
    
    -- Animation Settings (for Matrix theme, etc.)
    animation_enabled BOOLEAN DEFAULT TRUE,
    animation_speed VARCHAR(20) DEFAULT 'normal',  -- 'slow', 'normal', 'fast', 'off'
    
    -- Performance Settings
    cache_duration_policies INTEGER DEFAULT 3600,  -- seconds
    cache_duration_cbo_data INTEGER DEFAULT 86400,  -- seconds
    cache_duration_charts INTEGER DEFAULT 600,  -- seconds
    auto_refresh_data BOOLEAN DEFAULT FALSE,
    max_monte_carlo_iterations INTEGER DEFAULT 10000,
    
    -- Advanced Settings
    debug_mode BOOLEAN DEFAULT FALSE,
    experimental_features BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(255) DEFAULT 'http://localhost:5000',
    
    -- Notification Preferences
    email_notifications BOOLEAN DEFAULT TRUE,
    notify_simulation_complete BOOLEAN DEFAULT TRUE,
    notify_policy_updates BOOLEAN DEFAULT FALSE,
    notify_new_features BOOLEAN DEFAULT TRUE,
    notify_weekly_digest BOOLEAN DEFAULT FALSE,
    
    -- Locale Settings
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    date_format VARCHAR(20) DEFAULT 'MM/DD/YYYY',
    
    -- Custom Theme Configuration (JSON)
    custom_theme_config JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(user_id)  -- One preference row per user
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_preferences_timestamp
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_timestamp();

-- Insert default preferences for existing users
INSERT INTO user_preferences (user_id)
SELECT id FROM users
WHERE id NOT IN (SELECT user_id FROM user_preferences)
ON CONFLICT (user_id) DO NOTHING;

COMMENT ON TABLE user_preferences IS 'Stores user-specific UI preferences, theme choices, and settings';
COMMENT ON COLUMN user_preferences.theme IS 'UI theme: light, dark, matrix, cyberpunk, nord, solarized';
COMMENT ON COLUMN user_preferences.custom_theme_config IS 'JSON configuration for custom themes (colors, animations, etc.)';
COMMENT ON COLUMN user_preferences.animation_enabled IS 'Enable/disable animated backgrounds (Matrix rain, etc.)';
