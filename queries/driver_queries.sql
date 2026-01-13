-- =====================================================
-- Query 1: Driver Location Search (Naive Haversine Approach)
-- =====================================================
SELECT 
    d.user_id AS driver_id,
    u.name,
    (6371 * asin(
        cos(radians(53.229225)) 
        * cos(radians(d.latitude)) 
        * sin(radians(d.longitude) - radians(-2.179150)) 
        * sin(radians(d.longitude) - radians(-2.179150)) 
        + sin(radians(53.229225) - radians(d.latitude)) 
        * sin(radians(53.229225) - radians(d.latitude))
    )) AS distance_km
FROM driver d
JOIN vehicle v ON d.user_id = v.driver_id
JOIN appuser u ON u.user_id = d.user_id
WHERE d.work_status = 'available'
  AND v.status = 'active'
  AND d.latitude BETWEEN (53.229225 - 0.1) AND (53.229225 + 0.1)
  AND d.longitude BETWEEN (-2.179150 - 0.1) AND (-2.179150 + 0.1)
ORDER BY distance_km
LIMIT 5;


-- =====================================================
-- Query 2: Driver Location Search (Optimized with Earthdistance + GiST)
-- =====================================================
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;

CREATE INDEX IF NOT EXISTS idx_driver_location_gist
ON driver USING GIST (ll_to_earth(latitude, longitude));

SELECT 
    d.user_id AS driver_id,
    u.name,
    (ll_to_earth(d.latitude, d.longitude) 
        <-> ll_to_earth(53.229225, -2.179150)) / 1000.0 AS distance_km
FROM driver d
JOIN vehicle v ON v.driver_id = d.user_id
JOIN appuser u ON u.user_id = d.user_id
WHERE d.work_status = 'available'
  AND v.status = 'active'
  AND earth_box(
        ll_to_earth(53.229225, -2.179150), 50000
      ) @> ll_to_earth(d.latitude, d.longitude)
ORDER BY distance_km
LIMIT 5;


-- =====================================================
-- Query 3: Driver Performance Statistics (INNER JOIN + GROUP BY)
-- =====================================================
SELECT 
    u.user_id,
    u.name,
    COUNT(t.trip_id) AS completed_trips,
    AVG(f.rating) AS avg_rating
FROM appuser u
JOIN driver d ON u.user_id = d.user_id
JOIN trip t ON d.user_id = t.driver_id
JOIN feedback f ON t.trip_id = f.trip_id
WHERE t.status = 'completed'
  AND EXTRACT(MONTH FROM t.end_time) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM t.end_time) = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY u.user_id, u.name
HAVING AVG(f.rating) > 4.5
ORDER BY completed_trips DESC
LIMIT 10;


-- =====================================================
-- Query 4: Driver Performance Statistics (CTE Optimized)
-- =====================================================
WITH MonthlyPerformance AS (
    SELECT 
        t.driver_id,
        COUNT(t.trip_id) AS completed_trips,
        AVG(f.rating) AS avg_rating
    FROM trip t
    JOIN feedback f ON t.trip_id = f.trip_id
    WHERE t.status = 'completed'
      AND EXTRACT(MONTH FROM t.end_time) = EXTRACT(MONTH FROM CURRENT_DATE)
      AND EXTRACT(YEAR FROM t.end_time) = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY t.driver_id
    HAVING AVG(f.rating) > 4.5
)
SELECT 
    p.driver_id,
    u.name,
    p.completed_trips,
    p.avg_rating
FROM MonthlyPerformance p
JOIN appuser u ON p.driver_id = u.user_id
ORDER BY p.completed_trips DESC
LIMIT 10;


-- =====================================================
-- Query 5: Driver Performance Statistics (Subquery + Index)
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_trip_perf
ON trip (status, end_time, driver_id);

CREATE INDEX IF NOT EXISTS idx_feedback_rating
ON feedback (trip_id, rating);

SELECT 
    u.user_id,
    u.name,
    stats.completed_count,
    stats.avg_rating
FROM appuser u
JOIN (
    SELECT 
        t.driver_id,
        COUNT(*) AS completed_count,
        AVG(f.rating) AS avg_rating
    FROM trip t
    JOIN feedback f ON t.trip_id = f.trip_id
    WHERE t.status = 'completed'
      AND EXTRACT(MONTH FROM t.end_time) = EXTRACT(MONTH FROM CURRENT_DATE)
      AND EXTRACT(YEAR FROM t.end_time) = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY t.driver_id
) stats ON u.user_id = stats.driver_id
WHERE stats.avg_rating > 4.5
ORDER BY stats.completed_count DESC
LIMIT 10;


