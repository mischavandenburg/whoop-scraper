"""Database schema for Whoop API data."""

import logging

import psycopg

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
-- Whoop OAuth tokens for stateless container deployments
CREATE TABLE IF NOT EXISTS whoop_oauth_tokens (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- Ensures single row
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    token_type VARCHAR(50) DEFAULT 'bearer',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profile
CREATE TABLE IF NOT EXISTS whoop_user_profile (
    user_id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Body measurements
CREATE TABLE IF NOT EXISTS whoop_body_measurement (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    height_meter DECIMAL(5, 3),
    weight_kilogram DECIMAL(6, 2),
    max_heart_rate INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Physiological cycles
CREATE TABLE IF NOT EXISTS whoop_cycle (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    timezone_offset VARCHAR(10),
    score_strain DECIMAL(5, 2),
    score_kilojoule DECIMAL(10, 2),
    score_average_heart_rate INTEGER,
    score_max_heart_rate INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whoop_cycle_start_time ON whoop_cycle(start_time);
CREATE INDEX IF NOT EXISTS idx_whoop_cycle_user_id ON whoop_cycle(user_id);

-- Recovery data
CREATE TABLE IF NOT EXISTS whoop_recovery (
    cycle_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    sleep_id VARCHAR(100),
    score_recovery_score INTEGER,
    score_resting_heart_rate INTEGER,
    score_hrv_rmssd_milli DECIMAL(8, 3),
    score_spo2_percentage DECIMAL(5, 2),
    score_skin_temp_celsius DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whoop_recovery_cycle_id ON whoop_recovery(cycle_id);

-- Sleep data
CREATE TABLE IF NOT EXISTS whoop_sleep (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    timezone_offset VARCHAR(10),
    nap BOOLEAN DEFAULT FALSE,
    score_stage_summary_total_in_bed_time_milli BIGINT,
    score_stage_summary_total_awake_time_milli BIGINT,
    score_stage_summary_total_no_data_time_milli BIGINT,
    score_stage_summary_total_light_sleep_time_milli BIGINT,
    score_stage_summary_total_slow_wave_sleep_time_milli BIGINT,
    score_stage_summary_total_rem_sleep_time_milli BIGINT,
    score_stage_summary_sleep_cycle_count INTEGER,
    score_stage_summary_disturbance_count INTEGER,
    score_sleep_needed_baseline_milli BIGINT,
    score_sleep_needed_need_from_sleep_debt_milli BIGINT,
    score_sleep_needed_need_from_recent_strain_milli BIGINT,
    score_sleep_needed_need_from_recent_nap_milli BIGINT,
    score_respiratory_rate DECIMAL(5, 2),
    score_sleep_performance_percentage DECIMAL(5, 2),
    score_sleep_consistency_percentage DECIMAL(5, 2),
    score_sleep_efficiency_percentage DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whoop_sleep_start_time ON whoop_sleep(start_time);
CREATE INDEX IF NOT EXISTS idx_whoop_sleep_user_id ON whoop_sleep(user_id);

-- Workout data
CREATE TABLE IF NOT EXISTS whoop_workout (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    timezone_offset VARCHAR(10),
    sport_id INTEGER,
    score_strain DECIMAL(5, 2),
    score_average_heart_rate INTEGER,
    score_max_heart_rate INTEGER,
    score_kilojoule DECIMAL(10, 2),
    score_percent_recorded DECIMAL(5, 2),
    score_distance_meter DECIMAL(12, 2),
    score_altitude_gain_meter DECIMAL(10, 2),
    score_altitude_change_meter DECIMAL(10, 2),
    score_zone_duration_zone_zero_milli BIGINT,
    score_zone_duration_zone_one_milli BIGINT,
    score_zone_duration_zone_two_milli BIGINT,
    score_zone_duration_zone_three_milli BIGINT,
    score_zone_duration_zone_four_milli BIGINT,
    score_zone_duration_zone_five_milli BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whoop_workout_start_time ON whoop_workout(start_time);
CREATE INDEX IF NOT EXISTS idx_whoop_workout_user_id ON whoop_workout(user_id);
"""


def get_schema_sql() -> str:
    """Return the schema SQL for manual inspection."""
    return SCHEMA_SQL


def init_schema(conn: psycopg.Connection[tuple[object, ...]]) -> None:
    """Initialize the database schema.

    Args:
        conn: Database connection
    """
    logger.info("Initializing database schema...")
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
    logger.info("Schema initialization complete")
