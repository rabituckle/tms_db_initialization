-- 5.4 enterprise queries

-- 5.4.1 insert new male appuser (user_id=1000001, role='driver', join_date=current_date, status='active')
insert into appuser (user_id, name, phone, email, gender, role, join_date, status)
values (1000001, 'Nguyen Van A', '0987654321', 'nguyenvana@example.com', 1, 'driver', current_date, 'active');

-- 5.4.2 top 10 drivers by total revenue from completed trips (min 5 completed trips)
create index idx_trip_completed_driverid on trip (driver_id) where status = 'completed';
create index idx_feedback_tripid on feedback (trip_id);
with driver_have5_completedtrip as (
  select t.driver_id, count(*) as completed_trips, sum(t.fare) as total_revenue
  from trip t
  where t.status = 'completed'
  group by t.driver_id
  having count(*) >= 5
),
avgfeedback_on_trip as (
  select f.trip_id, avg(f.rating) as avg_trip_rating
  from feedback f
  group by f.trip_id
),
avgfeedback_on_driver as (
  select t.driver_id, avg(fbt.avg_trip_rating) as avg_rating
  from trip t
  join avgfeedback_on_trip fbt on fbt.trip_id = t.trip_id
  where t.status = 'completed'
  group by t.driver_id
)
select d.user_id, au.name as driver_name, ta.completed_trips, ta.total_revenue, ra.avg_rating
from driver_have5_completedtrip ta
join driver d on d.user_id = ta.driver_id
join appuser au on au.user_id = d.user_id
left join avgfeedback_on_driver ra on ra.driver_id = ta.driver_id
order by ta.total_revenue desc
limit 10;

-- 5.4.3 list stale available drivers (last_update < now() - 10 minutes)
create index on trip (driver_id) where status in ('assigned','in_progress');
create index idx_driver_available_last_update on driver (last_update) where work_status = 'available';
with stale_drivers as (
  select d.user_id, u.name, d.work_status, d.last_update, d.latitude, d.longitude
  from driver d
  join appuser u on u.user_id = d.user_id
  where d.work_status = 'available' and d.last_update < now() - interval '10 minutes'
),
active_trip_counts as (
  select t.driver_id, count(*) as active_trips
  from trip t
  where t.status in ('assigned','in_progress')
  group by t.driver_id
)
select sd.user_id as driver_id, sd.name as driver_name, sd.work_status, sd.last_update, sd.latitude, sd.longitude,
coalesce(atc.active_trips, 0) as active_trips
from stale_drivers sd
left join active_trip_counts atc on atc.driver_id = sd.user_id
order by sd.last_update asc;

-- 5.4.4 suspend drivers with >= 5 canceled trips in last 30 days
create index idx_trip_canceled_driver_trid on trip (driver_id, trip_request_id) where status = 'canceled';
create index idx_trip_request_request_time_trid on trip_request (request_time, trip_request_id);
with canceled_30d as (
  select t.driver_id
  from trip t
  join trip_request tr on tr.trip_request_id = t.trip_request_id
  where t.status = 'canceled' and tr.request_time >= now() - interval '30 days'
  group by t.driver_id having count(*) >= 5
)
update appuser au
set status = 'suspended'
from canceled_30d c
where au.user_id = c.driver_id and au.role = 'driver' and au.status <> 'suspended';

-- 5.4.5 delete vehicle_id=2001 if in maintenance, no driver, no trip
delete from vehicle v
where v.vehicle_id = 2001 and v.status = 'maintenance' and v.driver_id is null
and not exists (select 1 from trip t where t.vehicle_id = v.vehicle_id);

-- 5.4.6 per-vehicle stats
create index idx_trip_vehicle_id on trip (vehicle_id);
create index idx_trip_vehicle_completed on trip (vehicle_id) where status = 'completed';
create index idx_trip_vehicle_end_time on trip (vehicle_id, end_time desc);
with trip_by_vehicle as (
  select t.vehicle_id, count(*) as total_trips_all_statuses,
  sum(t.fare) filter (where t.status = 'completed') as completed_trip_revenue,
  max(t.end_time) as latest_trip_end_time
  from trip t group by t.vehicle_id
)
select v.vehicle_id, v.license_plate,
coalesce(tb.total_trips_all_statuses, 0) as total_trips_all_statuses,
coalesce(tb.completed_trip_revenue, 0) as completed_trip_revenue,
tb.latest_trip_end_time
from vehicle v
left join trip_by_vehicle tb on tb.vehicle_id = v.vehicle_id
order by completed_trip_revenue desc;

