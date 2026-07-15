import contextlib
import csv
import os

from electronics_repair_sim.simpy_runner import run_basic_fifo_simulation


def run_quiet(config):
    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull):
            metrics = run_basic_fifo_simulation(config, export_results=False)

    return metrics


def get_key_metrics(metrics):
    total_sim_time = metrics.find_last_job_finish_time()

    return {
        "completed_jobs": metrics.count_completed_jobs(),
        "average_wait_time": metrics.calculate_average_wait_time(),
        "average_turnaround_time": metrics.calculate_average_turnaround_time(),
        "throughput_jobs_per_hour": metrics.calculate_throughput(total_sim_time),
    }


def write_rows_to_csv(rows, field_names, file_path):
    with open(file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)
