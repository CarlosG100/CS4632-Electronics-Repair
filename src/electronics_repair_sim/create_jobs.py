from electronics_repair_sim.csv_parser import load_all_csv_data
from electronics_repair_sim.input_analysis import average, parse_date
from electronics_repair_sim.job_rules import (
    get_outcome_value,
    get_priority_value,
    get_source_from_production_row,
    get_source_from_rma_type,
)
from electronics_repair_sim.models import (
    CAPABILITY_GENERAL,
    CAPABILITY_SPECIALTY,
    OUTCOME_REPAIRED,
    PRIORITY_ASAP,
    Job,
    capability_from_sop,
)


def make_parent_lookup(rma_parents):
    # This connects each unit row back to the parent RMA row.
    parent_lookup = {}

    for parent in rma_parents:
        rma_id = parent.get("anon_rma_id", "")
        parent_lookup[rma_id] = parent

    return parent_lookup


def get_capability(unit_row):
    # Use the capability column first.
    capability = unit_row.get("capability", "").strip().lower()

    if capability == CAPABILITY_SPECIALTY:
        return CAPABILITY_SPECIALTY
    if capability == CAPABILITY_GENERAL:
        return CAPABILITY_GENERAL

    return capability_from_sop(unit_row.get("sop", ""))


def get_service_time_from_dates(start_text, end_text):
    # Service time is from in-progress date to complete date.
    start_date = parse_date(start_text)
    end_date = parse_date(end_text)

    if start_date is None:
        return None
    if end_date is None:
        return None
    if end_date <= start_date:
        return None

    time_difference = end_date - start_date
    return time_difference.total_seconds() / 3600


def get_average_rma_service_time(rma_units):
    # Use closed RMA unit rows for the historical service-time estimate.
    service_times = []

    for unit in rma_units:
        unit_status = unit.get("board_status", "").strip().lower()

        if unit_status == "closed":
            service_time = get_service_time_from_dates(
                unit.get("in_progress_date", ""),
                unit.get("complete_date", ""),
            )

            if service_time is not None:
                service_times.append(service_time)

    return average(service_times)


def get_rma_service_time(unit_row, default_service_time):
    service_time = get_service_time_from_dates(
        unit_row.get("in_progress_date", ""),
        unit_row.get("complete_date", ""),
    )

    if service_time is not None:
        return service_time

    return default_service_time


def get_rma_board_status(parent_row, unit_row):
    # Treat the job as open only when the parent RMA and unit row are open.
    parent_status = parent_row.get("board_status", "").strip().lower()
    unit_status = unit_row.get("board_status", "").strip().lower()

    if parent_status == "open" and unit_status == "open":
        return "open"

    return "closed"


def create_rma_jobs(rma_parents, rma_units):
    jobs = []
    parent_lookup = make_parent_lookup(rma_parents)
    default_service_time = get_average_rma_service_time(rma_units)

    job_number = 1
    for unit in rma_units:
        rma_id = unit.get("anon_rma_id", "")
        parent = parent_lookup.get(rma_id, {})

        source = get_source_from_rma_type(parent.get("rma_type", ""))
        priority = get_priority_value(parent.get("priority", ""))
        arrival_time = parent.get("request_date", "")
        service_time = get_rma_service_time(unit, default_service_time)
        capability = get_capability(unit)

        job = Job(
            "RMA-" + str(job_number),
            source,
            priority,
            arrival_time,
            service_time,
            capability,
        )

        job.outcome = get_outcome_value(unit.get("outcome", ""))
        job.board_status = get_rma_board_status(parent, unit)
        jobs.append(job)
        job_number += 1

    return jobs


def create_production_jobs(production_rows):
    # Create simulation jobs from production issue rows.
    # Production failures are urgent and can interrupt lower-priority repair work.
    jobs = []

    job_number = 1
    for row in production_rows:
        source = get_source_from_production_row(row)
        priority = PRIORITY_ASAP
        arrival_time = row.get("arrival_date", "")
        service_time = 0.5
        capability = CAPABILITY_GENERAL

        job = Job(
            "PROD-" + str(job_number),
            source,
            priority,
            arrival_time,
            service_time,
            capability,
        )

        job.outcome = OUTCOME_REPAIRED
        job.board_status = "historical"
        jobs.append(job)
        job_number += 1

    return jobs


def create_all_jobs():
    rma_parents, rma_units, production_rows = load_all_csv_data()

    rma_jobs = create_rma_jobs(rma_parents, rma_units)
    production_jobs = create_production_jobs(production_rows)

    return rma_jobs + production_jobs
