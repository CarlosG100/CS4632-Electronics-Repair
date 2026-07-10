import os
import random
from datetime import datetime

import simpy

from electronics_repair_sim.create_jobs import build_all_job_models, make_production_job, make_reship_job, make_synthetic_job
from electronics_repair_sim.metrics import SimulationMetrics
from electronics_repair_sim.models import CAPABILITY_SPECIALTY, SOURCE_ADVEX, SOURCE_RESHIP, SOURCE_RMA, export_config_csv, format_sim_time_as_day_time, validate_config
from electronics_repair_sim.resources import create_stations, create_technicians


HOURS_PER_DAY = 24
BUSINESS_START_HOUR = 7.0
BUSINESS_END_HOUR = 15.5
LAST_BUSINESS_DAY = 4


def is_business_hours(sim_time):
    day_number = int(sim_time // HOURS_PER_DAY) % 7
    hour_of_day = sim_time % HOURS_PER_DAY

    if day_number > LAST_BUSINESS_DAY:
        return False
    if hour_of_day < BUSINESS_START_HOUR or hour_of_day >= BUSINESS_END_HOUR:
        return False
    return True


def get_business_end_of_day(sim_time):
    day_number = int(sim_time // HOURS_PER_DAY)
    return (day_number * HOURS_PER_DAY) + BUSINESS_END_HOUR


def get_next_business_start(sim_time):
    day_number = int(sim_time // HOURS_PER_DAY)

    for day_offset in range(0, 8):
        candidate_day = day_number + day_offset
        day_of_week = candidate_day % 7

        if day_of_week <= LAST_BUSINESS_DAY:
            candidate_start = (candidate_day * HOURS_PER_DAY) + BUSINESS_START_HOUR
            if candidate_start >= sim_time:
                return candidate_start

    return sim_time


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


def get_resource_priority(job):
    if job.source == SOURCE_RMA:
        return 1
    return 0


def repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, preempt):
    while True:
        if not is_business_hours(env.now):
            wait_hours = get_next_business_start(env.now) - env.now
            yield env.timeout(wait_hours)
            continue

        print("Time", format(env.now, ".2f") + ":", job.job_id, "pending")

        tech = None
        station = None
        started_this_attempt = False
        resource_priority = get_resource_priority(job)

        try:
            with tech_resource.request(priority=resource_priority, preempt=preempt) as tech_req:
                yield tech_req

                with station_resource.request(priority=resource_priority, preempt=preempt) as station_req:
                    yield station_req

                    tech = find_free_tech(job, technicians)
                    station = find_free_station(job, stations)

                    if job.start_time is None:
                        job.start_time = env.now

                    tech.current_job_id = job.job_id
                    station.current_job_id = job.job_id
                    started_this_attempt = True

                    print("Time", format(env.now, ".2f") + ":", job.job_id, "started on", tech.tech_id, "and", station.station_id)
                    metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "started", tech.tech_id, station.station_id)

                    while job.remaining_time > 0:
                        if not is_business_hours(env.now):
                            wait_hours = get_next_business_start(env.now) - env.now
                            yield env.timeout(wait_hours)
                            continue

                        hours_left_today = get_business_end_of_day(env.now) - env.now
                        chunk = min(job.remaining_time, hours_left_today)

                        yield env.timeout(chunk)

                        job.remaining_time = job.remaining_time - chunk
                        tech.busy_time = tech.busy_time + chunk
                        station.busy_time = station.busy_time + chunk

                        if job.remaining_time > 0:
                            wait_hours = get_next_business_start(env.now) - env.now
                            print("Time", format(env.now, ".2f") + ":", job.job_id, "paused for the day, remaining time", format(job.remaining_time, ".2f"))
                            metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "paused", tech.tech_id, station.station_id, job.remaining_time)
                            yield env.timeout(wait_hours)

                    job.finish_time = env.now

                    print("Time", format(env.now, ".2f") + ":", job.job_id, "finished")

                    metrics.record_completed_job(job, tech, station)

                    tech.current_job_id = None
                    station.current_job_id = None
                    return

        except simpy.Interrupt:
            # a higher priority job (like a production failure) took the resource
            job.interrupted_count += 1

            if started_this_attempt:
                tech_id = ""
                station_id = ""

                if tech is not None:
                    tech_id = tech.tech_id
                    tech.current_job_id = None
                if station is not None:
                    station_id = station.station_id
                    station.current_job_id = None

                print("Time", format(env.now, ".2f") + ":", job.job_id, "interrupted, remaining time", format(job.remaining_time, ".2f"))
                metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "interrupted", tech_id, station_id, job.remaining_time)
            else:
                print("Time", format(env.now, ".2f") + ":", job.job_id, "bumped before it could start")
                metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "bumped", remaining_time=job.remaining_time)