-- =====================================================
-- Query 6: Driver Rest Rule Checking (Trigger + Function)
-- =====================================================
CREATE OR REPLACE FUNCTION func_check_rest()
RETURNS TRIGGER AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_is_exceeded BOOLEAN;
BEGIN
    IF NEW.status = 'completed'
       AND (OLD.status IS NULL OR OLD.status != 'completed') THEN
        v_start_time := NEW.end_time - INTERVAL '3 hours';
        SELECT EXISTS (
            SELECT 1
            FROM trip
            WHERE driver_id = NEW.driver_id
              AND status = 'completed'
              AND end_time >= v_start_time
            OFFSET 10 LIMIT 1
        ) INTO v_is_exceeded;
        IF v_is_exceeded THEN
            UPDATE driver
            SET work_status = 'unavailable'
            WHERE user_id = NEW.driver_id
              AND work_status != 'unavailable';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_driver_rest
AFTER UPDATE OF status
ON trip
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION func_check_rest();


-- =====================================================
-- Query 7: Speed Fraud Detection (Trigger + Function)
-- =====================================================
CREATE OR REPLACE FUNCTION func_check_speed_fraud()
RETURNS TRIGGER AS $$
DECLARE
    v_distance_km DECIMAL;
    v_duration_hours DECIMAL;
    v_avg_speed DECIMAL;
    v_threshold_speed CONSTANT INT := 120;
BEGIN
    IF NEW.status = 'completed'
       AND (OLD.status IS NULL OR OLD.status != 'completed')
       AND NEW.start_time IS NOT NULL
       AND NEW.end_time IS NOT NULL THEN
        SELECT
            6371 * 2 * ASIN(
                SQRT(
                    POWER(SIN(RADIANS(tr.drop_latitude - tr.pickup_latitude) / 2), 2) +
                    COS(RADIANS(tr.pickup_latitude)) *
                    COS(RADIANS(tr.drop_latitude)) *
                    POWER(SIN(RADIANS(tr.drop_longitude - tr.pickup_longitude) / 2), 2)
                )
            )
        INTO v_distance_km
        FROM trip_request tr
        WHERE tr.trip_request_id = NEW.trip_request_id;
        v_duration_hours := EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) / 3600;
        IF v_duration_hours > 0 AND v_distance_km IS NOT NULL THEN
            v_avg_speed := v_distance_km / v_duration_hours;
            IF v_avg_speed > v_threshold_speed THEN
                INSERT INTO fraud_logs (
                    driver_id, trip_id, reason, details, created_at
                ) VALUES (
                    NEW.driver_id,
                    NEW.trip_id,
                    'Abnormal speed',
                    'Speed=' || ROUND(v_avg_speed,2) || ' km/h, Distance=' || ROUND(v_distance_km,2) || ' km',
                    NOW()
                );
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_speed_fraud_check
AFTER UPDATE OF status
ON trip
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION func_check_speed_fraud();


-- =====================================================
-- Query 8: Periodic Vehicle Maintenance Check
-- =====================================================
SELECT v.vehicle_id, v.license_plate
FROM vehicle v
WHERE v.status = 'active'
  AND EXISTS (
      SELECT 1
      FROM trip t
      JOIN trip_request tr ON t.trip_request_id = tr.trip_request_id
      WHERE t.vehicle_id = v.vehicle_id
      GROUP BY t.vehicle_id
      HAVING SUM(tr.distance) > 5000
  );


-- =====================================================
-- Query 9: Average Fare Range Analysis
-- =====================================================
SELECT trip_id, fare, end_time
FROM trip
WHERE status = 'completed'
  AND fare BETWEEN 5 AND 10;


-- =====================================================
-- Query 10: High-Performance Driver Identification (No Low Ratings)
-- =====================================================
SELECT d.user_id, u.name
FROM driver d
JOIN appuser u ON d.user_id = u.user_id
LEFT JOIN trip t ON d.user_id = t.driver_id
LEFT JOIN feedback f 
       ON t.trip_id = f.trip_id AND f.rating <= 2
WHERE u.status = 'active'
  AND f.feedback_id IS NULL;