-- =====================================================
-- CUSTOMER QUERIES – MEDIUM LEVEL
-- Ride-Hailing System (PostgreSQL)
-- =====================================================

-- =====================================================
-- CASE 1 – Customer Spending Between Two Dates
-- Function-based Query
-- =====================================================

CREATE OR REPLACE FUNCTION fn_customer_total_spending(
    p_user_id    BIGINT,
    p_start_date DATE,
    p_end_date   DATE
)
RETURNS NUMERIC
AS $$
DECLARE
    total NUMERIC;
BEGIN
    SELECT COALESCE(SUM(p.amount), 0)
    INTO total
    FROM trip_request tr
    JOIN trip t
      ON t.trip_request_id = tr.trip_request_id
    JOIN payment p
      ON p.trip_id = t.trip_id
    WHERE tr.user_id = p_user_id
      AND t.status   = 'completed'
      AND p.status   = 'completed'
      AND t.end_time >= p_start_date
      AND t.end_time <  p_end_date + INTERVAL '1 day';

    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Example usage
SELECT fn_customer_total_spending(12345, '2025-10-01', '2025-10-31');



-- =====================================================
-- CASE 2 – Customers Without Any Completed Trip
-- =====================================================

-- Naive Query (NOT IN)
SELECT c.user_id
FROM customer c
WHERE c.user_id NOT IN (
    SELECT tr.user_id
    FROM trip t
    JOIN trip_request tr
      ON t.trip_request_id = tr.trip_request_id
    WHERE t.status = 'completed'
);

-- Optimized Query (LEFT JOIN ... IS NULL)
SELECT c.user_id
FROM customer c
LEFT JOIN (
    SELECT DISTINCT tr.user_id
    FROM trip t
    JOIN trip_request tr
      ON t.trip_request_id = tr.trip_request_id
    WHERE t.status = 'completed'
) completed_users
ON c.user_id = completed_users.user_id
WHERE completed_users.user_id IS NULL;



-- =====================================================
-- CASE 3 – Customer Spending Summary
-- =====================================================

-- Naive Query
SELECT tr.user_id, SUM(p.amount) AS total_spent
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE p.status = 'completed'
GROUP BY tr.user_id;

-- Optimized Query
SELECT tr.user_id, SUM(p.amount) AS total_spent
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE p.status = 'completed'
GROUP BY tr.user_id
HAVING SUM(p.amount) > 0;

-- Supporting index (impact may be limited)
CREATE INDEX IF NOT EXISTS idx_payment_completed
ON payment (trip_id, amount)
WHERE status = 'completed';



-- =====================================================
-- CASE 4 – Top 20 Customers with Highest Failed Amount
-- =====================================================

-- Naive Query
SELECT au.user_id, au.name, au.email, au.phone,
       COUNT(*) AS failed_payment_count,
       SUM(p.amount) AS failed_amount
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
JOIN appuser au
  ON tr.user_id = au.user_id
WHERE p.status = 'failed'
GROUP BY au.user_id, au.name, au.email, au.phone
ORDER BY failed_amount DESC
LIMIT 20;

-- Optimized Query
SELECT 
    au.user_id,
    au.name,
    au.email,
    au.phone,
    COUNT(p.payment_id) AS failed_payment_count,
    ROUND(SUM(p.amount), 2) AS failed_amount,
    MAX(t.end_time) AS last_failure_date
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
JOIN appuser au
  ON tr.user_id = au.user_id
WHERE p.status = 'failed'
GROUP BY au.user_id, au.name, au.email, au.phone
HAVING SUM(p.amount) > 0
ORDER BY failed_amount DESC
LIMIT 20;

-- Supporting partial index
CREATE INDEX IF NOT EXISTS idx_payment_failed
ON payment(trip_id)
WHERE status = 'failed';



-- =====================================================
-- CASE 5 – Trips Completed but Missing Payment
-- =====================================================

-- Naive Query (NOT IN)
SELECT t.trip_id, t.end_time, t.fare
FROM trip t
WHERE t.status = 'completed'
  AND t.trip_id NOT IN (
      SELECT p.trip_id FROM payment p
  );

-- Optimized Query (LEFT JOIN)
SELECT t.trip_id, t.end_time, t.fare
FROM trip t
LEFT JOIN payment p
  ON p.trip_id = t.trip_id
WHERE t.status = 'completed'
  AND p.trip_id IS NULL;



-- =====================================================
-- CASE 6 – Customers Without Feedback
-- SPECIAL CASE: Naive is Faster in This Dataset
-- =====================================================

