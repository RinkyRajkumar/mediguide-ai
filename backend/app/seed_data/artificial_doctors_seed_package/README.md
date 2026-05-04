# Artificial Doctor Seed Data for AI Scheduling Agent

This package contains fully artificial sample data for a medical appointment scheduling system.

## Contents

- `doctors_seed_postgres.sql` - PostgreSQL schema + inserts
- `doctors_seed.csv` - 540 doctors
- `doctor_availability_seed.csv` - 2176 weekly availability records
- `departments_seed.csv` - 18 departments
- `clinics_seed.csv` - 10 clinics
- `doctors_seed.json` - same data in JSON format

## Dataset size

- Medical fields/departments: 18
- Doctors per field: 30
- Total doctors: 540
- Total availability templates: 2176

## Import

```bash
psql -d mediguide_ai -f doctors_seed_postgres.sql
```

## Note

All names, phone numbers, and details are artificial/randomly generated for student project/demo use.
