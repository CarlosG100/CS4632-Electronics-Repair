from electronics_repair_sim.models import (
    CAPABILITY_GENERAL,
    CAPABILITY_SPECIALTY,
    Station,
    Technician,
)


def create_technicians(config):
    # build the list of technicians based on the scenario settings
    technicians = []
    tech_number = 1

    for count in range(config.general_technicians):
        technicians.append(Technician("Tech " + str(tech_number), CAPABILITY_GENERAL))
        tech_number += 1

    for count in range(config.specialty_technicians):
        technicians.append(Technician("Tech " + str(tech_number), CAPABILITY_SPECIALTY))
        tech_number += 1

    return technicians


def create_stations(config):
    # build the list of stations based on the scenario settings
    stations = []
    station_number = 1

    for count in range(config.general_stations):
        stations.append(Station("Station " + str(station_number), CAPABILITY_GENERAL))
        station_number += 1

    for count in range(config.specialty_stations):
        stations.append(Station("Station " + str(station_number), CAPABILITY_SPECIALTY))
        station_number += 1

    return stations
