from datetime import datetime

from electronics_repair_sim.input_analysis import parse_date
from electronics_repair_sim.job_rules import is_direct_request, is_rma_rack_job


class RmaRack:
    # Open customer RMA jobs are picked in FIFO order.
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def sort_fifo(self):
        # Oldest arrival date should be first on the rack.
        self.jobs.sort(key=get_fifo_sort_value)

    def get_next_job(self):
        # Return the oldest job and remove it from the rack.
        if len(self.jobs) == 0:
            return None

        self.sort_fifo()
        return self.jobs.pop(0)

    def look_at_next_job(self):
        # Return the oldest job without removing it from the rack.
        if len(self.jobs) == 0:
            return None

        self.sort_fifo()
        return self.jobs[0]

    def count_jobs(self):
        return len(self.jobs)


class DirectRequestList:
    # This holds AdvEx, reship, and production jobs.
    # These are worked in priority order instead of FIFO order.
    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def sort_by_priority(self):
        # lower priority number means the job should be worked first
        self.jobs.sort(key=get_priority_sort_value)

    def get_next_job(self):
        # Return the highest priority job and remove it from the list.
        if len(self.jobs) == 0:
            return None

        self.sort_by_priority()
        return self.jobs.pop(0)

    def look_at_next_job(self):
        # Return the highest priority job without removing it from the list.
        if len(self.jobs) == 0:
            return None

        self.sort_by_priority()
        return self.jobs[0]

    def count_jobs(self):
        return len(self.jobs)


def get_fifo_sort_value(job):
    arrival_date = parse_date(job.arrival_time)

    if arrival_date is None:
        return datetime(9999, 12, 31)

    return arrival_date


def get_priority_sort_value(job):
    arrival_date = parse_date(job.arrival_time)

    if arrival_date is None:
        arrival_date = datetime(9999, 12, 31)

    return (job.priority, arrival_date)


def split_jobs_into_waiting_lines(jobs):
    # Separate open rack jobs from direct requests.
    rma_rack = RmaRack()
    direct_requests = DirectRequestList()

    for job in jobs:
        if is_rma_rack_job(job.source) and job.board_status == "open":
            rma_rack.add_job(job)
        elif is_direct_request(job.source) and job.board_status == "open":
            direct_requests.add_job(job)

    return rma_rack, direct_requests
