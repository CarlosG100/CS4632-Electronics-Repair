import csv
import json
from datetime import datetime


class SimulationMetrics:
    def __init__(self):
        self.completed_jobs = []

    def record_completed_job(self, job, technician, station):
        # wait time is how long the job sat before starting
        # turnaround time is how long the job took from arrival to finish
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
        }

        self.completed_jobs.append(record)

    def count_completed_jobs(self):
        return len(self.completed_jobs)

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

    def export_events_csv(self, file_path):
        field_names = [
            "job_id", "source", "capability", "outcome", "start_time", "finish_time",
            "wait_time", "turnaround_time", "service_time", "technician", "station",
        ]

        with open(file_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writeheader()

            for record in self.completed_jobs:
                writer.writerow(record)

    def export_summary_json(self, file_path, technicians, stations, total_sim_time):
        tech_utilization = {}
        for tech in technicians:
            if total_sim_time > 0:
                tech_utilization[tech.tech_id] = (tech.busy_time / total_sim_time) * 100
            else:
                tech_utilization[tech.tech_id] = 0

        station_utilization = {}
        for station in stations:
            if total_sim_time > 0:
                station_utilization[station.station_id] = (station.busy_time / total_sim_time) * 100
            else:
                station_utilization[station.station_id] = 0

        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_sim_time": total_sim_time,
            "completed_jobs": self.count_completed_jobs(),
            "average_wait_time": self.calculate_average_wait_time(),
            "average_turnaround_time": self.calculate_average_turnaround_time(),
            "max_wait_time": self.get_max_wait_time(),
            "min_wait_time": self.get_min_wait_time(),
            "throughput_jobs_per_hour": self.calculate_throughput(total_sim_time),
            "technician_utilization_percent": tech_utilization,
            "station_utilization_percent": station_utilization,
        }

        with open(file_path, "w") as json_file:
            json.dump(summary, json_file, indent=2)

    def print_summary(self, total_sim_time):
        print("Simulation Metrics")
        print("------------------")
        print("Completed jobs:", self.count_completed_jobs())
        print("Avg wait time:", format(self.calculate_average_wait_time(), ".2f"))
        print("Avg turnaround time:", format(self.calculate_average_turnaround_time(), ".2f"))
        print("Max wait time:", format(self.get_max_wait_time(), ".2f"))
        print("Min wait time:", format(self.get_min_wait_time(), ".2f"))
        print("Throughput (jobs per hour):", format(self.calculate_throughput(total_sim_time), ".4f"))
        print()

        for record in self.completed_jobs:
            print("Job ID:", record["job_id"])
            print("Source:", record["source"])
            print("Capability:", record["capability"])
            print("Outcome:", record["outcome"])
            print("Start time:", format(record["start_time"], ".2f"))
            print("Finish time:", format(record["finish_time"], ".2f"))
            print("Wait time:", format(record["wait_time"], ".2f"))
            print("Turnaround time:", format(record["turnaround_time"], ".2f"))
            print("Service time:", format(record["service_time"], ".2f"))
            print("Technician:", record["technician"])
            print("Station:", record["station"])
            print()
