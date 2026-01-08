-- =========================
-- USER
-- =========================
CREATE TABLE appuser (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    gender INT CHECK (gender IN (0, 1)),
    role VARCHAR(10) NOT NULL CHECK (role IN ('customer','driver')),
    join_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('active','inactive','suspended'))
);

-- =========================
-- CUSTOMER
-- =========================
CREATE TABLE customer (
    user_id BIGINT PRIMARY KEY REFERENCES appuser(user_id),
    penalty_count INT DEFAULT 0 CHECK (penalty_count >= 0)
);

-- =========================
-- DRIVER
-- =========================
CREATE TABLE driver (
    user_id BIGINT PRIMARY KEY REFERENCES appuser(user_id),
    work_status VARCHAR(15) NOT NULL
        CHECK (work_status IN ('available','unavailable')),
    longitude DECIMAL(9,6) NOT NULL,
    latitude DECIMAL(8,6) NOT NULL,
    last_update TIMESTAMP NOT NULL
);

-- =========================
-- VEHICLE
-- =========================
CREATE TABLE vehicle (
    vehicle_id BIGINT PRIMARY KEY,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(10) NOT NULL
        CHECK (type IN ('car','motorbike')),
    status VARCHAR(15) NOT NULL
        CHECK (status IN ('active','maintenance')),
    driver_id BIGINT REFERENCES driver(user_id)
);

-- =========================
-- TRIP REQUEST
-- =========================
CREATE TABLE trip_request (
    trip_request_id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES customer(user_id),
    pickup_location TEXT NOT NULL,
    drop_location TEXT NOT NULL,
    pickup_latitude DECIMAL(8,6) NOT NULL,
    pickup_longitude DECIMAL(9,6) NOT NULL,
    drop_latitude DECIMAL(8,6) NOT NULL,
    drop_longitude DECIMAL(9,6) NOT NULL,
    status VARCHAR(10) NOT NULL
        CHECK (status IN ('requested','rejected','accepted')),
    request_time TIMESTAMP NOT NULL
);

-- =========================
-- TRIP
-- =========================
CREATE TABLE trip (
    trip_id BIGINT PRIMARY KEY,
    trip_request_id BIGINT UNIQUE REFERENCES trip_request(trip_request_id),
    driver_id BIGINT REFERENCES driver(user_id),
    vehicle_id BIGINT REFERENCES vehicle(vehicle_id),
    status VARCHAR(15) NOT NULL
        CHECK (status IN ('assigned','in_progress','completed','canceled')),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    fare DECIMAL(10,2) NOT NULL CHECK (fare >= 0)
);

-- =========================
-- PAYMENT
-- =========================
CREATE TABLE payment (
    payment_id BIGINT PRIMARY KEY,
    trip_id BIGINT UNIQUE REFERENCES trip(trip_id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    payment_method VARCHAR(10) NOT NULL
        CHECK (payment_method IN ('cash','wallet','credit')),
    status VARCHAR(10) NOT NULL
        CHECK (status IN ('completed','failed'))
);

-- =========================
-- FEEDBACK
-- =========================
CREATE TABLE feedback (
    feedback_id BIGINT PRIMARY KEY,
    trip_id BIGINT UNIQUE REFERENCES trip(trip_id),
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment VARCHAR(512)
);
