import random

from electronics_repair_sim.csv_parser import load_all_csv_data
from electronics_repair_sim.input_analysis import average, get_interarrival_hours, get_sorted_dates, parse_date
from electronics_repair_sim.job_rules import (
    get_outcome_value,
    get_priority_value,
    get_production_outcome,
    get_source_from_rma_type,
)
from electronics_repair_sim.models import (
    CAPABILITY_GENERAL,
    CAPABILITY_SPECIALTY,
    OUTCOME_REPAIRED,
    OUTCOME_RTV,
    PRIORITY_ASAP,
    SOURCE_PRODUCTION,
    SOURCE_RMA,
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


def get_rma_service_times_list(rma_units):
    # Use closed RMA unit rows for the historical service times.
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

    return service_times


def get_average_rma_service_time(rma_units):
    service_times = get_rma_service_times_list(rma_units)
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
    #job is open only when the parent RMA and unit row are open.
    parent_status = parent_row.get("board_status", "").strip().lower()
    unit_status = unit_row.get("board_status", "").strip().lower()

    if parent_status == "open" and unit_status == "open":
        return "open"

    return "closed"


def get_closed_customer_rma_units(rma_parents, rma_units):
    # Only look at closed Customer RMA units.
    parent_lookup = make_parent_lookup(rma_parents)
    closed_units = []

    for unit in rma_units:
        rma_id = unit.get("anon_rma_id", "")
        parent = parent_lookup.get(rma_id, {})

        source = get_source_from_rma_type(parent.get("rma_type", ""))
        unit_status = unit.get("board_status", "").strip().lower()

        if source == SOURCE_RMA and unit_status == "closed":
            closed_units.append(unit)

    return closed_units


def split_units_by_capability(units):
    general_units = []
    specialty_units = []

    for unit in units:
        capability = get_capability(unit)

        if capability == CAPABILITY_SPECIALTY:
            specialty_units.append(unit)
        else:
            general_units.append(unit)

    return general_units, specialty_units


def get_outcome_counts(units):
    # count how many closed units ended up with each outcome
    counts = {}

    for unit in units:
        outcome = get_outcome_value(unit.get("outcome", ""))

        if outcome not in counts:
            counts[outcome] = 0

        counts[outcome] = counts[outcome] + 1

    return counts


def draw_random_outcome(outcome_counts):
    total = sum(outcome_counts.values())

    if total == 0:
        return "unknown"

    roll = random.uniform(0, total)
    running_total = 0

    for outcome in outcome_counts:
        running_total = running_total + outcome_counts[outcome]
        if roll <= running_total:
            return outcome

    return "unknown"


def create_rma_jobs(rma_parents, rma_units):
    jobs = []
    parent_lookup = make_parent_lookup(rma_parents)

    # build a repair-time and outcome model from closed Customer RMA units only,
    closed_customer_units = get_closed_customer_rma_units(rma_parents, rma_units)
    general_closed_units, specialty_closed_units = split_units_by_capability(closed_customer_units)

    general_service_times = get_rma_service_times_list(general_closed_units)
    specialty_service_times = get_rma_service_times_list(specialty_closed_units)

    general_avg_service_time = average(general_service_times)
    specialty_avg_service_time = average(specialty_service_times)

    general_outcome_counts = get_outcome_counts(general_closed_units)
    specialty_outcome_counts = get_outcome_counts(specialty_closed_units)

    job_number = 1
    for unit in rma_units:
        rma_id = unit.get("anon_rma_id", "")
        parent = parent_lookup.get(rma_id, {})

        source = get_source_from_rma_type(parent.get("rma_type", ""))
        priority = get_priority_value(parent.get("priority", ""))
        arrival_time = parent.get("request_date", "")
        capability = get_capability(unit)
        board_status = get_rma_board_status(parent, unit)

        is_open_customer_rma = source == SOURCE_RMA and board_status == "open"

        if is_open_customer_rma:
            if capability == CAPABILITY_SPECIALTY:
                if len(specialty_service_times) > 0:
                    service_time = random.choice(specialty_service_times)
                else:
                    service_time = specialty_avg_service_time
                outcome = draw_random_outcome(specialty_outcome_counts)
            else:
                if len(general_service_times) > 0:
                    service_time = random.choice(general_service_times)
                else:
                    service_time = general_avg_service_time
                outcome = draw_random_outcome(general_outcome_counts)
        else:
            if capability == CAPABILITY_SPECIALTY:
                default_service_time = specialty_avg_service_time
            else:
                default_service_time = general_avg_service_time

            service_time = get_rma_service_time(unit, default_service_time)
            outcome = get_outcome_value(unit.get("outcome", ""))

        job = Job(
            "RMA-" + str(job_number),
            source,
            priority,
            arrival_time,
            service_time,
            capability,
        )

        job.outcome = outcome
        job.board_status = board_status
        jobs.append(job)
        job_number += 1

    return jobs


def get_average_production_interarrival_hours(production_rows):
    # historical average time between production failures
    dates = get_sorted_dates(production_rows, "arrival_date")
    gaps = get_interarrival_hours(dates)
    return average(gaps)


def get_production_rtv_probability(production_rows):
    # what percentage of historical production failures had a location filled in
    if len(production_rows) == 0:
        return 0

    rtv_count = 0
    for row in production_rows:
        outcome = get_production_outcome(row.get("location", ""))
        if outcome == OUTCOME_RTV:
            rtv_count = rtv_count + 1

    return rtv_count / len(production_rows)


def make_production_job(job_number, rtv_probability):
    # simulate a brand new production failure using patterns learned from history
    if random.random() < rtv_probability:
        outcome = OUTCOME_RTV
    else:
        outcome = OUTCOME_REPAIRED

    job = Job(
        "PROD-" + str(job_number),
        SOURCE_PRODUCTION,
        PRIORITY_ASAP,
        None,
        0.5,
        CAPABILITY_GENERAL,
    )

    job.outcome = outcome
    job.board_status = "open"
    return job


def create_all_jobs(config):
    random.seed(config.random_seed)

    rma_parents, rma_units, production_rows = load_all_csv_data()

    rma_jobs = create_rma_jobs(rma_parents, rma_units)

    avg_production_interarrival_hours = get_average_production_interarrival_hours(production_rows)
    production_rtv_probability = get_production_rtv_probability(production_rows)

    return rma_jobs, avg_production_interarrival_hours, production_rtv_probability
