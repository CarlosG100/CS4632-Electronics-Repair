from electronics_repair_sim.csv_parser import load_all_csv_data
from electronics_repair_sim.job_rules import (
    get_outcome_value,
    get_priority_value,
    get_source_from_rma_type,
    is_direct_request,
    is_rma_rack_job,
)


def main():
    # Show how CSV values map into simulation rules.
    rma_parents, rma_units, production_jobs = load_all_csv_data()

    print()
    print("Priority numbers:")
    print("ASAP ", get_priority_value("ASAP"))
    print("Critical ", get_priority_value("Critical"))
    print("Normal ", get_priority_value("Normal"))

    print()
    print("Sources:")
    print("AdvEx =", get_source_from_rma_type("AdvEx"))
    print("Reship =", get_source_from_rma_type("Reship"))
    print("Repair & Return =", get_source_from_rma_type("Repair & Return"))

    print()
    print("Queue check:")
    advex_source = get_source_from_rma_type("AdvEx")
    rma_source = get_source_from_rma_type("Repair & Return")
    print("AdvEx is direct request:", is_direct_request(advex_source))
    print("Repair & Return is RMA rack job:", is_rma_rack_job(rma_source))


if __name__ == "__main__":
    main()
