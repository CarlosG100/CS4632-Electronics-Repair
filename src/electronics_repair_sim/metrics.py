import csv
import os
from datetime import datetime


class SimulationMetrics:
    def __init__(self):
        self.completed_jobs = []
        self.queue_history = []

    def add_queue_snapshot(self, sim_time, tech_queue_length, station_queue_length, techs_busy, techs_idle, stations_busy, stations_idle):
        row = {
            "sim_time": sim_time,
            "tech_queue_length": tech_queue_length,
            "station_queue_length": station_queue_length,
            "techs_busy": techs_busy,
            "techs_idle": techs_idle,
            "stations_busy": stations_busy,
            "stations_idle": stations_idle,
        }

        self.queue_history.append(row)

    def record_completed_job(self, job, technician, station):
        wait_time = job.start_time - job.sim_arrival_time
        turnaround_time = job.finish_time - job.sim_arrival_time

        record = {
            "job_id": job.job_id,
            "source": job.source,
            "capability": job.capability,
            "outcome": job.outcome,
            "start_time": job.start_time,
            "finish_time": job.finish_time,
            "wait_time": wait_time,
            "turnaround_time": turnaround_time,
            "service_time": job.service_time,
            "technician": technician.tech_id,
            "station": station.station_id,
            "interrupted_count": job.interrupted_count,
        }

        self.completed_jobs.append(record)

    def count_completed_jobs(self):
        return len(self.completed_jobs)

    def find_last_job_finish_time(self):
        if len(self.completed_jobs) == 0:
            return 0

        last_time = self.completed_jobs[0]["finish_time"]
        for record in self.completed_jobs:
            if record["finish_time"] > last_time:
                last_time = record["finish_time"]

        return last_time

    def calculate_average_wait_time(self):
        if len(self.completed_jobs) == 0:
            return 0

        total = 0
        for record in self.completed_jobs:
            total = total + record["wait_time"]

        return total / len(self.completed_jobs)

    def calculate_average_turnaround_time(self):
        if len(self.completed_jobs) == 0:
            return 0

        total = 0
        for record in self.completed_jobs:
            total = total + record["turnaround_time"]

        return total / len(self.completed_jobs)

    def get_max_wait_time(self):
        if len(self.completed_jobs) == 0:
            return 0

        max_value = self.completed_jobs[0]["wait_time"]
        for record in self.completed_jobs:
            if record["wait_time"] > max_value:
                max_value = record["wait_time"]

        return max_value

    def get_min_wait_time(self):
        if len(self.completed_jobs) == 0:
            return 0

        min_value = self.completed_jobs[0]["wait_time"]
        for record in self.completed_jobs:
            if record["wait_time"] < min_value:
                min_value = record["wait_time"]

        return min_value

    def calculate_throughput(self, total_sim_time):
        if total_sim_time == 0:
            return 0

        return self.count_completed_jobs() / total_sim_time

    def export_events_csv(self, file_path, scenario_name):
        field_names = [
            "scenario", "job_id", "source", "capability", "outcome", "start_time", "finish_time",
            "wait_time", "turnaround_time", "service_time", "technician", "station",
            "interrupted_count",
        ]

        file_already_exists = os.path.exists(file_path)

        with open(file_path, "a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)

            if not file_already_exists:
                writer.writeheader()

            for record in self.completed_jobs:
                row = dict(record)
                row["scenario"] = scenario_name
                writer.writerow(row)

    def save_queue_history_csv(self, file_path, scenario_name):
        field_names = [
            "scenario", "sim_time", "tech_queue_length", "station_queue_length",
            "techs_busy", "techs_idle", "stations_busy", "stations_idle",
        ]

        file_already_exists = os.path.exists(file_path)

        with open(file_path, "a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)

            if not file_already_exists:
                writer.writeheader()

            for row in self.queue_history:
                row_with_scenario = dict(row)
                row_with_scenario["scenario"] = scenario_name
                writer.writerow(row_with_scenario)

    def export_summary_csv(self, file_path, technicians, stations, total_sim_time, scenario_name):
        new_row = {
            "scenario": scenario_name,
            "generated_at": datetime.now().isoformat(),
            "total_sim_time": total_sim_time,
            "completed_jobs": self.count_completed_jobs(),
            "average_wait_time": self.calculate_average_wait_time(),
            "average_turnaround_time": self.calculate_average_turnaround_time(),
            "max_wait_time": self.get_max_wait_time(),
            "min_wait_time": self.get_min_wait_time(),
            "throughput_jobs_per_hour": self.calculate_throughput(total_sim_time),
        }

        for tech in technicians:
            if total_sim_time > 0:
                percent_busy = (tech.busy_time / total_sim_time) * 100
            else:
                percent_busy = 0
            new_row[tech.tech_id + "_utilization_percent"] = percent_busy

        for station in stations:
            if total_sim_time > 0:
                percent_busy = (station.busy_time / total_sim_time) * 100
            else:
                percent_busy = 0
            new_row[station.station_id + "_utilization_percent"] = percent_busy

        existing_rows = []
        existing_field_names = []

        if os.path.exists(file_path):
            with open(file_path, newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                existing_field_names = reader.fieldnames or []
                existing_rows = list(reader)

        existing_rows.append(new_row)
        field_names = list(existing_field_names)
        for key in new_row:
            if key not in field_names:
                field_names.append(key)

        with open(file_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names, restval="")
            writer.writeheader()

            for row in existing_rows:
                writer.writerow(row)

    def print_summary(self, total_sim_time):
        print("Simulation Metrics")
        print("------------------")
        print("Completed jobs:", self.count_completed_jobs())
        print("Avg wait time:", format(self.calculate_average_wait_time(), ".2f"), "hrs")
        print("Avg turnaround time:", format(self.calculate_average_turnaround_time(), ".2f"), "hrs")
        print("Max wait time:", format(self.get_max_wait_time(), ".2f"), "hrs")
        print("Min wait time:", format(self.get_min_wait_time(), ".2f"), "hrs")
        print("Throughput (jobs per hour):", format(self.calculate_throughput(total_sim_time), ".4f"))
        print()

        for record in self.completed_jobs:
            print("Job ID:", record["job_id"])
            print("Source:", record["source"])
            print("Capability:", record["capability"])
            print("Outcome:", record["outcome"])
            print("Start time:", format(record["start_time"], ".2f"), "hrs")
            print("Finish time:", format(record["finish_time"], ".2f"), "hrs")
            print("Wait time:", format(record["wait_time"], ".2f"), "hrs")
            print("Turnaround time:", format(record["turnaround_time"], ".2f"), "hrs")
            print("Service time:", format(record["service_time"], ".2f"), "hrs")
            print("Technician:", record["technician"])
            print("Station:", record["station"])
            print("Interrupted count:", record["interrupted_count"])
            print()
