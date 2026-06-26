# Electronics Repair Department Simulation

Carlos Guerrero  
CS 4632 - Modeling and Simulation, Section W01  
Summer 2026

## Project Overview

This project is a discrete-event simulation of the electronics manufacturing support department where I work. The department repairs PCBs and HVAC and refrigeration controller units.

Work comes from customer RMAs, advance exchanges, reships, and production-line failures. The department has two technicians and two test stations. Customer RMAs are selected from a rack in FIFO order. Other work is brought directly to the technicians, and urgent production failures can interrupt a repair already in progress.

The main events are when a job arrives, a technician starts or finishes work, a repair is interrupted, and a job receives its final outcome. A job can be repaired, scrapped, or returned to the vendor.

The simulation will measure turnaround time, waiting time, queue length, technician and station use, throughput, interruptions, and repair outcomes. Historical work data will be used for the simulation inputs.

## Project Structure

- `M1/` - M1 proposal PDF, LaTeX source, bibliography, and diagrams
- `data/` - cleaned CSV files used as project input data
- `src/` - Python source code for the simulation

## Project Status

This project is currently at the M2 stage. The code can
read the cleaned project data, create repair jobs, separate open work from
closed work, check the FIFO RMA rack, and run a small SimPy test using
technician and station resources.

Implemented so far:

- cleaned CSV project data
- basic job, technician, and station classes
- source, priority, outcome, and capability rules
- job creation from the CSV data
- open RMA rack jobs separated from closed jobs
- FIFO selection for customer RMA rack work
- basic SimPy runner
- technician and station resource matching
- basic metrics for completed jobs

In-Progress:

- direct-request priority queue for AdvEx, production failures, and reships
- production interruption/preemption logic
- advance-exchange process details
- working-hours time handling
- larger simulation runs and scenario testing
- more complete output metrics and validation checks

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

To create early simulation job objects from the CSV data:

```cmd
python src\print_created_jobs.py
```

This creates `Job` objects for RMA unit jobs and production issue jobs, then
prints counts for open and historical work.

To check the basic FIFO RMA rack logic:

```cmd
python src\print_fifo_queue.py
```

This separates open customer RMA jobs from direct requests and prints the first
open jobs that would be selected from the RMA rack.

To run the first SimPy simulation test:

```cmd
python src\print_simpy_run.py
```

This uses SimPy time to run a few FIFO RMA jobs and prints basic simulation
metrics for completed jobs.

## Architecture Overview

- `models.py` has the main classes for jobs, technicians, stations, and scenario settings.
- `csv_parser.py` reads the CSV data.
- `input_analysis.py` prints early estimates from the closed RMA data.
- `job_rules.py` maps CSV values into simulation rules.
- `create_jobs.py` creates `Job` objects from the CSV rows.
- `queue.py` separates open RMA rack jobs from direct requests.
- `resources.py` creates SimPy technician and station resources.
- `simpy_runner.py` runs the SimPy test.
- `metrics.py` records basic completed-job results.

## UML Mapping

The M1 `class_diagram.png` shows the main planned program parts:
`RepairDepartment`, `Job`, `Repair`, `Results`, `Technician`, and `Station`.

- `Job` maps to the `Job` class in `models.py`.
- `Technician` maps to the `Technician` class in `models.py`.
- `Station` maps to the `Station` class in `models.py`.
- `RepairDepartment` is split across `queue.py`, `resources.py`, and
  `simpy_runner.py`.
- `Repair` is represented by the SimPy repair process in `simpy_runner.py`.
- `Results` maps to `metrics.py`.

The M1 `activity_diagram.png` shows the work flow. Customer RMAs go to the
rack, wait for an available technician and station, then get repaired and
recorded. The current M2 code covers that first path with the FIFO rack, SimPy
resource matching, and basic completed-job metrics.

The `activity_diagram.png` also shows the direct-request path for advance
exchanges, production failures, and reships. That path is started but the full priority and interruption behavior is still in-progress.

## Troubleshooting

- Run commands from the project folder. If Python says it cannot find a file,
  use the `cd PATH TO PROJECT` command from the setup section .
- If Python says `No module named simpy`, run:

```cmd
python -m pip install -r requirements.txt
```
