from electronics_repair_sim.cli_prompts import ask_custom_parameters, ask_yes_no
from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import run_basic_fifo_simulation


def main():
    config = ScenarioConfig()
    config.name = "base run"

    if ask_yes_no("Do you want to set custom parameters"):
        config = ask_custom_parameters(config)

    run_basic_fifo_simulation(config)


if __name__ == "__main__":
    main()
