import os

from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import get_results_folder, run_basic_fifo_simulation


def make_scenarios():
    scenarios = []

    baseline = ScenarioConfig()
    baseline.name = "base run"
    scenarios.append({"config": baseline, "purpose": "Baseline", "key_parameters": "Default values"})

    extra_general_tech = ScenarioConfig()
    extra_general_tech.name = "extra gen tech"
    extra_general_tech.general_technicians = 2
    scenarios.append({"config": extra_general_tech, "purpose": "Extra general technician", "key_parameters": "general_technicians=2"})

    extra_specialty_tech = ScenarioConfig()
    extra_specialty_tech.name = "extra spec tech"
    extra_specialty_tech.specialty_technicians = 2
    scenarios.append({"config": extra_specialty_tech, "purpose": "Extra specialty technician", "key_parameters": "specialty_technicians=2"})

    extra_general_station = ScenarioConfig()
    extra_general_station.name = "extra gen station"
    extra_general_station.general_stations = 2
    scenarios.append({"config": extra_general_station, "purpose": "Extra general station", "key_parameters": "general_stations=2"})

    extra_specialty_station = ScenarioConfig()
    extra_specialty_station.name = "extra spec station"
    extra_specialty_station.specialty_stations = 2
    scenarios.append({"config": extra_specialty_station, "purpose": "Extra specialty station", "key_parameters": "specialty_stations=2"})

    extra_everything = ScenarioConfig()
    extra_everything.name = "+1 of all"
    extra_everything.general_technicians = 2
    extra_everything.specialty_technicians = 2
    extra_everything.general_stations = 2
    extra_everything.specialty_stations = 2
    scenarios.append({
        "config": extra_everything,
        "purpose": "Extra of everything",
        "key_parameters": "general_technicians=2, specialty_technicians=2, general_stations=2, specialty_stations=2",
    })

    no_preemption = ScenarioConfig()
    no_preemption.name = "no preemption"
    no_preemption.allow_preemption = False
    scenarios.append({"config": no_preemption, "purpose": "No preemption", "key_parameters": "allow_preemption=False"})

    no_preemption_extra_specialty_tech = ScenarioConfig()
    no_preemption_extra_specialty_tech.name = "no preemption and +1 spec tech"
    no_preemption_extra_specialty_tech.allow_preemption = False
    no_preemption_extra_specialty_tech.specialty_technicians = 2
    scenarios.append({
        "config": no_preemption_extra_specialty_tech,
        "purpose": "No preemption plus extra specialty tech",
        "key_parameters": "allow_preemption=False, specialty_technicians=2",
    })

    heavier_load = ScenarioConfig()
    heavier_load.name = "more demand"
    heavier_load.job_limit = 10
    heavier_load.advex_job_count = 10
    heavier_load.reship_job_count = 10
    heavier_load.production_job_count = 10
    scenarios.append({
        "config": heavier_load,
        "purpose": "Higher job volume",
        "key_parameters": "job_limit=10, advex_job_count=10, reship_job_count=10, production_job_count=10",
    })

    heavier_load_extra_resources = ScenarioConfig()
    heavier_load_extra_resources.name = "more demand and +1 all"
    heavier_load_extra_resources.job_limit = 10
    heavier_load_extra_resources.advex_job_count = 10
    heavier_load_extra_resources.reship_job_count = 10
    heavier_load_extra_resources.production_job_count = 10
    heavier_load_extra_resources.general_technicians = 2
    heavier_load_extra_resources.specialty_technicians = 2
    heavier_load_extra_resources.general_stations = 2
    heavier_load_extra_resources.specialty_stations = 2
    scenarios.append({
        "config": heavier_load_extra_resources,
        "purpose": "Higher job volume plus extra resources",
        "key_parameters": "job_limit=10, advex_job_count=10, reship_job_count=10, production_job_count=10, all resources x2",
    })

    return scenarios


def print_run_header(run_number, name):
    title = "Run " + str(run_number) + " - " + name
    total_width = 60
    dash_count = total_width - len(title)

    if dash_count < 0:
        dash_count = 0

    left_dashes = dash_count // 2
    right_dashes = dash_count - left_dashes

    print(("-" * left_dashes) + title + ("-" * right_dashes))


def print_run_summary_table(run_records):
    print("Run ID | Purpose | Key Parameters | Duration | Status")
    print("-------------------------------------------------------")

    for record in run_records:
        print(
            record["run_number"], "|",
            record["purpose"], "|",
            record["key_parameters"], "|",
            format(record["duration_hours"], ".2f") + " hrs", "|",
            record["status"],
        )
        print()


def clear_old_results():
    results_folder = get_results_folder()
    file_names = ["config.csv", "summary.csv", "events.csv", "timeseries.csv"]

    for file_name in file_names:
        file_path = os.path.join(results_folder, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)


def run_all_scenarios():
    clear_old_results()

    scenarios = make_scenarios()
    run_records = []

    run_number = 1
    for scenario in scenarios:
        config = scenario["config"]

        print_run_header(run_number, config.name)

        status = "Complete"
        duration_hours = 0

        try:
            metrics = run_basic_fifo_simulation(config)
            duration_hours = metrics.find_last_job_finish_time()
        except Exception as error:
            status = "Error: " + str(error)

        record = {
            "run_number": run_number,
            "purpose": scenario["purpose"],
            "key_parameters": scenario["key_parameters"],
            "duration_hours": duration_hours,
            "status": status,
        }
        run_records.append(record)

        run_number += 1

    print()
    print("Run summary")
    print("-----------")
    print_run_summary_table(run_records)


if __name__ == "__main__":
    run_all_scenarios()
