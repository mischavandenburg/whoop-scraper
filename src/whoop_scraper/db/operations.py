"""Database operations for Whoop data."""

import logging
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


def upsert_user_profile(
    conn: psycopg.Connection[tuple[object, ...]],
    data: dict[str, Any],
) -> None:
    """Upsert user profile data."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO whoop_user_profile (user_id, email, first_name, last_name, updated_at)
            VALUES (%(user_id)s, %(email)s, %(first_name)s, %(last_name)s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                email = EXCLUDED.email,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                updated_at = NOW()
            """,
            {
                "user_id": data.get("user_id", "unknown"),
                "email": data.get("email"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
            },
        )
    conn.commit()
    logger.info("Upserted user profile")


def upsert_body_measurement(
    conn: psycopg.Connection[tuple[object, ...]],
    data: dict[str, Any],
) -> None:
    """Upsert body measurement data."""
    with conn.cursor() as cur:
        # Delete old and insert new (simpler than upsert for this table)
        cur.execute("DELETE FROM whoop_body_measurement WHERE user_id = %(user_id)s", data)
        cur.execute(
            """
            INSERT INTO whoop_body_measurement
                (user_id, height_meter, weight_kilogram, max_heart_rate)
            VALUES (%(user_id)s, %(height_meter)s, %(weight_kilogram)s, %(max_heart_rate)s)
            """,
            {
                "user_id": data.get("user_id", "unknown"),
                "height_meter": data.get("height_meter"),
                "weight_kilogram": data.get("weight_kilogram"),
                "max_heart_rate": data.get("max_heart_rate"),
            },
        )
    conn.commit()
    logger.info("Upserted body measurement")


