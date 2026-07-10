import csv
import os


# Job sources from my project scope.
SOURCE_RMA = "Customer RMA"
SOURCE_ADVEX = "Advance Exchange"
SOURCE_RESHIP = "Reship"
SOURCE_PRODUCTION = "Production Failure"


# Priority values. Lower number means higher priority.
PRIORITY_ASAP = 1
PRIORITY_CRITICAL = 2
PRIORITY_HIGH = 3
PRIORITY_NORMAL = 4


# Capability values for resource matching.
CAPABILITY_GENERAL = "general"
CAPABILITY_SPECIALTY = "specialty"


# Possible outcomes for jobs.
OUTCOME_REPAIRED = "repaired"
OUTCOME_SCRAP = "scrap"
OUTCOME_RTV = "rtv"
OUTCOME_RESHIPPED = "reshipped"


# S&OP values that require specialty equipment.
SPECIALTY_SOP_PREFIXES = [
    "TSTAT",
    "DIMMER",
    "VFR",
    "RLDS",
    "ACC",
    "CC200",
    "XC",
    "XEV",
    "XR",
    "IPRO",
    "MRLDS",
    "CRLDS",
    "CC100",
    "XM",
]


class Job:
    # A job is the unit or request moving through the department.
    def __init__(self, job_id, source, priority, arrival_time, service_time, capability):
        self.job_id = job_id
        self.source = source
        self.priority = priority
        self.arrival_time = arrival_time
        self.service_time = service_time
        self.capability = capability

        self.outcome = None
        self.board_status = ""
        self.sim_arrival_time = None
        self.start_time = None
        self.finish_time = None
        self.remaining_time = service_time
        self.interrupted_count = 0


class Technician:
    # A technician is one of the limited workers in the department.
    def __init__(self, tech_id, capability):
        self.tech_id = tech_id
        self.capability = capability
        self.current_job_id = None
        self.busy_time = 0.0

    def can_work(self, job):
        # General jobs can be worked by anyone.
        # Specialty jobs need a specialty-capable technician.
        if job.capability == CAPABILITY_GENERAL:
            return True
        return self.capability == CAPABILITY_SPECIALTY


class Station:
    # A station is the station needed for a job.
    def __init__(self, station_id, capability):
        self.station_id = station_id
        self.capability = capability
        self.current_job_id = None
        self.busy_time = 0.0

    def can_handle(self, job):
        # General jobs can use any station.
        # Specialty jobs need a specialty-capable station.
        if job.capability == CAPABILITY_GENERAL:
            return True
        return self.capability == CAPABILITY_SPECIALTY


class ScenarioConfig:
    # Settings for sim run
    def __init__(self):
        self.name = "baseline"

        # My starting system has 1 general and 1 specialty technician (2 total).
        self.general_technicians = 1
        self.specialty_technicians = 1

        # My starting system has 1 general and 1 specialty station (2 total).
        self.general_stations = 1
        self.specialty_stations = 1

        # how many new/simulated Customer RMA jobs to generate this run
        self.job_limit = 3

        # how many new/simulated AdvEx jobs to generate this run
        self.advex_job_count = 3

        # how many new/simulated reship jobs to generate this run
        self.reship_job_count = 3

        # how many new/simulated production failures to generate this run
        self.production_job_count = 3

        # used to seed python's random module so results can be reproduced
        self.random_seed = 42

        # how many simulated hours to wait between each queue check
        self.snapshot_gap_hours = 5

        # stop taking queue checks after this many, so the sim always ends
        self.snapshot_limit = 200

        # Production failures can interrupt lower-priority work.
        self.allow_preemption = True


def validate_config(config):
    if config.general_technicians < 0:
        raise ValueError("general_technicians cannot be negative")
    if config.specialty_technicians < 0:
        raise ValueError("specialty_technicians cannot be negative")
    if config.general_stations < 0:
        raise ValueError("general_stations cannot be negative")
    if config.specialty_stations < 0:
        raise ValueError("specialty_stations cannot be negative")
    if config.job_limit < 0:
        raise ValueError("job_limit cannot be negative")
    if config.advex_job_count < 0:
        raise ValueError("advex_job_count cannot be negative")
    if config.reship_job_count < 0:
        raise ValueError("reship_job_count cannot be negative")
    if config.production_job_count < 0:
        raise ValueError("production_job_count cannot be negative")
    if config.snapshot_gap_hours < 0:
        raise ValueError("snapshot_gap_hours cannot be negative")
    if config.snapshot_limit < 0:
        raise ValueError("snapshot_limit cannot be negative")

    if config.general_technicians + config.specialty_technicians == 0:
        raise ValueError("You need at least one technician.")
    if config.general_stations + config.specialty_stations == 0:
        raise ValueError("You need at least one station.")


def export_config_csv(config, file_path, generated_at):
    new_row = {
        "scenario": config.name,
        "generated_at": generated_at,
        "general_technicians": config.general_technicians,
        "specialty_technicians": config.specialty_technicians,
        "general_stations": config.general_stations,
        "specialty_stations": config.specialty_stations,
        "job_limit": config.job_limit,
        "advex_job_count": config.advex_job_count,
        "reship_job_count": config.reship_job_count,
        "production_job_count": config.production_job_count,
        "random_seed": config.random_seed,
        "snapshot_gap_hours": config.snapshot_gap_hours,
        "snapshot_limit": config.snapshot_limit,
        "allow_preemption": config.allow_preemption,
    }

    existing_rows = []
    if os.path.exists(file_path):
        with open(file_path, newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            existing_rows = list(reader)

    existing_rows.append(new_row)
    field_names = list(new_row.keys())

    with open(file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names, restval="")
        writer.writeheader()

        for row in existing_rows:
            writer.writerow(row)


def capability_from_sop(sop_value):
    if sop_value is None:
        return CAPABILITY_GENERAL

    cleaned = str(sop_value).strip().upper()

    for prefix in SPECIALTY_SOP_PREFIXES:
        if cleaned.startswith(prefix):
            return CAPABILITY_SPECIALTY

    return CAPABILITY_GENERAL
