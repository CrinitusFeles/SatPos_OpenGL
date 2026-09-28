from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from skyfield.api import Loader
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time, Timescale

configs_path = Path.cwd()
load = Loader(configs_path)


def calc_path_points(tle: str,
                     t_1: datetime, t_2: datetime,
                     sampling_rate=1):
    timescale: Timescale = load.timescale()
    t_amount = int((t_2 - t_1).total_seconds() * sampling_rate)
    time_points: Time = timescale.linspace(timescale.from_datetime(t_1),
                                           timescale.from_datetime(t_2),
                                           t_amount)
    tle_strings: list[str] = tle.split('\n')
    if len(tle_strings) == 2:
        sat_name = ''
        line1 = tle_strings[1]
        line2 = tle_strings[2]
    elif len(tle_strings) >= 3:
        sat_name: str = tle_strings[0]
        line1: str = tle_strings[1]
        line2: str = tle_strings[2]
    else:
        raise ValueError(f'Incorrect amount of TLE lines {len(tle_strings)}')

    satellite: EarthSatellite = EarthSatellite(name=sat_name,
                                               line1=line1,
                                               line2=line2)
    itrf = satellite.at(time_points).itrf_xyz()  # type: ignore
    points = np.array(itrf.km.T / 6356)   # type: ignore
    rotation_matrix = np.array([
        [1,  0,  0],  # Новая X = старая X
        [0,  0,  1],  # Новая Y = старая Z (Полюс стал "Верхом")
        [0, -1,  0]   # Новая Z = старая -Y
    ])

    points_transformed = points @ rotation_matrix.T
    return points_transformed

def calc_sat():
    tle = """2025-313AK
1 67281U 25313AK  26251.71378333  .00004676  00000+0  20009-3 0  9995
2 67281  97.3822 324.8446 0013255  70.4815 289.7852 15.23220184 38661
    """
    start = datetime.now().astimezone()
    finish = start + timedelta(hours=14)
    return calc_path_points(tle, start, finish)

if __name__ == '__main__':
    print(calc_sat()[0])