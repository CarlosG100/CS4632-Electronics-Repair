from electronics_repair_sim.create_jobs import create_all_jobs
from electronics_repair_sim.job_rules import is_direct_request, is_rma_rack_job
from electronics_repair_sim.models import ScenarioConfig


def count_sources(jobs):
    # Count how many jobs came from each source.
    counts = {}

    for job in jobs:
        if job.source not in counts:
            counts[job.source] = 0

        counts[job.source] = counts[job.source] + 1

    return counts


def print_source_counts(jobs):
    counts = count_sources(jobs)

    print("Jobs by source")
    for source in sorted(counts):
        print(source + ":", counts[source])
    print()


def main():
    config = ScenarioConfig()
    jobs, avg_production_interarrival_hours, production_rtv_probability = create_all_jobs(config)

    open_rma_count = 0
    historical_rma_count = 0
    open_direct_request_count = 0
    historical_direct_request_count = 0

    for job in jobs:
        if is_rma_rack_job(job.source) and job.board_status == "open":
            open_rma_count = open_rma_count + 1
        if is_rma_rack_job(job.source) and job.board_status == "closed":
            historical_rma_count = historical_rma_count + 1
        if is_direct_request(job.source) and job.board_status == "open":
            open_direct_request_count = open_direct_request_count + 1
        if is_direct_request(job.source) and job.board_status != "open":
            historical_direct_request_count = historical_direct_request_count + 1

    print("Jobs made from data")
    print("Total jobs:", len(jobs))
    print("Open RMA rack jobs:", open_rma_count)
    print("Historical closed RMA jobs:", historical_rma_count)
    print("Open direct request jobs:", open_direct_request_count)
    print("Historical direct request jobs:", historical_direct_request_count)
    print()

    print_source_counts(jobs)

    print("Production failure model (learned from historical data)")
    print("Average interarrival hours:", format(avg_production_interarrival_hours, ".2f"))
    print("RTV probability:", format(production_rtv_probability, ".4f"))
    print()


if __name__ == "__main__":
    main()