-- 5.4.7 create view v_vehicle_rating_30d
create index idx_trip_vehicle_completed_end_time on trip (vehicle_id, end_time desc) where status = 'completed';
create index if not exists idx_feedback_trip_id on feedback (trip_id);
create or replace view v_vehicle_rating_30d as
with completed_30d as (
  select t.trip_id, t.vehicle_id
  from trip t
  where t.status = 'completed' and date(t.end_time) >= current_date - interval '30 days'
),
agg as (
  select c.vehicle_id, count(*) as completed_trips_30d, avg(f.rating) as avg_rating_30d
  from completed_30d c left join feedback f on f.trip_id = c.trip_id
  group by c.vehicle_id
)
select v.vehicle_id, v.license_plate, coalesce(a.completed_trips_30d, 0) as completed_trips_30d, a.avg_rating_30d
from vehicle v left join agg a on a.vehicle_id = v.vehicle_id;

-- 5.4.8 trigger for auto-maintenance
create index idx_trip_vehicle_completed_end_time on trip (vehicle_id, end_time desc) where status = 'completed';
create index idx_feedback_trip_id on feedback (trip_id);
create or replace function tg_vehicle_maintenance() returns trigger as $$
declare v_vehicle_id bigint; v_completed_cnt int; v_avg_rating numeric;
begin
  select t.vehicle_id into v_vehicle_id from trip t where t.trip_id = new.trip_id;
  select count(*) as completed_cnt, avg(f.rating) as avg_rating into v_completed_cnt, v_avg_rating
  from trip t left join feedback f on f.trip_id = t.trip_id
  where t.vehicle_id = v_vehicle_id and t.status = 'completed' and t.end_time >= now() - interval '30 days';
  if v_completed_cnt >= 3 and v_avg_rating <= 2.5 then
    update vehicle set status = 'maintenance' where vehicle_id = v_vehicle_id and status <> 'maintenance';
  end if; return new;
end; $$ language plpgsql;
create or replace trigger trg_vehicle_maintenance after insert or update of rating on feedback for each row execute function tg_vehicle_maintenance();

-- 5.4.9 daily finance report (last 30 days)
create index idx_trip_completed_end_time on trip (end_time) where status = 'completed';
create index idx_payment_completed_trip_id on payment (trip_id) where status = 'completed';
with daily as (
  select date(t.end_time) as day, count(*) as completed_trips, sum(t.fare) as gross_revenue,
  coalesce(sum(p.amount) filter (where p.status = 'completed'), 0) as collected_revenue,
  count(*) filter (where p.trip_id is null) as missing_payment_cnt,
  count(*) filter (where p.status = 'completed' and p.amount <> t.fare) as mismatch_cnt
  from trip t left join payment p on p.trip_id = t.trip_id
  where t.status = 'completed' and t.end_time >= current_date - interval '30 days'
  and t.end_time < current_date + interval '1 day' group by day
),
collected_7d as (
  select d1.day, coalesce(sum(d2.collected_revenue), 0) as collected_7d_sum
  from daily d1 left join daily d2 on d2.day between d1.day - 6 and d1.day group by d1.day
)
select d.day, d.completed_trips, d.gross_revenue, d.collected_revenue, d.missing_payment_cnt, d.mismatch_cnt, c.collected_7d_sum
from daily d join collected_7d c on c.day = d.day order by d.day asc;

-- 5.4.10 function fn_driver_earning(driver_id, day1, day2)
create index idx_trip_driver_completed_end_time on trip (driver_id, end_time) where status = 'completed';
create index idx_payment_trip_completed on payment (trip_id) where status = 'completed';
create or replace function fn_driver_earning(p_driver_id bigint, p_day1 date, p_day2 date) returns numeric as $$
declare res numeric;
begin
  select coalesce(sum(t.fare), 0) into res
  from trip t join payment p on p.trip_id = t.trip_id
  where t.driver_id = p_driver_id and t.status = 'completed'
  and date(t.end_time) >= p_day1 and date(t.end_time) < p_day2 + 1 and p.status = 'completed';
  return res;
end; $$ language plpgsql;
