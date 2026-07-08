import time

from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import run_basic_fifo_simulation


def make_scenarios():
    
    scenarios = []

    baseline = ScenarioConfig()
    baseline.name = "base run"
    scenarios.append(baseline)

    extra_general_tech = ScenarioConfig()
    extra_general_tech.name = "extra gen tech"
    extra_general_tech.general_technicians = 2
    scenarios.append(extra_general_tech)

    extra_specialty_tech = ScenarioConfig()
    extra_specialty_tech.name = "extra spec tech"
    extra_specialty_tech.specialty_technicians = 2
    scenarios.append(extra_specialty_tech)

    extra_general_station = ScenarioConfig()
    extra_general_station.name = "extra gen station"
    extra_general_station.general_stations = 2
    scenarios.append(extra_general_station)

    extra_specialty_station = ScenarioConfig()
    extra_specialty_station.name = "extra spec station"
    extra_specialty_station.specialty_stations = 2
    scenarios.append(extra_specialty_station)

    extra_everything = ScenarioConfig()
    extra_everything.name = "+1 of all"
    extra_everything.general_technicians = 2
    extra_everything.specialty_technicians = 2
    extra_everything.general_stations = 2
    extra_everything.specialty_stations = 2
    scenarios.append(extra_everything)

    no_preemption = ScenarioConfig()
    no_preemption.name = "no preemption"
    no_preemption.allow_preemption = False
    scenarios.append(no_preemption)

    no_preemption_extra_specialty_tech = ScenarioConfig()
    no_preemption_extra_specialty_tech.name = "no preemption and +1 spec tech"
    no_preemption_extra_specialty_tech.allow_preemption = False
    no_preemption_extra_specialty_tech.specialty_technicians = 2
    scenarios.append(no_preemption_extra_specialty_tech)

    heavier_load = ScenarioConfig()
    heavier_load.name = "more demand"
    heavier_load.job_limit = 10
    heavier_load.direct_request_limit = 10
    heavier_load.production_job_count = 10
    scenarios.append(heavier_load)

    heavier_load_extra_resources = ScenarioConfig()
    heavier_load_extra_resources.name = "more demand and +1 all"
    heavier_load_extra_resources.job_limit = 10
    heavier_load_extra_resources.direct_request_limit = 10
    heavier_load_extra_resources.production_job_count = 10
    heavier_load_extra_resources.general_technicians = 2
    heavier_load_extra_resources.specialty_technicians = 2
    heavier_load_extra_resources.general_stations = 2
    heavier_load_extra_resources.specialty_stations = 2
    scenarios.append(heavier_load_extra_resources)

    return scenarios


def run_all_scenarios():
    scenarios = make_scenarios()
    run_records = []

    run_number = 1
    for config in scenarios:
        print("=" * 60)
        print("Run", run_number, "-", config.name)
        print("=" * 60)

        start_time = time.time()
        status = "Complete"

        try:
            run_basic_fifo_simulation(config)
        except Exception as error:
            status = "Error: " + str(error)

        end_time = time.time()
        duration_seconds = end_time - start_time

        record = {
            "run_number": run_number,
            "name": config.name,
            "duration_seconds": duration_seconds,
            "status": status,
        }
        run_records.append(record)

        run_number += 1

    print()
    print("Run summary")
    print("-----------")
    for record in run_records:
        print(
            "Run", record["run_number"], "-", record["name"] + ":",
            format(record["duration_seconds"], ".2f"), "seconds -", record["status"],
        )


if __name__ == "__main__":
    run_all_scenarios()
