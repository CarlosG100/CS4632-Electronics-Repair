from electronics_repair_sim.create_jobs import create_all_jobs
from electronics_repair_sim.rack import split_jobs_into_waiting_lines


def print_next_rma_jobs(rma_rack, amount):
    print("First RMA jobs on the rack")

    for count in range(amount):
        job = rma_rack.get_next_job()

        if job is None:
            print("No more open RMA jobs.")
            return

        print("Job:", job.job_id)
        print("Arrival time:", job.arrival_time)
        print("Priority:", job.priority)
        print("Estimated service hours:", format(job.service_time, ".2f"))
        print("Capability:", job.capability)
        print()


def main():
    jobs = create_all_jobs()
    rma_rack, direct_requests = split_jobs_into_waiting_lines(jobs)

    print("FIFO")
    print("Open RMA jobs:", rma_rack.count_jobs())
    print("Open direct requests:", direct_requests.count_jobs())
    print()

    print_next_rma_jobs(rma_rack, 5)


if __name__ == "__main__":
    main()
