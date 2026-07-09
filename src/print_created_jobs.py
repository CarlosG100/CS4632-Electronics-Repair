from electronics_repair_sim.create_jobs import build_all_job_models
from electronics_repair_sim.models import ScenarioConfig


def print_job_model(title, model):
    print(title)
    print("Average interarrival hours:", format(model["avg_interarrival_hours"], ".2f"))
    print("General fraction:", format(model["general_fraction"], ".4f"))
    print("General avg service hours:", format(model["general_avg_service_time"], ".2f"))
    print("Specialty avg service hours:", format(model["specialty_avg_service_time"], ".2f"))
    print("General outcome counts:", model["general_outcome_counts"])
    print("Specialty outcome counts:", model["specialty_outcome_counts"])
    print("Priority counts:", model["priority_counts"])
    print()


def main():
    config = ScenarioConfig()
    rma_model, advex_model, reship_model, production_avg_interarrival_hours, production_rtv_probability = build_all_job_models(config)

    print_job_model("Customer RMA model", rma_model)
    print_job_model("AdvEx model", advex_model)
    print_job_model("Reship model", reship_model)

    print("Production failure model")
    print("Average interarrival hours:", format(production_avg_interarrival_hours, ".2f"))
    print("RTV probability:", format(production_rtv_probability, ".4f"))
    print()


if __name__ == "__main__":
    main()