def upsert_cycles(
    conn: psycopg.Connection[tuple[object, ...]],
    records: list[dict[str, Any]],
) -> int:
    """Upsert cycle records.

    Returns:
        Number of records upserted
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        for record in records:
            score = record.get("score", {}) or {}
            cur.execute(
                """
                INSERT INTO whoop_cycle
                    (id, user_id, start_time, end_time, timezone_offset,
                     score_strain, score_kilojoule, score_average_heart_rate, score_max_heart_rate,
                     updated_at)
                VALUES (%(id)s, %(user_id)s, %(start)s, %(end)s, %(timezone_offset)s,
                        %(strain)s, %(kilojoule)s, %(average_heart_rate)s, %(max_heart_rate)s,
                        NOW())
                ON CONFLICT (id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    score_strain = EXCLUDED.score_strain,
                    score_kilojoule = EXCLUDED.score_kilojoule,
                    score_average_heart_rate = EXCLUDED.score_average_heart_rate,
                    score_max_heart_rate = EXCLUDED.score_max_heart_rate,
                    updated_at = NOW()
                """,
                {
                    "id": record.get("id"),
                    "user_id": record.get("user_id", "unknown"),
                    "start": record.get("start"),
                    "end": record.get("end"),
                    "timezone_offset": record.get("timezone_offset"),
                    "strain": score.get("strain"),
                    "kilojoule": score.get("kilojoule"),
                    "average_heart_rate": score.get("average_heart_rate"),
                    "max_heart_rate": score.get("max_heart_rate"),
                },
            )
    conn.commit()
    logger.info("Upserted %d cycle records", len(records))
    return len(records)


def upsert_recovery(
    conn: psycopg.Connection[tuple[object, ...]],
    records: list[dict[str, Any]],
) -> int:
    """Upsert recovery records.

    Returns:
        Number of records upserted
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        for record in records:
            score = record.get("score", {}) or {}
            cur.execute(
                """
                INSERT INTO whoop_recovery
                    (cycle_id, user_id, sleep_id,
                     score_recovery_score, score_resting_heart_rate, score_hrv_rmssd_milli,
                     score_spo2_percentage, score_skin_temp_celsius,
                     updated_at)
                VALUES (%(cycle_id)s, %(user_id)s, %(sleep_id)s,
                        %(recovery_score)s, %(resting_heart_rate)s, %(hrv_rmssd_milli)s,
                        %(spo2_percentage)s, %(skin_temp_celsius)s,
                        NOW())
                ON CONFLICT (cycle_id) DO UPDATE SET
                    sleep_id = EXCLUDED.sleep_id,
                    score_recovery_score = EXCLUDED.score_recovery_score,
                    score_resting_heart_rate = EXCLUDED.score_resting_heart_rate,
                    score_hrv_rmssd_milli = EXCLUDED.score_hrv_rmssd_milli,
                    score_spo2_percentage = EXCLUDED.score_spo2_percentage,
                    score_skin_temp_celsius = EXCLUDED.score_skin_temp_celsius,
                    updated_at = NOW()
                """,
                {
                    "cycle_id": record.get("cycle_id"),
                    "user_id": record.get("user_id", "unknown"),
                    "sleep_id": record.get("sleep_id"),
                    "recovery_score": score.get("recovery_score"),
                    "resting_heart_rate": score.get("resting_heart_rate"),
                    "hrv_rmssd_milli": score.get("hrv_rmssd_milli"),
                    "spo2_percentage": score.get("spo2_percentage"),
                    "skin_temp_celsius": score.get("skin_temp_celsius"),
                },
            )
    conn.commit()
    logger.info("Upserted %d recovery records", len(records))
    return len(records)


def upsert_sleep(
    conn: psycopg.Connection[tuple[object, ...]],
    records: list[dict[str, Any]],
) -> int:
    """Upsert sleep records.

    Returns:
        Number of records upserted
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        for record in records:
            score = record.get("score", {}) or {}
            stage_summary = score.get("stage_summary", {}) or {}
            sleep_needed = score.get("sleep_needed", {}) or {}
            cur.execute(
                """
                INSERT INTO whoop_sleep
                    (id, user_id, start_time, end_time, timezone_offset, nap,
                     score_stage_summary_total_in_bed_time_milli,
                     score_stage_summary_total_awake_time_milli,
                     score_stage_summary_total_no_data_time_milli,
                     score_stage_summary_total_light_sleep_time_milli,
                     score_stage_summary_total_slow_wave_sleep_time_milli,
                     score_stage_summary_total_rem_sleep_time_milli,
                     score_stage_summary_sleep_cycle_count,
                     score_stage_summary_disturbance_count,
                     score_sleep_needed_baseline_milli,
                     score_sleep_needed_need_from_sleep_debt_milli,
                     score_sleep_needed_need_from_recent_strain_milli,
                     score_sleep_needed_need_from_recent_nap_milli,
                     score_respiratory_rate,
                     score_sleep_performance_percentage,
                     score_sleep_consistency_percentage,
                     score_sleep_efficiency_percentage,
                     updated_at)
                VALUES (%(id)s, %(user_id)s, %(start)s, %(end)s, %(timezone_offset)s, %(nap)s,
                        %(total_in_bed_time_milli)s, %(total_awake_time_milli)s,
                        %(total_no_data_time_milli)s, %(total_light_sleep_time_milli)s,
                        %(total_slow_wave_sleep_time_milli)s, %(total_rem_sleep_time_milli)s,
                        %(sleep_cycle_count)s, %(disturbance_count)s,
                        %(baseline_milli)s, %(need_from_sleep_debt_milli)s,
                        %(need_from_recent_strain_milli)s, %(need_from_recent_nap_milli)s,
                        %(respiratory_rate)s, %(sleep_performance_percentage)s,
                        %(sleep_consistency_percentage)s, %(sleep_efficiency_percentage)s,
                        NOW())
                ON CONFLICT (id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    score_stage_summary_total_in_bed_time_milli =
                        EXCLUDED.score_stage_summary_total_in_bed_time_milli,
                    score_stage_summary_total_awake_time_milli =
                        EXCLUDED.score_stage_summary_total_awake_time_milli,
                    score_stage_summary_total_rem_sleep_time_milli =
                        EXCLUDED.score_stage_summary_total_rem_sleep_time_milli,
                    score_sleep_performance_percentage =
                        EXCLUDED.score_sleep_performance_percentage,
                    updated_at = NOW()
                """,
                {
                    "id": record.get("id"),
                    "user_id": record.get("user_id", "unknown"),
                    "start": record.get("start"),
                    "end": record.get("end"),
                    "timezone_offset": record.get("timezone_offset"),
                    "nap": record.get("nap", False),
                    "total_in_bed_time_milli": stage_summary.get("total_in_bed_time_milli"),
                    "total_awake_time_milli": stage_summary.get("total_awake_time_milli"),
                    "total_no_data_time_milli": stage_summary.get("total_no_data_time_milli"),
                    "total_light_sleep_time_milli": stage_summary.get(
                        "total_light_sleep_time_milli"
                    ),
                    "total_slow_wave_sleep_time_milli": stage_summary.get(
                        "total_slow_wave_sleep_time_milli"
                    ),
                    "total_rem_sleep_time_milli": stage_summary.get("total_rem_sleep_time_milli"),
                    "sleep_cycle_count": stage_summary.get("sleep_cycle_count"),
                    "disturbance_count": stage_summary.get("disturbance_count"),
                    "baseline_milli": sleep_needed.get("baseline_milli"),
                    "need_from_sleep_debt_milli": sleep_needed.get("need_from_sleep_debt_milli"),
                    "need_from_recent_strain_milli": sleep_needed.get(
                        "need_from_recent_strain_milli"
                    ),
                    "need_from_recent_nap_milli": sleep_needed.get("need_from_recent_nap_milli"),
                    "respiratory_rate": score.get("respiratory_rate"),
                    "sleep_performance_percentage": score.get("sleep_performance_percentage"),
                    "sleep_consistency_percentage": score.get("sleep_consistency_percentage"),
                    "sleep_efficiency_percentage": score.get("sleep_efficiency_percentage"),
                },
            )
    conn.commit()
    logger.info("Upserted %d sleep records", len(records))
    return len(records)


def upsert_workouts(
    conn: psycopg.Connection[tuple[object, ...]],
    records: list[dict[str, Any]],
) -> int:
    """Upsert workout records.

    Returns:
        Number of records upserted
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        for record in records:
            score = record.get("score", {}) or {}
            zone_duration = score.get("zone_duration", {}) or {}
            cur.execute(
                """
                INSERT INTO whoop_workout
                    (id, user_id, start_time, end_time, timezone_offset, sport_id,
                     score_strain, score_average_heart_rate, score_max_heart_rate,
                     score_kilojoule, score_percent_recorded, score_distance_meter,
                     score_altitude_gain_meter, score_altitude_change_meter,
                     score_zone_duration_zone_zero_milli, score_zone_duration_zone_one_milli,
                     score_zone_duration_zone_two_milli, score_zone_duration_zone_three_milli,
                     score_zone_duration_zone_four_milli, score_zone_duration_zone_five_milli,
                     updated_at)
                VALUES (%(id)s, %(user_id)s, %(start)s, %(end)s, %(timezone_offset)s, %(sport_id)s,
                        %(strain)s, %(average_heart_rate)s, %(max_heart_rate)s,
                        %(kilojoule)s, %(percent_recorded)s, %(distance_meter)s,
                        %(altitude_gain_meter)s, %(altitude_change_meter)s,
                        %(zone_zero_milli)s, %(zone_one_milli)s,
                        %(zone_two_milli)s, %(zone_three_milli)s,
                        %(zone_four_milli)s, %(zone_five_milli)s,
                        NOW())
                ON CONFLICT (id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    score_strain = EXCLUDED.score_strain,
                    score_kilojoule = EXCLUDED.score_kilojoule,
                    updated_at = NOW()
                """,
                {
                    "id": record.get("id"),
                    "user_id": record.get("user_id", "unknown"),
                    "start": record.get("start"),
                    "end": record.get("end"),
                    "timezone_offset": record.get("timezone_offset"),
                    "sport_id": record.get("sport_id"),
                    "strain": score.get("strain"),
                    "average_heart_rate": score.get("average_heart_rate"),
                    "max_heart_rate": score.get("max_heart_rate"),
                    "kilojoule": score.get("kilojoule"),
                    "percent_recorded": score.get("percent_recorded"),
                    "distance_meter": score.get("distance_meter"),
                    "altitude_gain_meter": score.get("altitude_gain_meter"),
                    "altitude_change_meter": score.get("altitude_change_meter"),
                    "zone_zero_milli": zone_duration.get("zone_zero_milli"),
                    "zone_one_milli": zone_duration.get("zone_one_milli"),
                    "zone_two_milli": zone_duration.get("zone_two_milli"),
                    "zone_three_milli": zone_duration.get("zone_three_milli"),
                    "zone_four_milli": zone_duration.get("zone_four_milli"),
                    "zone_five_milli": zone_duration.get("zone_five_milli"),
                },
            )
    conn.commit()
    logger.info("Upserted %d workout records", len(records))
    return len(records)
