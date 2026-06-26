from datetime import datetime

from electronics_repair_sim.csv_parser import count_values, load_all_csv_data


def parse_date(date_text):
    # try to turn a date string into a datetime object
    # returns None if the date is blank or doesn't work
    if date_text is None:
        return None

    cleaned = str(date_text).strip()
    if cleaned == "":
        return None

    try:
        return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        return datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        pass

    try:
        return datetime.strptime(cleaned, "%m/%d/%Y %H:%M")
    except ValueError:
        pass

    return None


def get_sorted_dates(rows, column_name):
    # Pull valid dates from a column and sort them.
    dates = []

    for row in rows:
        parsed_date = parse_date(row.get(column_name, ""))
        if parsed_date is not None:
            dates.append(parsed_date)

    dates.sort()
    return dates


def get_interarrival_hours(dates):
    # Interarrival time is the time between one arrival and the next.
    interarrival_hours = []

    for index in range(1, len(dates)):
        time_difference = dates[index] - dates[index - 1]
        hours = time_difference.total_seconds() / 3600

        if hours >= 0:
            interarrival_hours.append(hours)

    return interarrival_hours


def get_service_hours(unit_rows):
    # Service time is in-progress date to complete date.
    service_hours = []

    for row in unit_rows:
        start_date = parse_date(row.get("in_progress_date", ""))
        end_date = parse_date(row.get("complete_date", ""))

        if start_date is not None and end_date is not None and end_date > start_date:
            hours = (end_date - start_date).total_seconds() / 3600
            service_hours.append(hours)

    return service_hours


def average(values):
    if len(values) == 0:
        return 0

    return sum(values) / len(values)


def percentage(part, total):
    if total == 0:
        return 0

    return (part / total) * 100


def print_date_range(title, dates):
    # Print the first and last date for a date list.
    print(title)

    if len(dates) == 0:
        print("No valid dates found")
        print()
        return

    print("First date:", dates[0])
    print("Last date:", dates[-1])
    print("Valid date count:", len(dates))
    print()


def print_percent_counts(title, counts):
    # Print counts and percentages for a category column.
    print(title)

    total = sum(counts.values())
    for value in sorted(counts):
        percent = percentage(counts[value], total)
        print(value + ":", counts[value], "(" + format(percent, ".1f") + "%)")

    print()


def print_input_estimates():
    # use CSV data to estimate early simulation inputs.
    rma_parents, rma_units, production_jobs = load_all_csv_data()

    rma_request_dates = get_sorted_dates(rma_parents, "request_date")
    production_arrival_dates = get_sorted_dates(production_jobs, "arrival_date")

    rma_interarrival_hours = get_interarrival_hours(rma_request_dates)
    production_interarrival_hours = get_interarrival_hours(production_arrival_dates)
    repair_service_hours = get_service_hours(rma_units)

    print_date_range("RMA request dates", rma_request_dates)
    print_date_range("Production issue dates", production_arrival_dates)

    print("Arrival times")
    print("RMA arrivals with valid request dates:", len(rma_request_dates))
    print("Average RMA interarrival hours:", format(average(rma_interarrival_hours), ".2f"))
    print("Production arrivals with valid dates:", len(production_arrival_dates))
    print("Average production interarrival hours:", format(average(production_interarrival_hours), ".2f"))
    print()

    print("Service times")
    print("RMA units with valid service times:", len(repair_service_hours))
    print("Average RMA service hours:", format(average(repair_service_hours), ".2f"))
    print("Production service time assumption: 0.50 hours")
    print()

    print_percent_counts("Outcomes", count_values(rma_units, "outcome"))
    print_percent_counts("Capabilities", count_values(rma_units, "capability"))
    print_percent_counts("Priorities", count_values(rma_parents, "priority"))
