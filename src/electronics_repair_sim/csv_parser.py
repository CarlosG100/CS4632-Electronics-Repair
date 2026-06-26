import csv
import os


# File names for the cleaned project CSV data.
RMA_PARENT_FILE = "rma_parent_jobs.csv"
RMA_UNIT_FILE = "rma_unit_jobs.csv"
PRODUCTION_FILE = "production_issue_jobs.csv"


def get_data_folder():
    this_file = os.path.abspath(__file__)
    sim_folder = os.path.dirname(this_file)
    src_folder = os.path.dirname(sim_folder)
    project_folder = os.path.dirname(src_folder)
    return os.path.join(project_folder, "data")


def read_csv_file(file_name):
    # Read a CSV file and return a list of rows.
    file_path = os.path.join(get_data_folder(), file_name)

    rows = []
    with open(file_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)

    return rows


def load_all_csv_data():
    # Load all three cleaned CSV files.
    rma_parents = read_csv_file(RMA_PARENT_FILE)
    rma_units = read_csv_file(RMA_UNIT_FILE)
    production_jobs = read_csv_file(PRODUCTION_FILE)

    return rma_parents, rma_units, production_jobs


def count_values(rows, column_name):
    # Count how many times each value appears in a column.
    counts = {}

    for row in rows:
        value = row.get(column_name, "").strip()

        if value == "":
            value = "blank"

        if value not in counts:
            counts[value] = 0

        counts[value] = counts[value] + 1

    return counts


def count_missing(rows, column_name):
    # Count blank values in a column.
    missing_count = 0

    for row in rows:
        value = row.get(column_name, "").strip()
        if value == "":
            missing_count = missing_count + 1

    return missing_count


def print_counts(title, counts):
    # Print count results
    print(title)

    for value in sorted(counts):
        print(value + ":", counts[value])

    print()


def print_csv_summary():
    # verify project can read the data.
    rma_parents, rma_units, production_jobs = load_all_csv_data()

    print("RMA parent jobs:", len(rma_parents))
    print("RMA unit jobs:", len(rma_units))
    print("Production issue jobs:", len(production_jobs))
    print()

    print_counts("RMA priorities", count_values(rma_parents, "priority"))
    print_counts("RMA types", count_values(rma_parents, "rma_type"))
    print_counts("Unit outcomes", count_values(rma_units, "outcome"))
    print_counts("Unit capabilities", count_values(rma_units, "capability"))
    print_counts("Production locations", count_values(production_jobs, "location"))

