from electronics_repair_sim.models import CAPABILITY_GENERAL, PRIORITY_ASAP, PRIORITY_CRITICAL, PRIORITY_NORMAL, SOURCE_ADVEX, SOURCE_RMA, Job
from electronics_repair_sim.rack import DirectRequestList, RmaRack


def print_next_rma_jobs(rma_rack, amount):
    print("RMA rack jobs in FIFO order")

    for count in range(amount):
        job = rma_rack.get_next_job()

        if job is None:
            print("No more jobs on the rack.")
            return

        print("Job:", job.job_id)
        print("Arrival time:", job.arrival_time)
        print("Priority:", job.priority)
        print("Estimated service hours:", format(job.service_time, ".2f"))
        print("Capability:", job.capability)
        print()


def print_next_direct_requests(direct_requests, amount):
    print("Direct requests in priority order")

    for count in range(amount):
        job = direct_requests.get_next_job()

        if job is None:
            print("No more direct requests.")
            return

        print("Job:", job.job_id)
        print("Priority:", job.priority)
        print()


def main():
    rma_rack = RmaRack()
    rma_rack.add_job(Job("RMA-A", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-05", 5, CAPABILITY_GENERAL))
    rma_rack.add_job(Job("RMA-B", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-01", 5, CAPABILITY_GENERAL))
    rma_rack.add_job(Job("RMA-C", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-10", 5, CAPABILITY_GENERAL))

    direct_requests = DirectRequestList()
    direct_requests.add_job(Job("ADVEX-A", SOURCE_ADVEX, PRIORITY_NORMAL, "2024-01-01", 1, CAPABILITY_GENERAL))
    direct_requests.add_job(Job("ADVEX-B", SOURCE_ADVEX, PRIORITY_ASAP, "2024-01-05", 1, CAPABILITY_GENERAL))
    direct_requests.add_job(Job("ADVEX-C", SOURCE_ADVEX, PRIORITY_CRITICAL, "2024-01-03", 1, CAPABILITY_GENERAL))

    print("Open RMA jobs:", rma_rack.count_jobs())
    print("Open direct requests:", direct_requests.count_jobs())
    print()

    print_next_rma_jobs(rma_rack, 5)
    print_next_direct_requests(direct_requests, 5)


if __name__ == "__main__":
    main()
