import simpy

from electronics_repair_sim.create_jobs import create_all_jobs
from electronics_repair_sim.metrics import SimulationMetrics
from electronics_repair_sim.models import CAPABILITY_SPECIALTY, validate_config
from electronics_repair_sim.rack import split_jobs_into_waiting_lines
from electronics_repair_sim.resources import create_stations, create_technicians


def find_free_tech(job, technicians):
    # go through the list and return the first free tech that can work this job
    for tech in technicians:
        if tech.can_work(job) and tech.current_job_id is None:
            return tech
    return None


def find_free_station(job, stations):
    # go through the list and return the first free station that can handle this job
    for station in stations:
        if station.can_handle(job) and station.current_job_id is None:
            return station
    return None


def pick_resources(job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource):
    # return the right pair of simpy resources based on job capability
    if job.capability == CAPABILITY_SPECIALTY:
        return specialty_tech_resource, specialty_station_resource
    return general_tech_resource, general_station_resource


def repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics):
    print("Time", format(env.now, ".2f") + ":", job.job_id, "pending")

    with tech_resource.request() as tech_req:
        yield tech_req

        with station_resource.request() as station_req:
            yield station_req

            tech = find_free_tech(job, technicians)
            station = find_free_station(job, stations)

            job.start_time = env.now
            tech.current_job_id = job.job_id
            station.current_job_id = job.job_id

            print("Time", format(env.now, ".2f") + ":", job.job_id, "started on", tech.tech_id, "and", station.station_id)

            yield env.timeout(job.service_time)

            job.finish_time = env.now

            print("Time", format(env.now, ".2f") + ":", job.job_id, "finished")

            metrics.record_completed_job(job, tech, station)

            tech.current_job_id = None
            station.current_job_id = None


def run_basic_fifo_simulation(config):
    validate_config(config)

    env = simpy.Environment()

    technicians = create_technicians(config)
    stations = create_stations(config)

    general_tech_resource = simpy.Resource(env, capacity=config.general_technicians)
    specialty_tech_resource = simpy.Resource(env, capacity=config.specialty_technicians)
    general_station_resource = simpy.Resource(env, capacity=config.general_stations)
    specialty_station_resource = simpy.Resource(env, capacity=config.specialty_stations)

    metrics = SimulationMetrics()

    jobs = create_all_jobs()
    rma_rack, direct_requests = split_jobs_into_waiting_lines(jobs)

    print("Scenario:", config.name)
    print("General technicians:", config.general_technicians)
    print("Specialty technicians:", config.specialty_technicians)
    print("General stations:", config.general_stations)
    print("Specialty stations:", config.specialty_stations)
    print("Allow preemption:", config.allow_preemption)
    print("Job limit:", config.job_limit)
    print("Direct request limit:", config.direct_request_limit)
    print("Open RMA jobs waiting:", rma_rack.count_jobs())
    print("Open direct requests waiting:", direct_requests.count_jobs())
    print()

    for count in range(config.job_limit):
        job = rma_rack.get_next_job()

        if job is not None:
            tech_resource, station_resource = pick_resources(
                job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource
            )

            # mark when the job enters the sim so wait time can be measured
            job.sim_arrival_time = env.now

            env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics))

    # direct requests (AdvEx, reship, production) are pulled in priority order
    for count in range(config.direct_request_limit):
        job = direct_requests.get_next_job()

        if job is not None:
            tech_resource, station_resource = pick_resources(
                job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource
            )

            job.sim_arrival_time = env.now

            env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics))

    env.run()

    print()
    metrics.print_summary()

    return metrics
