from electronics_repair_sim.models import (
    CAPABILITY_GENERAL,
    CAPABILITY_SPECIALTY,
    Station,
    Technician,
)


def create_technicians():
    # two technicians, one general and one specialty
    technicians = [
        Technician("Tech 1", CAPABILITY_GENERAL),
        Technician("Tech 2", CAPABILITY_SPECIALTY),
    ]
    return technicians


def create_stations():
    # two stations, one general and one specialty
    stations = [
        Station("Station 1", CAPABILITY_GENERAL),
        Station("Station 2", CAPABILITY_SPECIALTY),
    ]
    return stations
