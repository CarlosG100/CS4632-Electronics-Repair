# Electronics Repair Department Simulation

Carlos Guerrero  
CS 4632 - Modeling and Simulation, Section W01  
Summer 2026

## Project Description

This project is a discrete-event simulation of the electronics manufacturing
support department where I work. The department repairs PCBs and HVAC and
refrigeration controller units.

Work comes from customer RMAs, advance exchanges, reships, and production-line
failures. The department has two technicians and two test stations. Customer
RMAs are selected from a rack in FIFO order. Other work is brought directly to
the technicians, and urgent production failures can interrupt a repair already
in progress.

The main events are when a job arrives, a technician starts or finishes work,
a repair is interrupted, and a job receives its final outcome. A job can be
repaired, scrapped, or returned to the vendor.

The simulation will measure turnaround time, waiting time, queue length,
technician and station use, throughput, interruptions, and repair outcomes.
Historical work data will be used for the simulation inputs.

## Files

- `main.tex` - M1 project report
- `preamble.tex` - formatting from the provided LaTeX template
- `references.bib` - sources cited in the report
- `class_diagram.png` - class diagram used in the report
- `activity_diagram.png` - activity diagram used in the report