-- Naive Query (NOT IN)
SELECT DISTINCT tr.user_id
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE t.trip_id NOT IN (
    SELECT trip_id FROM feedback
);

-- Optimized Query (LEFT JOIN)
SELECT DISTINCT tr.user_id
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
LEFT JOIN feedback f
  ON t.trip_id = f.trip_id
WHERE f.trip_id IS NULL;



-- =====================================================
-- CASE 7 – Monthly Spending Statistics
-- =====================================================

-- Naive Query
SELECT 
    EXTRACT(MONTH FROM t.end_time) AS month,
    COUNT(*) AS total_trips,
    SUM(t.fare) AS total_spent
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE tr.user_id = 1500
  AND t.status = 'completed'
  AND EXTRACT(YEAR FROM t.end_time) = 2025
GROUP BY EXTRACT(MONTH FROM t.end_time)
ORDER BY month;

-- Optimized Query
SELECT 
    DATE_TRUNC('month', t.end_time) AS month,
    COUNT(*) AS total_trips,
    SUM(t.fare) AS total_spent,
    AVG(t.fare) AS avg_fare
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE tr.user_id = 1500
  AND t.status = 'completed'
  AND t.end_time >= '2025-01-01'
  AND t.end_time <  '2026-01-01'
GROUP BY DATE_TRUNC('month', t.end_time)
ORDER BY month;

-- Supporting partial index
CREATE INDEX IF NOT EXISTS idx_trip_completed_endtime
ON trip(end_time)
WHERE status = 'completed';



-- =====================================================
-- CASE 8 – Customers Active in Last N Days
-- =====================================================

-- Naive Query
SELECT DISTINCT tr.user_id
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE t.end_time >= NOW() - INTERVAL '30 days';

-- Optimized Query
SELECT DISTINCT tr.user_id
FROM trip t
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE t.status = 'completed'
  AND t.end_time >= CURRENT_DATE - 30;

-- Supporting partial index
CREATE INDEX IF NOT EXISTS idx_trip_recent_completed
ON trip(end_time)
WHERE status = 'completed';



-- =====================================================
-- CASE 9 – Customers Using Credit Card Frequently
-- =====================================================

-- Naive Query
SELECT tr.user_id, COUNT(*) AS credit_count
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE p.payment_method = 'credit'
GROUP BY tr.user_id;

-- Optimized Query
SELECT tr.user_id, COUNT(*) AS credit_count
FROM payment p
JOIN trip t
  ON p.trip_id = t.trip_id
JOIN trip_request tr
  ON t.trip_request_id = tr.trip_request_id
WHERE p.payment_method = 'credit'
  AND p.status = 'completed'
GROUP BY tr.user_id
HAVING COUNT(*) >= 2;

-- Supporting partial index
CREATE INDEX IF NOT EXISTS idx_payment_credit_completed
ON payment(trip_id)
WHERE payment_method = 'credit'
  AND status = 'completed';



-- =====================================================
-- CASE 10 – Ride Request Behavior by Hour
-- =====================================================

-- Naive Query
SELECT 
    EXTRACT(HOUR FROM tr.request_time) AS hour_of_day,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN tr.status = 'accepted' THEN 1 ELSE 0 END) AS accepted,
    SUM(CASE WHEN tr.status = 'rejected' THEN 1 ELSE 0 END) AS rejected
FROM trip_request tr
WHERE tr.user_id = 1500
GROUP BY EXTRACT(HOUR FROM tr.request_time)
ORDER BY hour_of_day;

-- Optimized Query (CTE-based)
WITH hourly_stats AS (
    SELECT 
        EXTRACT(HOUR FROM request_time) AS hour_of_day,
        status,
        COUNT(*) AS request_count
    FROM trip_request
    WHERE user_id = 1500
      AND request_time >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY EXTRACT(HOUR FROM request_time), status
)
SELECT 
    hour_of_day,
    SUM(request_count) AS total_requests,
    SUM(CASE WHEN status = 'accepted' THEN request_count ELSE 0 END) AS accepted,
    SUM(CASE WHEN status = 'rejected' THEN request_count ELSE 0 END) AS rejected,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'accepted' THEN request_count ELSE 0 END)
        / NULLIF(SUM(request_count), 0),
        2
    ) AS acceptance_rate
FROM hourly_stats
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Supporting composite index
CREATE INDEX IF NOT EXISTS idx_triprequest_user_time_status
ON trip_request(user_id, request_time DESC, status);
