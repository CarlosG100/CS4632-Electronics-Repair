import os

from electronics_repair_sim.analysis import get_key_metrics, run_quiet, write_rows_to_csv
from electronics_repair_sim.create_jobs import apply_period_based_job_counts, build_all_job_models
from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import get_results_folder


UPDATABLE_PARAMETERS = [
    "general_technicians",
    "specialty_technicians",
    "general_stations",
    "specialty_stations",
    "simulation_period_hours",
    "job_limit",
    "advex_job_count",
    "reship_job_count",
    "production_job_count",
]

NUM_REPLICATIONS_PER_VALUE = 100
BASE_SEED = 2000


def print_baseline(config):
    print("Baseline (everything stays this way except the one parameter you change each run):")
    print("General Techs:", config.general_technicians)
    print("Specialty Techs:", config.specialty_technicians)
    print("General stations:", config.general_stations)
    print("Specialty stations:", config.specialty_stations)
    print("Simulation period (hours):", config.simulation_period_hours)
    print("Customer RMA jobs:", config.job_limit)
    print("AdvEx jobs:", config.advex_job_count)
    print("Reship jobs:", config.reship_job_count)
    print("Production jobs:", config.production_job_count)
    print("Allow preemption:", config.allow_preemption)
    print()


def ask_how_many_runs():
    text = input("How many runs do you want to do? Each run changes one parameter to one new value: ").strip()
    return int(text)


def ask_which_parameter(run_number):
    print()
    print("Run", str(run_number) + ": which parameter do you want to change?")

    index = 1
    for name in UPDATABLE_PARAMETERS:
        print(str(index) + ".", name)
        index += 1

    choice = input("Enter a number: ").strip()
    choice_index = int(choice) - 1

    return UPDATABLE_PARAMETERS[choice_index]


def ask_new_value(parameter_name):
    text = input("What new value do you want to test for " + parameter_name + "? ").strip()
    return int(text)


def get_parameter_value(config, parameter_name):
    if parameter_name == "general_technicians":
        return config.general_technicians
    elif parameter_name == "specialty_technicians":
        return config.specialty_technicians
    elif parameter_name == "general_stations":
        return config.general_stations
    elif parameter_name == "specialty_stations":
        return config.specialty_stations
    elif parameter_name == "simulation_period_hours":
        return config.simulation_period_hours
    elif parameter_name == "job_limit":
        return config.job_limit
    elif parameter_name == "advex_job_count":
        return config.advex_job_count
    elif parameter_name == "reship_job_count":
        return config.reship_job_count
    elif parameter_name == "production_job_count":
        return config.production_job_count


def apply_parameter_value(config, parameter_name, value):
    if parameter_name == "general_technicians":
        config.general_technicians = value
    elif parameter_name == "specialty_technicians":
        config.specialty_technicians = value
    elif parameter_name == "general_stations":
        config.general_stations = value
    elif parameter_name == "specialty_stations":
        config.specialty_stations = value
    elif parameter_name == "simulation_period_hours":
        config.simulation_period_hours = value
    elif parameter_name == "job_limit":
        config.job_limit = value
    elif parameter_name == "advex_job_count":
        config.advex_job_count = value
    elif parameter_name == "reship_job_count":
        config.reship_job_count = value
    elif parameter_name == "production_job_count":
        config.production_job_count = value

    return config


def clone_config_with_seed(base_config, seed):
    config = ScenarioConfig()
    config.name = base_config.name
    config.general_technicians = base_config.general_technicians
    config.specialty_technicians = base_config.specialty_technicians
    config.general_stations = base_config.general_stations
    config.specialty_stations = base_config.specialty_stations
    config.simulation_period_hours = base_config.simulation_period_hours
    config.job_limit = base_config.job_limit
    config.advex_job_count = base_config.advex_job_count
    config.reship_job_count = base_config.reship_job_count
    config.production_job_count = base_config.production_job_count
    config.snapshot_gap_hours = base_config.snapshot_gap_hours
    config.snapshot_limit = base_config.snapshot_limit
    config.allow_preemption = base_config.allow_preemption
    config.random_seed = seed

    return config


def average_metric_records(metric_records):
    completed_total = 0
    wait_total = 0
    turnaround_total = 0
    throughput_total = 0

    for record in metric_records:
        completed_total = completed_total + record["completed_jobs"]
        wait_total = wait_total + record["average_wait_time"]
        turnaround_total = turnaround_total + record["average_turnaround_time"]
        throughput_total = throughput_total + record["throughput_jobs_per_hour"]

    count = len(metric_records)

    return {
        "completed_jobs": completed_total / count,
        "average_wait_time": wait_total / count,
        "average_turnaround_time": turnaround_total / count,
        "throughput_jobs_per_hour": throughput_total / count,
    }


