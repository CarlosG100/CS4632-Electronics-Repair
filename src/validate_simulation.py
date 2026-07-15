import simpy

from electronics_repair_sim.metrics import SimulationMetrics
from electronics_repair_sim.models import (
    CAPABILITY_GENERAL,
    PRIORITY_ASAP,
    PRIORITY_CRITICAL,
    PRIORITY_NORMAL,
    SOURCE_ADVEX,
    SOURCE_PRODUCTION,
    SOURCE_RMA,
    Job,
    ScenarioConfig,
    validate_config,
)
from electronics_repair_sim.rack import DirectRequestList, RmaRack
from electronics_repair_sim.resources import create_stations, create_technicians
from electronics_repair_sim.simpy_runner import repair_job, run_basic_fifo_simulation


def check_rma_rack_fifo_order():
    rack = RmaRack()

    job_a = Job("A", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-05", 1, CAPABILITY_GENERAL)
    job_b = Job("B", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-01", 1, CAPABILITY_GENERAL)
    job_c = Job("C", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-10", 1, CAPABILITY_GENERAL)

    rack.add_job(job_a)
    rack.add_job(job_b)
    rack.add_job(job_c)

    first = rack.get_next_job()
    second = rack.get_next_job()
    third = rack.get_next_job()

    if first.job_id == "B" and second.job_id == "A" and third.job_id == "C":
        return True

    return False


def check_direct_request_priority_order():
    direct_requests = DirectRequestList()

    job_low = Job("LOW", SOURCE_ADVEX, PRIORITY_NORMAL, "2024-01-01", 1, CAPABILITY_GENERAL)
    job_high = Job("HIGH", SOURCE_ADVEX, PRIORITY_ASAP, "2024-01-05", 1, CAPABILITY_GENERAL)
    job_mid = Job("MID", SOURCE_ADVEX, PRIORITY_CRITICAL, "2024-01-03", 1, CAPABILITY_GENERAL)

    direct_requests.add_job(job_low)
    direct_requests.add_job(job_high)
    direct_requests.add_job(job_mid)

    first = direct_requests.get_next_job()
    second = direct_requests.get_next_job()
    third = direct_requests.get_next_job()

    if first.job_id == "HIGH" and second.job_id == "MID" and third.job_id == "LOW":
        return True

    return False


def check_config_validation_catches_bad_input():
    bad_config = ScenarioConfig()
    bad_config.general_technicians = 0
    bad_config.specialty_technicians = 0

    try:
        validate_config(bad_config)
    except ValueError:
        return True

    return False


def check_config_validation_allows_good_input():
    good_config = ScenarioConfig()

    try:
        validate_config(good_config)
    except ValueError:
        return False

    return True


def get_start_time(record):
    return record["start_time"]


def check_no_double_booking():
    config = ScenarioConfig()
    config.name = "validation check no preemption"
    config.job_limit = 5
    config.advex_job_count = 5
    config.reship_job_count = 5
    config.production_job_count = 0
    config.allow_preemption = False

    metrics = run_basic_fifo_simulation(config)

    jobs_by_tech = {}
    for record in metrics.completed_jobs:
        tech = record["technician"]
        if tech not in jobs_by_tech:
            jobs_by_tech[tech] = []
        jobs_by_tech[tech].append(record)

    for tech in jobs_by_tech:
        jobs = jobs_by_tech[tech]
        jobs.sort(key=get_start_time)

        for index in range(1, len(jobs)):
            previous_job = jobs[index - 1]
            current_job = jobs[index]

            if current_job["start_time"] < previous_job["finish_time"]:
                return False

    return True


def check_wait_and_turnaround_make_sense():
    config = ScenarioConfig()
    config.name = "validation check wait and turnaround"
    config.job_limit = 5
    config.advex_job_count = 5
    config.reship_job_count = 5
    config.production_job_count = 0
    config.allow_preemption = False

    metrics = run_basic_fifo_simulation(config)

    for record in metrics.completed_jobs:
        if record["wait_time"] < 0:
            return False

        expected_minimum_turnaround = record["wait_time"] + record["service_time"]

        if record["turnaround_time"] < expected_minimum_turnaround - 0.01:
            return False

    return True


def check_preemption_interrupts_lower_priority_job():
    config = ScenarioConfig()
    config.general_technicians = 1
    config.specialty_technicians = 0
    config.general_stations = 1
    config.specialty_stations = 0
    technicians = create_technicians(config)
    stations = create_stations(config)

    env = simpy.Environment()
    general_tech_resource = simpy.PreemptiveResource(env, capacity=1)
    specialty_tech_resource = simpy.PreemptiveResource(env, capacity=1)
    general_station_resource = simpy.PreemptiveResource(env, capacity=1)
    specialty_station_resource = simpy.PreemptiveResource(env, capacity=1)
    metrics = SimulationMetrics()

    normal_job = Job("NORMAL-TEST", SOURCE_RMA, PRIORITY_NORMAL, "2024-01-01", 10, CAPABILITY_GENERAL)
    normal_job.sim_arrival_time = 0

    production_job = Job("PROD-TEST", SOURCE_PRODUCTION, PRIORITY_ASAP, None, 2, CAPABILITY_GENERAL)

    def start_normal_job():
        yield env.process(repair_job(
            env, normal_job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
            technicians, stations, metrics, False,
        ))

    def start_production_job():
        yield env.timeout(3)
        production_job.sim_arrival_time = env.now
        yield env.process(repair_job(
            env, production_job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
            technicians, stations, metrics, True,
        ))

    env.process(start_normal_job())
    env.process(start_production_job())
    env.run()

    if normal_job.interrupted_count > 0:
        return True

    return False


def run_all_checks():
    checks = [
        ("RMA rack picks oldest job first", check_rma_rack_fifo_order),
        ("Direct requests pick highest priority first", check_direct_request_priority_order),
        ("Config validation catches bad input", check_config_validation_catches_bad_input),
        ("Config validation allows good input", check_config_validation_allows_good_input),
        ("No technician is double booked", check_no_double_booking),
        ("Wait and turnaround time add up correctly", check_wait_and_turnaround_make_sense),
        ("Preemption interrupts a lower priority job", check_preemption_interrupts_lower_priority_job),
    ]

    passed_count = 0
    failed_count = 0

    print("Validation Checks")
    print("-----------------")

    for description, check_function in checks:
        passed = check_function()

        if passed:
            print("PASS -", description)
            passed_count = passed_count + 1
        else:
            print("FAIL -", description)
            failed_count = failed_count + 1

    print()
    print("Checks passed:", passed_count)
    print("Checks failed:", failed_count)


if __name__ == "__main__":
    run_all_checks()
