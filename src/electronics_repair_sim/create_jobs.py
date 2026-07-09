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
    OUTCOME_RESHIPPED,
    OUTCOME_RTV,
    PRIORITY_ASAP,
    SOURCE_ADVEX,
    SOURCE_PRODUCTION,
    SOURCE_RESHIP,
    SOURCE_RMA,
    Job,
    capability_from_sop,
)


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
    # Use closed unit rows for the historical service times.
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


def make_parent_lookup(rma_parents):
    # This connects each unit row back to the parent RMA row.
    parent_lookup = {}

    for parent in rma_parents:
        rma_id = parent.get("anon_rma_id", "")
        parent_lookup[rma_id] = parent

    return parent_lookup


def get_closed_units_by_source(rma_parents, rma_units, source):
    # Only look at closed units for the given source (RMA, AdvEx, or reship).
    parent_lookup = make_parent_lookup(rma_parents)
    closed_units = []

    for unit in rma_units:
        rma_id = unit.get("anon_rma_id", "")
        parent = parent_lookup.get(rma_id, {})

        unit_source = get_source_from_rma_type(parent.get("rma_type", ""))
        unit_status = unit.get("board_status", "").strip().lower()

        if unit_source == source and unit_status == "closed":
            closed_units.append(unit)

    return closed_units


def get_parent_rows_by_source(rma_parents, source):
    matching_rows = []

    for parent in rma_parents:
        parent_source = get_source_from_rma_type(parent.get("rma_type", ""))
        if parent_source == source:
            matching_rows.append(parent)

    return matching_rows


def get_average_interarrival_hours_by_source(rma_parents, source):
    matching_rows = get_parent_rows_by_source(rma_parents, source)
    dates = get_sorted_dates(matching_rows, "request_date")
    gaps = get_interarrival_hours(dates)
    return average(gaps)


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


def get_general_fraction(units):
    if len(units) == 0:
        return 0.5

    general_units, specialty_units = split_units_by_capability(units)
    return len(general_units) / len(units)


def get_outcome_counts(units):
    # count how many closed units ended up with each outcome
    counts = {}

    for unit in units:
        outcome = get_outcome_value(unit.get("outcome", ""))

        if outcome not in counts:
            counts[outcome] = 0

        counts[outcome] = counts[outcome] + 1

    return counts


def get_priority_counts(parent_rows):
    # count how many parent rows had each priority level
    counts = {}

    for parent in parent_rows:
        priority = get_priority_value(parent.get("priority", ""))

        if priority not in counts:
            counts[priority] = 0

        counts[priority] = counts[priority] + 1

    return counts


def draw_random_outcome(outcome_counts):
    # pick a random value
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


def build_job_model(rma_parents, rma_units, source):
    closed_units = get_closed_units_by_source(rma_parents, rma_units, source)
    general_units, specialty_units = split_units_by_capability(closed_units)

    matching_parent_rows = get_parent_rows_by_source(rma_parents, source)

    model = {
        "avg_interarrival_hours": get_average_interarrival_hours_by_source(rma_parents, source),
        "general_fraction": get_general_fraction(closed_units),
        "general_avg_service_time": average(get_rma_service_times_list(general_units)),
        "specialty_avg_service_time": average(get_rma_service_times_list(specialty_units)),
        "general_service_times": get_rma_service_times_list(general_units),
        "specialty_service_times": get_rma_service_times_list(specialty_units),
        "general_outcome_counts": get_outcome_counts(general_units),
        "specialty_outcome_counts": get_outcome_counts(specialty_units),
        "priority_counts": get_priority_counts(matching_parent_rows),
    }

    return model


def make_synthetic_job(job_number, id_prefix, source, model):
    if random.random() < model["general_fraction"]:
        capability = CAPABILITY_GENERAL
        service_times = model["general_service_times"]
        avg_service_time = model["general_avg_service_time"]
        outcome_counts = model["general_outcome_counts"]
    else:
        capability = CAPABILITY_SPECIALTY
        service_times = model["specialty_service_times"]
        avg_service_time = model["specialty_avg_service_time"]
        outcome_counts = model["specialty_outcome_counts"]

    if len(service_times) > 0:
        service_time = random.choice(service_times)
    else:
        service_time = avg_service_time

    outcome = draw_random_outcome(outcome_counts)
    priority = draw_random_outcome(model["priority_counts"])

    job = Job(id_prefix + "-" + str(job_number), source, priority, None, service_time, capability)
    job.outcome = outcome
    job.board_status = "open"
    return job


def make_reship_job(job_number, model):
    if random.random() < model["general_fraction"]:
        capability = CAPABILITY_GENERAL
    else:
        capability = CAPABILITY_SPECIALTY

    service_time = random.uniform(1, 2)

    priority = draw_random_outcome(model["priority_counts"])

    job = Job("RESHIP-" + str(job_number), SOURCE_RESHIP, priority, None, service_time, capability)
    job.outcome = OUTCOME_RESHIPPED
    job.board_status = "open"
    return job


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


def build_all_job_models(config):
    random.seed(config.random_seed)

    rma_parents, rma_units, production_rows = load_all_csv_data()

    rma_model = build_job_model(rma_parents, rma_units, SOURCE_RMA)
    advex_model = build_job_model(rma_parents, rma_units, SOURCE_ADVEX)
    reship_model = build_job_model(rma_parents, rma_units, SOURCE_RESHIP)

    reship_model["avg_interarrival_hours"] = advex_model["avg_interarrival_hours"]

    production_avg_interarrival_hours = get_average_production_interarrival_hours(production_rows)
    production_rtv_probability = get_production_rtv_probability(production_rows)

    return rma_model, advex_model, reship_model, production_avg_interarrival_hours, production_rtv_probability
