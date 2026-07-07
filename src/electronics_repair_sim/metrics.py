class SimulationMetrics:
    #data from one simulation run.
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
        # jobs completed per hour of simulation time
        if total_sim_time == 0:
            return 0

        return self.count_completed_jobs() / total_sim_time

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
