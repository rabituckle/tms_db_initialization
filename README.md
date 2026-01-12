# TMS Data Generator (Rabituckle)

A Python-based tool designed to generate realistic, high-fidelity synthetic data for a Transportation Management System (TMS). It produces SQL INSERT statements while maintaining complex business logic and referential integrity.

## 📂 Project Structure

- **generators/**: Core logic scripts for each database table.  
- **output/**: Stores individual generated SQL files.  
- **test/**: pytest suite to validate data consistency and ratios.  
- **create_tms.sql**: Database schema definition.  
- **data_tms.sql**: Final merged SQL file for production/testing.  
- **merge.py**: Integration script to bundle all SQL files into a single transaction.  

## 🛠 Methodology

- **Generation**: Uses Faker and `random.choices` to simulate real-world distributions.  
- **Dependency Management**: Data is generated in a strict relational order  
  (e.g., `Users → Customers → Trips`).  
- **Validation**: Automated testing via pytest ensures foreign key integrity and statistical accuracy.  
- **Integration**: All statements are merged into `data_tms.sql` and wrapped in a transaction for safe, atomic import.  

## 📊 Business Rules & Constraints

| Table         | Main Constraints                                   | Distribution / Ratios                          |
|---------------|----------------------------------------------------|-----------------------------------------------|
| appuser       | Unique IDs; Role ∈ {customer, driver}              | 80% Customer, 20% Driver; 88% Active           |
| customer      | Linked to appuser (role: customer)                 | 70% have 0 penalties                           |
| driver        | Active users; 1 vehicle per driver                 | 80% available, 20% unavailable                 |
| vehicle       | One per driver; Type-specific status               | 70% Motorbike, 30% Car                         |
| trip_request  | request_time ≥ join_date                           | 5% inactive users; 1% power users              |
| trip          | Linked to requests; start ≤ end                    | Fare: Car > Motorbike                          |
| payment       | Only for completed trips; amount = fare            | 50% Cash, 40% Wallet, 10% Credit               |
| feedback      | Completed/Canceled trips only                      | Ratings vary based on trip outcome             |

## 🚀 Quick Start

### Install dependencies

```bash
pip install faker pytest