def synthetic_job_arrival_process(env, model, id_prefix, source, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource, technicians, stations, metrics, preempt, job_count):
    job_number = 1
    avg_interarrival_hours = model["avg_interarrival_hours"]

    while job_number <= job_count:
        if avg_interarrival_hours > 0:
            gap = random.expovariate(1 / avg_interarrival_hours)
        else:
            gap = 0

        yield env.timeout(gap)

        if not is_business_hours(env.now):
            wait_hours = get_next_business_start(env.now) - env.now
            yield env.timeout(wait_hours)

        job = make_synthetic_job(job_number, id_prefix, source, model)
        job.sim_arrival_time = env.now
        job_number += 1

        tech_resource, station_resource = pick_resources(
            job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource
        )

        print("Time", format(env.now, ".2f") + ":", job.job_id, "arrived")
        metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "arrived")

        env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, preempt))


def reship_arrival_process(env, model, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource, technicians, stations, metrics, preempt, job_count):
    job_number = 1
    avg_interarrival_hours = model["avg_interarrival_hours"]

    while job_number <= job_count:
        if avg_interarrival_hours > 0:
            gap = random.expovariate(1 / avg_interarrival_hours)
        else:
            gap = 0

        yield env.timeout(gap)

        if not is_business_hours(env.now):
            wait_hours = get_next_business_start(env.now) - env.now
            yield env.timeout(wait_hours)

        job = make_reship_job(job_number, model)
        job.sim_arrival_time = env.now
        job_number += 1

        tech_resource, station_resource = pick_resources(
            job, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource
        )

        print("Time", format(env.now, ".2f") + ":", job.job_id, "arrived")
        metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "arrived")

        env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, preempt))


def production_arrival_process(env, avg_interarrival_hours, rtv_probability, tech_resource, station_resource, technicians, stations, metrics, config, job_count):
    job_number = 1

    while job_number <= job_count:
        if avg_interarrival_hours > 0:
            gap = random.expovariate(1 / avg_interarrival_hours)
        else:
            gap = 0

        yield env.timeout(gap)

        if not is_business_hours(env.now):
            wait_hours = get_next_business_start(env.now) - env.now
            yield env.timeout(wait_hours)

        job = make_production_job(job_number, rtv_probability)
        job.sim_arrival_time = env.now
        job_number += 1

        print("Time", format(env.now, ".2f") + ":", job.job_id, "new production failure arrived")
        metrics.record_event(env.now, format_sim_time_as_day_time(env.now), job.job_id, job.source, "arrived")

        env.process(repair_job(env, job, tech_resource, station_resource, technicians, stations, metrics, config.allow_preemption))


