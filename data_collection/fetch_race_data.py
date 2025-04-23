import requests
import pandas as pd
from tqdm import tqdm
import time

def fetch_race_results(start_year=2000, end_year=2025):
    all_data = []

    for year in tqdm(range(start_year, end_year + 1)):
        for round_num in range(1, 23):  # Typical max rounds; will skip if not found
            url = f"https://ergast.com/api/f1/{year}/{round_num}/results.json?limit=1000"
            res = requests.get(url)
            if res.status_code != 200:
                continue

            race_data = res.json()['MRData']['RaceTable']['Races']
            if not race_data:
                continue

            race = race_data[0]
            circuit = race['Circuit']
            for result in race['Results']:
                driver = result['Driver']
                constructor = result['Constructor']
                all_data.append({
                    "year": int(year),
                    "round": int(race['round']),
                    "date": race["date"],
                    "circuit_id": circuit['circuitId'],
                    "circuit_name": circuit['circuitName'],
                    "location": circuit['Location']['locality'],
                    "country": circuit['Location']['country'],
                    "driver": f"{driver['givenName']} {driver['familyName']}",
                    "driver_id": driver['driverId'],
                    "constructor": constructor['name'],
                    "constructor_id": constructor['constructorId'],
                    "position": int(result['position']),
                    "grid": int(result['grid']),
                    "status": result['status']
                })

            time.sleep(0.25)  # To respect API rate limits

    df = pd.DataFrame(all_data)
    df.to_csv("data/base_race_results.csv", index=False)
    print("✅ Base race results saved to data/base_race_results.csv")

if __name__ == "__main__":
    fetch_race_results()
