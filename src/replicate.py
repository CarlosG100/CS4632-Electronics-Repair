import os
import statistics

from electronics_repair_sim.analysis import get_key_metrics, run_quiet, write_rows_to_csv
from electronics_repair_sim.cli_prompts import ask_custom_parameters, ask_yes_no
from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import get_results_folder



NUM_REPLICATIONS = 100


BASE_SEED = 1000


def run_one_replication(base_config, replication_number):
    config = ScenarioConfig()
    config.name = base_config.name + " - replication " + str(replication_number)
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

  
    config.random_seed = BASE_SEED + replication_number

    metrics = run_quiet(config)

    record = get_key_metrics(metrics)
    record["replication_number"] = replication_number
    record["random_seed"] = config.random_seed

    return record


def calculate_confidence_interval(values):
    
    sample_size = len(values)

    if sample_size < 2:
        return 0, 0

    mean_value = statistics.mean(values)
    std_dev = statistics.stdev(values)
    margin_of_error = 1.96 * (std_dev / (sample_size ** 0.5))

    return mean_value - margin_of_error, mean_value + margin_of_error


def summarize_metric(metric_name, values):
    mean_value = statistics.mean(values)

    if len(values) > 1:
        std_dev = statistics.stdev(values)
    else:
        std_dev = 0

    ci_lower, ci_upper = calculate_confidence_interval(values)

    return {
        "metric": metric_name,
        "mean": mean_value,
        "std_dev": std_dev,
        "min": min(values),
        "max": max(values),
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
    }


def print_summary_table(summary_rows, num_replications):
    print("Statistical Summary across", num_replications, "replications")
    print("Metric                          | Mean      | Std Dev   | Min       | Max       | 95% CI")
    print("---------------------------------------------------------------------------------------------")

    for row in summary_rows:
        metric_column = row["metric"].ljust(31)
        mean_column = format(row["mean"], ".4f").rjust(9)
        std_dev_column = format(row["std_dev"], ".4f").rjust(9)
        min_column = format(row["min"], ".4f").rjust(9)
        max_column = format(row["max"], ".4f").rjust(9)
        ci_column = "[" + format(row["ci_95_lower"], ".4f") + ", " + format(row["ci_95_upper"], ".4f") + "]"

        print(metric_column, "|", mean_column, "|", std_dev_column, "|", min_column, "|", max_column, "|", ci_column)


def replicate():
    base_config = ScenarioConfig()
    base_config.name = "base run"

    if ask_yes_no("Do you want to set custom parameters for the scenario being replicated"):
        base_config = ask_custom_parameters(base_config)

    print()
    print("Running", NUM_REPLICATIONS, "replications of", "'" + base_config.name + "'", "with different random seeds...")

    records = []
    replication_number = 1
    while replication_number <= NUM_REPLICATIONS:
        record = run_one_replication(base_config, replication_number)
        records.append(record)
        replication_number += 1

    wait_times = []
    turnaround_times = []
    throughputs = []
    for record in records:
        wait_times.append(record["average_wait_time"])
        turnaround_times.append(record["average_turnaround_time"])
        throughputs.append(record["throughput_jobs_per_hour"])

    summary_rows = [
        summarize_metric("Average Wait Time (hrs)", wait_times),
        summarize_metric("Average Turnaround Time (hrs)", turnaround_times),
        summarize_metric("Throughput (jobs/hr)", throughputs),
    ]

    print()
    print_summary_table(summary_rows, NUM_REPLICATIONS)

    results_folder = get_results_folder()
    runs_path = os.path.join(results_folder, "replication_runs.csv")
    summary_path = os.path.join(results_folder, "replication_summary.csv")

    runs_field_names = [
        "replication_number", "random_seed", "completed_jobs",
        "average_wait_time", "average_turnaround_time", "throughput_jobs_per_hour",
    ]
    summary_field_names = ["metric", "mean", "std_dev", "min", "max", "ci_95_lower", "ci_95_upper"]

    write_rows_to_csv(records, runs_field_names, runs_path)
    write_rows_to_csv(summary_rows, summary_field_names, summary_path)


if __name__ == "__main__":
    replicate()
