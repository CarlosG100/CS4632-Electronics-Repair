import simpy

from electronics_repair_sim.create_jobs import create_all_jobs
from electronics_repair_sim.metrics import SimulationMetrics
from electronics_repair_sim.models import CAPABILITY_SPECIALTY, ScenarioConfig
from electronics_repair_sim.rack import split_jobs_into_waiting_lines
from electronics_repair_sim.resources import create_stations, create_technicians


def find_tech_for_job(job, technicians):
    # go through the list and return the first tech that can work this job
    for tech in technicians:
        if tech.can_work(job):
            return tech
    return None


def find_station_for_job(job, stations):
    # go through the list and return the first station that can handle this job
    for station in stations:
        if station.can_handle(job):
            return station
    return None


def repair_job(env, job, tech_resource, station_resource, tech, station, metrics):
    print("Time", format(env.now, ".2f") + ":", job.job_id, "pending")
    with tech_resource.request() as tech_req:
        yield tech_req

        with station_resource.request() as station_req:
            yield station_req

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


def run_basic_fifo_simulation(job_limit):
    env = simpy.Environment()
    config = ScenarioConfig()

    technicians = create_technicians()
    stations = create_stations()

    general_tech_resource = simpy.Resource(env, capacity=1)
    specialty_tech_resource = simpy.Resource(env, capacity=1)
    general_station_resource = simpy.Resource(env, capacity=1)
    specialty_station_resource = simpy.Resource(env, capacity=1)

    metrics = SimulationMetrics()

    jobs = create_all_jobs()
    rma_rack, direct_requests = split_jobs_into_waiting_lines(jobs)

    print("Scenario:", config.name)
    print("Technicians:", config.technicians)
    print("Stations:", config.stations)
    print("Open RMA jobs waiting:", rma_rack.count_jobs())
    print("Open direct requests waiting:", direct_requests.count_jobs())
    print()

    for count in range(job_limit):
        job = rma_rack.get_next_job()

        if job is not None:
            # find a tech and station that can work this job
            tech = find_tech_for_job(job, technicians)
            station = find_station_for_job(job, stations)

            if tech is None or station is None:
                print("No compatible resources found for", job.job_id)
                continue

            # pick the right simpy resource based on job capability
            if job.capability == CAPABILITY_SPECIALTY:
                tech_resource = specialty_tech_resource
                station_resource = specialty_station_resource
            else:
                tech_resource = general_tech_resource
                station_resource = general_station_resource

            # mark when the job enters sim so wait time can be measured
            job.sim_arrival_time = env.now

            env.process(repair_job(env, job, tech_resource, station_resource, tech, station, metrics))

    env.run()

    print()
    metrics.print_summary()

    return metrics
