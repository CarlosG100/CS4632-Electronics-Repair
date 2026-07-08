import os
import random

import simpy

from electronics_repair_sim.create_jobs import create_all_jobs, make_production_job
from electronics_repair_sim.metrics import SimulationMetrics
from electronics_repair_sim.models import CAPABILITY_SPECIALTY, export_config_json, validate_config
from electronics_repair_sim.rack import split_jobs_into_waiting_lines
from electronics_repair_sim.resources import create_stations, create_technicians


def get_results_folder():
    this_file = os.path.abspath(__file__)
    sim_folder = os.path.dirname(this_file)
    src_folder = os.path.dirname(sim_folder)
    project_folder = os.path.dirname(src_folder)
    results_folder = os.path.join(project_folder, "results")

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    return results_folder


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
    # return the right pair of resources based on job capability
    if job.capability == CAPABILITY_SPECIALTY:
        return specialty_tech_resource, specialty_station_resource
    return general_tech_resource, general_station_resource


def repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, preempt):
    # A production failure can jump ahead and kick a lower-priority job off its technician/station.
    while True:
        print("Time", format(env.now, ".2f") + ":", job.job_id, "pending")

        tech = None
        station = None
        work_started_at = env.now

        try:
            with tech_resource.request(priority=job.priority, preempt=preempt) as tech_req:
                yield tech_req

                with station_resource.request(priority=job.priority, preempt=preempt) as station_req:
                    yield station_req

                    tech = find_free_tech(job, technicians)
                    station = find_free_station(job, stations)

                    if job.start_time is None:
                        job.start_time = env.now

                    tech.current_job_id = job.job_id
                    station.current_job_id = job.job_id
                    work_started_at = env.now

                    print("Time", format(env.now, ".2f") + ":", job.job_id, "started on", tech.tech_id, "and", station.station_id)

                    # save this before it gets reset to 0 below
                    work_time = job.remaining_time

                    yield env.timeout(work_time)

                    job.finish_time = env.now
                    job.remaining_time = 0

                    tech.busy_time = tech.busy_time + work_time
                    station.busy_time = station.busy_time + work_time

                    print("Time", format(env.now, ".2f") + ":", job.job_id, "finished")

                    metrics.record_completed_job(job, tech, station)

                    tech.current_job_id = None
                    station.current_job_id = None
                    return

        except simpy.Interrupt:
            # a higher priority job (like a production failure) took the resource
            time_worked = env.now - work_started_at
            job.remaining_time = job.remaining_time - time_worked
            job.interrupted_count += 1

            if tech is not None:
                tech.busy_time = tech.busy_time + time_worked
                tech.current_job_id = None
            if station is not None:
                station.busy_time = station.busy_time + time_worked
                station.current_job_id = None

            print("Time", format(env.now, ".2f") + ":", job.job_id, "interrupted, remaining time", format(job.remaining_time, ".2f"))


def production_arrival_process(env, avg_interarrival_hours, rtv_probability, tech_resource, station_resource, technicians, stations, metrics, config, job_count):
    job_number = 1

    while job_number <= job_count:
        if avg_interarrival_hours > 0:
            gap = random.expovariate(1 / avg_interarrival_hours)
        else:
            gap = 0

        yield env.timeout(gap)

        job = make_production_job(job_number, rtv_probability)
        job.sim_arrival_time = env.now
        job_number += 1

        print("Time", format(env.now, ".2f") + ":", job.job_id, "new production failure arrived")

        env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, config.allow_preemption))


def run_basic_fifo_simulation(config):
    validate_config(config)

    env = simpy.Environment()

    technicians = create_technicians(config)
    stations = create_stations(config)

    # PreemptiveResource lets a higher priority job (like a production failure) take over lower priority 
    general_tech_resource = simpy.PreemptiveResource(env, capacity=config.general_technicians)
    specialty_tech_resource = simpy.PreemptiveResource(env, capacity=config.specialty_technicians)
    general_station_resource = simpy.PreemptiveResource(env, capacity=config.general_stations)
    specialty_station_resource = simpy.PreemptiveResource(env, capacity=config.specialty_stations)

    metrics = SimulationMetrics()

    jobs, avg_production_interarrival_hours, production_rtv_probability = create_all_jobs(config)
    rma_rack, direct_requests = split_jobs_into_waiting_lines(jobs)

    print("Scenario:", config.name)
    print("General technicians:", config.general_technicians)
    print("Specialty technicians:", config.specialty_technicians)
    print("General stations:", config.general_stations)
    print("Specialty stations:", config.specialty_stations)
    print("Allow preemption:", config.allow_preemption)
    print("Job limit:", config.job_limit)
    print("Direct request limit:", config.direct_request_limit)
    print("Production job count:", config.production_job_count)
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

            # only production failures are allowed to preempt other jobs
            env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, False))

    # direct requests (AdvEx, reship) are pulled in priority order
    for count in range(config.direct_request_limit):
        job = direct_requests.get_next_job()

        if job is not None:
            tech_resource, station_resource = pick_resources(
                job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource
            )

            job.sim_arrival_time = env.now

            env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, False))

    # production failures are simulated as brand new arrivals over time,
    env.process(production_arrival_process(
        env, avg_production_interarrival_hours, production_rtv_probability,
        general_tech_resource, general_station_resource, technicians, stations, metrics,
        config, config.production_job_count,
    ))

    env.run()

    print()
    metrics.print_summary(env.now)

    print_utilization(technicians, stations, env.now)

    results_folder = get_results_folder()
    file_name = config.name.replace(" ", "_")

    events_path = os.path.join(results_folder, file_name + "_events.csv")
    summary_path = os.path.join(results_folder, file_name + "_summary.json")
    config_path = os.path.join(results_folder, file_name + "_config.json")

    metrics.export_events_csv(events_path)
    metrics.export_summary_json(summary_path, technicians, stations, env.now)
    export_config_json(config, config_path)

    print("Results saved to:", results_folder)

    return metrics


def print_utilization(technicians, stations, total_sim_time):
    print("Technician utilization")
    for tech in technicians:
        # percent of the total sim time this tech was busy
        if total_sim_time > 0:
            percent_busy = (tech.busy_time / total_sim_time) * 100
        else:
            percent_busy = 0
        print(tech.tech_id + ":", format(tech.busy_time, ".2f"), "busy hours out of", format(total_sim_time, ".2f"), "(" + format(percent_busy, ".1f") + "%)")
    print()

    print("Station utilization")
    for station in stations:
        if total_sim_time > 0:
            percent_busy = (station.busy_time / total_sim_time) * 100
        else:
            percent_busy = 0
        print(station.station_id + ":", format(station.busy_time, ".2f"), "busy hours out of", format(total_sim_time, ".2f"), "(" + format(percent_busy, ".1f") + "%)")
    print()
