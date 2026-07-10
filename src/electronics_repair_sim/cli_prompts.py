def ask_yes_no(question):
    answer = input(question + " (y/n): ").strip().lower()
    return answer == "y" or answer == "yes"


def ask_for_text(prompt, default_value):
    text = input(prompt + " [" + str(default_value) + "]: ").strip()

    if text == "":
        return default_value

    return text


def ask_for_int(prompt, default_value):
    text = input(prompt + " [" + str(default_value) + "]: ").strip()

    if text == "":
        return default_value

    return int(text)


def ask_for_float(prompt, default_value):
    text = input(prompt + " [" + str(default_value) + "]: ").strip()

    if text == "":
        return default_value

    return float(text)


def ask_custom_parameters(config):
    print()
    print("Enter a value for each parameter, or press Enter to keep the default.")

    config.name = ask_for_text("Scenario name", config.name)
    config.general_technicians = ask_for_int("General Techs", config.general_technicians)
    config.specialty_technicians = ask_for_int("Specialty Techs", config.specialty_technicians)
    config.general_stations = ask_for_int("General stations", config.general_stations)
    config.specialty_stations = ask_for_int("Specialty stations", config.specialty_stations)
    config.job_limit = ask_for_int("Customer RMA jobs", config.job_limit)
    config.advex_job_count = ask_for_int("AdvEx jobs", config.advex_job_count)
    config.reship_job_count = ask_for_int("Reship jobs", config.reship_job_count)
    config.production_job_count = ask_for_int("Production jobs", config.production_job_count)
    config.random_seed = ask_for_int("Random seed", config.random_seed)
    config.snapshot_gap_hours = ask_for_float("Snapshot gap hours", config.snapshot_gap_hours)
    config.snapshot_limit = ask_for_int("Snapshot limit", config.snapshot_limit)
    config.allow_preemption = ask_yes_no("Allow preemption")

    print()

    return config
