# Electronics Repair Department Simulation

Carlos Guerrero  
CS 4632 - Modeling and Simulation, Section W01  
Summer 2026

## Project Overview

This project is a discrete-event simulation of the electronics manufacturing support department where I work. The department repairs PCBs and HVAC and refrigeration controller units.

Work comes from customer RMAs, advance exchanges, reships, and production-line failures. The department has technicians and stations split into general and specialty capability. Specialty technicians and stations can also do general work, and will pick up a general job if every general technician/station is busy - but only a specialty technician or station can do specialty work, and a general job borrowing specialty capacity can't be bumped by an incoming specialty job on that borrowed resource. Urgent production failures, advance exchanges, and reships can interrupt a customer RMA repair already in progress. The department only works business hours (7:00 AM to 3:30 PM, Monday through Friday), so a job that arrives or is still being worked on outside those hours just waits or pauses until the next business day.

The main events are when a job arrives, a technician starts or finishes work, a repair is interrupted, and a job receives its final outcome. A job can be repaired, scrapped, returned to the vendor, or reshipped. The simulation measures turnaround time, waiting time, queue length, technician and station use, throughput, interruptions, and repair outcomes. Historical work data is used for the simulation inputs, and job volume per source is figured out from a chosen simulation period (in hours) using each source's real historical arrival rate, instead of a hard-coded job count.

## Project Structure

- `M1/` - M1 proposal PDF, LaTeX source, bibliography, and diagrams
- `M2/` - M2 report PDF
- `M3/` - M3 report PDF
- `M4/` - M4 report PDF
- `M5/` - M5 final report LaTex
- `data/` - cleaned CSV files used as project input data
- `src/` - Python source code for the simulation
- `results/` - CSV output from simulation runs

## Project Status

The project is complete through M5.

Implemented so far:

- cleaned CSV project data
- job, technician, and station classes, plus a scenario config class with validation
- source, priority, outcome, and capability rules
- historical data used to build random-arrival job models for Customer RMA, AdvEx, and reship
- production failures generated as random urgent jobs
- live random arrivals for all four job sources
- job counts per source figured out automatically from a chosen simulation period (in hours) and each source's real historical arrival rate.
- general jobs prefer general technicians/stations, but will use an idle specialty technician/station if every general one is busy; specialty jobs only ever use specialty technicians/stations
- a general job borrowing specialty capacity can't be preempted by an incoming specialty job on that borrowed resource.
- production, AdvEx, and reship jobs can interrupt an in-progress Customer RMA repair, but never interrupt each other
- business hours (7 AM - 3:30 PM, Monday - Friday) for both job arrivals and repair work, with in-progress jobs pausing overnight/over the weekend and picking back up where they left off
- full metrics: wait time, turnaround time, queue length over time, technician/station utilization, throughput, interruption counts
- CSV export for events, summary stats, time queue snapshots, and scenario config
- a scenario runner that varies technician counts, station counts, preemption, and job volume across 10 runs, and records both simulated duration and real execution time per run to a master index file
- a parameter update that changes one parameter at a time against a baseline and reports sensitivity
- a replication that reruns the same scenario many times with different random seeds and reports mean, standard deviation, min, max, and a 95% confidence interval per metricb

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
and job volume, then prints a run summary table with simulated duration.

To test how one parameter at a time affects the results:

```cmd
python src\parameterUpdate.py
```

Runs a baseline first, then lets you pick how many additional runs to do -
each one changes a single parameter to a new value and compares it back to
that same baseline, including a sensitivity score.

To see how much results vary from randomness alone:

```cmd
python src\replicate.py
```

Reruns the same scenario 100 times with different random seeds and reports
mean, standard deviation, min, max, and a 95% confidence interval for wait
time, turnaround time, and throughput.

To run the validation checks:

```cmd
python src\validate_simulation.py
```

This runs 7 automated checks against the simulation, including FIFO order,
priority order, config validation, no technician double-booking, wait/turnaround
consistency, and preemption behavior.

## Architecture Overview

- `models.py` has the main classes for jobs, technicians, stations, and scenario settings, plus config validation, config CSV export, and the shared day/time and project-folder helpers.
- `csv_parser.py` reads the CSV data.
- `input_analysis.py` prints early estimates from the closed RMA data.
- `job_rules.py` maps CSV values into simulation rules.
- `create_jobs.py` builds the random-arrival job models from historical CSV data, generates new synthetic jobs (Customer RMA, AdvEx, reship, production) for a running simulation, and figures out job counts per source from the simulation period.
- `resources.py` creates SimPy technician and station resources.
- `cli_prompts.py` has the prompts used across the runs.
- `analysis.py` has helpers for runs that run many scenarios in a row 
- `simpy_runner.py` runs the live simulation: job arrival processes, resource selection, the repair work loop with preemption and business-hours handling, and the queue-watching process.
- `metrics.py` records the event log and completed-job results, and exports the CSV result files.

## UML Mapping

M1's original diagrams planned a `RepairDepartment` class with a `Repair` class
managing an RMA rack. M5 has updated diagrams that match the real code. The M1 diagrams are still in `M1/` for reference,
but the M5 ones are the accurate picture of the current architecture.

- `Job`, `Technician`, `Station`, and `ScenarioConfig` are the data classes in
  `models.py`.
- `SimulationMetrics` in `metrics.py` records the event log, completed jobs,
  and queue snapshots.
- `create_jobs.py` builds the historical job models and generates new jobs
  during a run.
- `csv_parser.py`, `input_analysis.py`, and `job_rules.py` feed historical
  data into `create_jobs.py`.
- `resources.py` builds the technician and station lists.
- `simpy_runner.py` is where the actual control logic lives. Its functions work directly
  with four SimPy `PreemptiveResource` pools (general/specialty technicians,
  general/specialty stations).

`M5/activity_diagram.png` shows a job moving through arrival, technician
selection, station selection, service, and possible interruption, including
the general/specialty borrowing rule and the queueing that happens if even
the borrowed resource is busy.

## Troubleshooting

- Run commands from the project folder. If Python says it cannot find a file,
  use the `cd PATH TO PROJECT` command from the setup section .
- If Python says `No module named simpy`, run:

```cmd
python -m pip install -r requirements.txt
```