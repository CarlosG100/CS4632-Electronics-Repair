class SimulationMetrics:
    #data from one simulation run.
    def __init__(self):
        self.completed_jobs = []

    def record_completed_job(self, job, technician, station):
        record = {
            "job_id": job.job_id,
            "source": job.source,
            "capability": job.capability,
            "outcome": job.outcome,
            "start_time": job.start_time,
            "finish_time": job.finish_time,
            "wait_time": job.start_time,
            "turnaround_time": job.finish_time,
            "service_time": job.service_time,
            "technician": technician.tech_id,
            "station": station.station_id,
        }

        self.completed_jobs.append(record)

    def count_completed_jobs(self):
        return len(self.completed_jobs)

    def print_summary(self):
        print("Simulation Metrics")
        print("------------------")
        print("Completed jobs:", self.count_completed_jobs())
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
