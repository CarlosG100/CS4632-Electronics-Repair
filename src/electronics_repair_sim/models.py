# Basic classes for the electronics repair simulation.

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
        self.busy_until = 0.0
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
        self.busy_until = 0.0
        self.busy_time = 0.0

    def can_handle(self, job):
        # General jobs can use any station.
        # Specialty jobs need a specialty-capable station.
        if job.capability == CAPABILITY_GENERAL:
            return True
        return self.capability == CAPABILITY_SPECIALTY


class ScenarioConfig:
    # Basic settings for one simulation run.
    def __init__(self):
        self.name = "baseline"

        # My starting system has 2 technicians and 2 stations.
        self.technicians = 2
        self.stations = 2

        # Production failures can interrupt lower-priority work.
        self.allow_preemption = True


def capability_from_sop(sop_value):
    if sop_value is None:
        return CAPABILITY_GENERAL

    cleaned = str(sop_value).strip().upper()

    for prefix in SPECIALTY_SOP_PREFIXES:
        if cleaned.startswith(prefix):
            return CAPABILITY_SPECIALTY

    return CAPABILITY_GENERAL
