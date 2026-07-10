# Electronics Repair Department Simulation

Carlos Guerrero  
CS 4632 - Modeling and Simulation, Section W01  
Summer 2026

## Project Overview

This project is a discrete-event simulation of the electronics manufacturing support department where I work. The department repairs PCBs and HVAC and refrigeration controller units.

Work comes from customer RMAs, advance exchanges, reships, and production-line failures. The department has two technicians and two test stations. Urgent production failures, advance exchanges, and reships can interrupt a customer RMA repair already in progress. The department only works business hours (7:00 AM to 3:30 PM, Monday through Friday), so a job that arrives or is still being worked on outside those hours just waits or pauses until the next business day.

The main events are when a job arrives, a technician starts or finishes work, a repair is interrupted, and a job receives its final outcome. A job can be repaired, scrapped, returned to the vendor, or reshipped. The simulation measures turnaround time, waiting time, queue length, technician and station use, throughput, interruptions, and repair outcomes. Historical work data is used for the simulation inputs.

## Project Structure

- `M1/` - M1 proposal PDF, LaTeX source, bibliography, and diagrams
- `M2/` - M2 report PDF
- `M3/` - M3 report PDF
- `data/` - cleaned CSV files used as project input data
- `src/` - Python source code for the simulation
- `results/` - CSV output from simulation runs (created after you run the code)

## Project Status

The simulation is fully implemented and runs complete scenarios end to end, from live random job arrivals through repair, interruption, and completion, with results exported to CSV.

Implemented so far:

- cleaned CSV project data
- job, technician, and station classes, plus a scenario config class with validation
- source, priority, outcome, and capability rules
- historical data used to build random-arrival job models for Customer RMA, AdvEx, and reship
- production failures generated as random urgent jobs
- live random arrivals for all four job sources
- technician and station resource matching by capability
- two-tier preemption: production, AdvEx, and reship jobs can interrupt an in-progress Customer RMA repair, but never interrupt each other
- business hours (7 AM - 3:30 PM, Monday - Friday) for both job arrivals and repair work, with in-progress jobs pausing overnight/over the weekend and picking back up where they left off
- full metrics collection: wait time, turnaround time, queue length over time, technician/station utilization, throughput, interruption counts
- CSV export for events, summary stats, time queue snapshots, and scenario config
- a scenario runner that varies technician counts, station counts, preemption, and job volume across 10 runs, and records both simulated duration and real execution time per run to a master index file
- parameter prompt that ask if you want to set custom parameters and walk through them one at a time if you say yes
- a validation script with automated checks (FIFO order, priority order, config validation, no double-booking, wait/turnaround consistency, preemption behavior)

## Setup

1. Open Command Prompt.
2. Go to the folder where you cloned or downloaded the project:

```cmd
cd "PROJECT LOCATION"\CS4632-Electronics-Repair
```

3. Install the Python dependency:

```cmd
python -m pip install -r requirements.txt
```

4. Run one of the commands below from the project folder.

## How to Run Current Code

From the project folder:

```cmd
python src\print_csv_summary.py
```

This prints a summary of the CSV data, including row counts, priorities,
RMA types, outcomes, capabilities, production locations, and missing date checks.

To print early simulation input estimates:

```cmd
python src\print_input_estimates.py
```

This estimates basic arrival, service-time, outcome, capability, and priority
values from the CSV data.

To check how CSV values map into simulation rules:

```cmd
python src\print_job_rules.py
```

This shows priority, source, outcome, and queue-type mapping.

To print the random-arrival job models built from the CSV data:

```cmd
python src\print_created_jobs.py
```

This shows the interarrival time, capability split, service times, outcome
counts, and priority counts used to generate Customer RMA, AdvEx, reship, and
production jobs.

To check the FIFO rack and priority list logic from M2:

```cmd
python src\print_fifo_queue.py
```

To run a single simulation scenario:

```cmd
python src\print_simpy_run.py
```

This runs one full scenario with live random arrivals, business hours, and
preemption, then prints the simulation metrics for every completed job.

**This is the main script for the project - run this one to generate the full
set of results:**

```cmd
python src\run_all_scenarios.py
```

Runs 10 scenarios that vary technician counts, station counts, preemption,
and job volume, then prints a run summary table with simulated duration and
real execution time for each run. It also asks if you want to set custom
parameters for the scenarios before running.

To run the validation checks:

```cmd
python src\validate_simulation.py
```

## Architecture Overview

- `models.py` has the main classes for jobs, technicians, stations, and scenario settings, plus config validation and config CSV export.
- `csv_parser.py` reads the CSV data.
- `input_analysis.py` prints early estimates from the closed RMA data.
- `job_rules.py` maps CSV values into simulation rules.
- `create_jobs.py` builds the random-arrival job models from historical CSV data and generates new synthetic jobs (Customer RMA, AdvEx, reship, production) for a running simulation.
- `resources.py` creates SimPy technician and station resources.
- `cli_prompts.py` has the shared prompt (yes/no questions and parameter entry) used by `print_simpy_run.py` and `run_all_scenarios.py`.
- `simpy_runner.py` runs the live simulation: job arrival processes, the repair work loop with preemption and business-hours handling, and the queue-watching process.
- `metrics.py` records the event log and completed-job results, and exports the CSV result files.

## UML Mapping

The M1 `class_diagram.png` shows the main planned program parts:
`RepairDepartment`, `Job`, `Repair`, `Results`, `Technician`, and `Station`.

- `Job` maps to the `Job` class in `models.py`.
- `Technician` maps to the `Technician` class in `models.py`.
- `Station` maps to the `Station` class in `models.py`.
- `RepairDepartment` is split across `resources.py` and `simpy_runner.py`.
- `Repair` is represented by the `repair_job` SimPy process in `simpy_runner.py`.
- `Results` maps to `metrics.py`.

The M1 `activity_diagram.png` shows the work flow. Customer RMAs arrive, wait
for an available technician and station, then get repaired and recorded. The
direct-request path for advance exchanges, production failures, and reships
is also implemented, with priority-based preemption instead of a pre-sorted
queue - a production failure, AdvEx, or reship can now interrupt an
in-progress Customer RMA repair, matching the real department behavior.

## Troubleshooting

- Run commands from the project folder. If Python says it cannot find a file,
  use the `cd PATH TO PROJECT` command from the setup section .
- If Python says `No module named simpy`, run:

```cmd
python -m pip install -r requirements.txt
```

- If a results CSV file is open in Excel or another program, close it before
  running the simulation again
