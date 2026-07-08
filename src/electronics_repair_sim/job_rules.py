from electronics_repair_sim.models import (
    OUTCOME_REPAIRED,
    OUTCOME_RTV,
    OUTCOME_SCRAP,
    PRIORITY_ASAP,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
    SOURCE_ADVEX,
    SOURCE_PRODUCTION,
    SOURCE_RESHIP,
    SOURCE_RMA,
)


def get_priority_value(priority_text):
    # Convert CSV priority text into a number.
    # Lower number means higher priority.
    cleaned = clean_text(priority_text)

    if cleaned == "asap":
        return PRIORITY_ASAP
    if cleaned == "critical":
        return PRIORITY_CRITICAL
    if cleaned == "high":
        return PRIORITY_HIGH

    return PRIORITY_NORMAL


def get_source_from_rma_type(rma_type):
    # Convert an RMA type from data into a simulation source.
    cleaned = clean_text(rma_type)

    if cleaned == "advex":
        return SOURCE_ADVEX
    if cleaned == "reship":
        return SOURCE_RESHIP

    return SOURCE_RMA


def get_source_from_production_row(row):
    # Production CSV rows are direct production failure work.
    return SOURCE_PRODUCTION


def get_production_outcome(location_value):
    cleaned = clean_text(location_value)

    if cleaned == "":
        return OUTCOME_REPAIRED

    return OUTCOME_RTV


def get_outcome_value(outcome_text):
    # Convert CSV outcome text into a simulation outcome.
    cleaned = clean_text(outcome_text)

    if cleaned == "repaired":
        return OUTCOME_REPAIRED
    if cleaned == "scrap":
        return OUTCOME_SCRAP
    if cleaned == "rtv":
        return OUTCOME_RTV

    return "unknown"


def is_direct_request(source):
    # AdvEx do not wait on the normal RMA rack.
    if source == SOURCE_ADVEX:
        return True
    if source == SOURCE_RESHIP:
        return True
    if source == SOURCE_PRODUCTION:
        return True

    return False


def is_rma_rack_job(source):
    # Customer RMA jobs wait on the RMA rack in FIFO order.
    return source == SOURCE_RMA


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()