def run_averaged(base_config, num_replications):
    metric_records = []

    replication_number = 1
    while replication_number <= num_replications:
        config = clone_config_with_seed(base_config, BASE_SEED + replication_number)
        metrics = run_quiet(config)
        metric_records.append(get_key_metrics(metrics))
        replication_number += 1

    return average_metric_records(metric_records)


def run_baseline(baseline_config):
    record = run_averaged(baseline_config, NUM_REPLICATIONS_PER_VALUE)
    record["run_number"] = 0
    record["parameter"] = "baseline"
    record["value"] = ""

    return record


def run_one_change(run_number, parameter_name, value):
    config_template = ScenarioConfig()
    config_template.name = parameter_name + "=" + str(value)
    config_template = apply_parameter_value(config_template, parameter_name, value)

    record = run_averaged(config_template, NUM_REPLICATIONS_PER_VALUE)
    record["run_number"] = run_number
    record["parameter"] = parameter_name
    record["value"] = value

    return record


def calculate_percent_change(new_value, old_value):
    if old_value == 0:
        return 0

    return ((new_value - old_value) / old_value) * 100


def add_sensitivity(record, baseline_record, baseline_parameter_value):
    percent_input_change = calculate_percent_change(record["value"], baseline_parameter_value)

    if percent_input_change == 0:
        record["wait_time_sensitivity"] = 0
        record["turnaround_time_sensitivity"] = 0
    else:
        percent_wait_change = calculate_percent_change(record["average_wait_time"], baseline_record["average_wait_time"])
        percent_turnaround_change = calculate_percent_change(record["average_turnaround_time"], baseline_record["average_turnaround_time"])

        record["wait_time_sensitivity"] = percent_wait_change / percent_input_change
        record["turnaround_time_sensitivity"] = percent_turnaround_change / percent_input_change

    return record


def print_results_table(records):
    print()
    print("Run | Parameter                | Value | Avg Completed | Avg Wait  | Avg Turnaround | Throughput | Wait Sensitivity | Turnaround Sensitivity")
    print("---------------------------------------------------------------------------------------------------------------------------------------------")

    for record in records:
        print(
            str(record["run_number"]).rjust(3), "|",
            record["parameter"].ljust(24), "|",
            str(record["value"]).rjust(5), "|",
            format(record["completed_jobs"], ".1f").rjust(14), "|",
            format(record["average_wait_time"], ".4f").rjust(9), "|",
            format(record["average_turnaround_time"], ".4f").rjust(14), "|",
            format(record["throughput_jobs_per_hour"], ".4f").rjust(10), "|",
            format(record["wait_time_sensitivity"], ".2f").rjust(16), "|",
            format(record["turnaround_time_sensitivity"], ".2f").rjust(22),
        )


def run_parameter_updates():
    baseline_config = ScenarioConfig()

    rma_model, advex_model, reship_model, production_avg_interarrival_hours, _ = build_all_job_models(baseline_config)
    baseline_config = apply_period_based_job_counts(baseline_config, rma_model, advex_model, reship_model, production_avg_interarrival_hours)

    print("Running baseline (" + str(NUM_REPLICATIONS_PER_VALUE) + " replications)...")
    baseline_record = run_baseline(baseline_config)

    print()
    print_baseline(baseline_config)

    num_runs = ask_how_many_runs()

    records = [baseline_record]

    run_number = 1
    while run_number <= num_runs:
        parameter_name = ask_which_parameter(run_number)
        value = ask_new_value(parameter_name)

        baseline_parameter_value = get_parameter_value(baseline_config, parameter_name)

        print("Running", NUM_REPLICATIONS_PER_VALUE, "replications for", parameter_name, "=", value, "...")
        record = run_one_change(run_number, parameter_name, value)
        record = add_sensitivity(record, baseline_record, baseline_parameter_value)

        records.append(record)
        run_number += 1

    baseline_record["wait_time_sensitivity"] = 0
    baseline_record["turnaround_time_sensitivity"] = 0

    print_results_table(records)

    results_folder = get_results_folder()
    output_path = os.path.join(results_folder, "parameter_update.csv")

    field_names = [
        "run_number", "parameter", "value", "completed_jobs", "average_wait_time", "average_turnaround_time",
        "throughput_jobs_per_hour", "wait_time_sensitivity", "turnaround_time_sensitivity",
    ]
    write_rows_to_csv(records, field_names, output_path)


if __name__ == "__main__":
    run_parameter_updates()