def watch_queues(env, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource, technicians, stations, metrics, gap_hours, limit):
    checks_done = 0

    while checks_done < limit:
        techs_busy = 0
        techs_idle = 0
        for tech in technicians:
            if tech.current_job_id is None:
                techs_idle = techs_idle + 1
            else:
                techs_busy = techs_busy + 1

        stations_busy = 0
        stations_idle = 0
        for station in stations:
            if station.current_job_id is None:
                stations_idle = stations_idle + 1
            else:
                stations_busy = stations_busy + 1

        tech_queue_length = len(general_tech_resource.queue) + len(specialty_tech_resource.queue)
        station_queue_length = len(general_station_resource.queue) + len(specialty_station_resource.queue)

        metrics.add_queue_snapshot(
            env.now,
            format_sim_time_as_day_time(env.now),
            tech_queue_length,
            station_queue_length,
            techs_busy,
            techs_idle,
            stations_busy,
            stations_idle,
        )

        checks_done = checks_done + 1
        yield env.timeout(gap_hours)


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

    rma_model, advex_model, reship_model, production_avg_interarrival_hours, production_rtv_probability = build_all_job_models(config)

    print("Scenario:", config.name)
    print("General technicians:", config.general_technicians)
    print("Specialty technicians:", config.specialty_technicians)
    print("General stations:", config.general_stations)
    print("Specialty stations:", config.specialty_stations)
    print("Allow preemption:", config.allow_preemption)
    print("RMA job limit:", config.job_limit)
    print("AdvEx job count:", config.advex_job_count)
    print("Reship job count:", config.reship_job_count)
    print("Production job count:", config.production_job_count)
    print()

    env.process(synthetic_job_arrival_process(
        env, rma_model, "RMA", SOURCE_RMA,
        general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
        technicians, stations, metrics, False, config.job_limit,
    ))

    env.process(synthetic_job_arrival_process(
        env, advex_model, "ADVEX", SOURCE_ADVEX,
        general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
        technicians, stations, metrics, config.allow_preemption, config.advex_job_count,
    ))

    env.process(reship_arrival_process(
        env, reship_model,
        general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
        technicians, stations, metrics, config.allow_preemption, config.reship_job_count,
    ))

    env.process(production_arrival_process(
        env, production_avg_interarrival_hours, production_rtv_probability,
        general_tech_resource, general_station_resource, technicians, stations, metrics,
        config, config.production_job_count,
    ))

    env.process(watch_queues(
        env, general_tech_resource, specialty_tech_resource, general_station_resource, specialty_station_resource,
        technicians, stations, metrics, config.snapshot_gap_hours, config.snapshot_limit,
    ))

    env.run()

    total_sim_time = metrics.find_last_job_finish_time()

    print()
    metrics.print_summary(total_sim_time)

    print_utilization(technicians, stations, total_sim_time)

    results_folder = get_results_folder()

    generated_at = datetime.now().isoformat()

    events_path = os.path.join(results_folder, "events.csv")
    summary_path = os.path.join(results_folder, "summary.csv")
    config_path = os.path.join(results_folder, "config.csv")
    timeseries_path = os.path.join(results_folder, "time.csv")

    metrics.export_events_csv(events_path, config.name, generated_at)
    metrics.export_summary_csv(summary_path, technicians, stations, total_sim_time, config.name, generated_at)
    export_config_csv(config, config_path, generated_at)
    metrics.save_queue_history_csv(timeseries_path, config.name, generated_at)

    print("Results saved to:", ".\\results")

    return metrics


def print_utilization(technicians, stations, total_sim_time):
    print("Tech utilization")
    for tech in technicians:
        # percent of the total sim time this tech was used
        if total_sim_time > 0:
            percent_used = (tech.busy_time / total_sim_time) * 100
        else:
            percent_used = 0
        print(tech.tech_id + ":", format(tech.busy_time, ".2f"), "hrs used out of", format(total_sim_time, ".2f"), "hrs", "(" + format(percent_used, ".1f") + "%)")
    print()

    print("Station utilization")
    for station in stations:
        if total_sim_time > 0:
            percent_used = (station.busy_time / total_sim_time) * 100
        else:
            percent_used = 0
        print(station.station_id + ":", format(station.busy_time, ".2f"), "hrs used out of", format(total_sim_time, ".2f"), "hrs", "(" + format(percent_used, ".1f") + "%)")
    print()
