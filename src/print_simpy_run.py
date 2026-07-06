from electronics_repair_sim.models import ScenarioConfig
from electronics_repair_sim.simpy_runner import run_basic_fifo_simulation


def main():
    config = ScenarioConfig()
    config.name = "base run" 
    run_basic_fifo_simulation(config)


if __name__ == "__main__":
    main()
