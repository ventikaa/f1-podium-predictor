import requests
import pandas as pd
from time import sleep
from tqdm import tqdm

def fetch_race_results(start_year=2000, end_year=2025):
    base_url = "https://ergast.com/api/f1"
    all_results = []

    for year in tqdm(range(start_year, end_year + 1), desc="Fetching data for years"):
        r = requests.get(f"{base_url}/{year}.json?limit=1000")
        rounds = r.json()['MRData']['RaceTable']['Races']
        
        for race in rounds:
            round_num = race['round']
            race_date = race['date']
            circuit = race['Circuit']
            circuit_name = circuit['circuitName']
            location = circuit['Location']['locality']
            country = circuit['Location']['country']

            results_url = f"{base_url}/{year}/{round_num}/results.json?limit=100"
            res = requests.get(results_url).json()
            sleep(0.25)  # to avoid rate limiting

            races = res['MRData']['RaceTable']['Races']
            if not races:
                continue

            for result in races[0]['Results']:
                driver = result['Driver']
                constructor = result['Constructor']

                all_results.append({
                    "year": int(year),
                    "round": int(round_num),
                    "circuit": circuit_name,
                    "location": location,
                    "country": country,
                    "date": race_date,
                    "driver": f"{driver['givenName']} {driver['familyName']}",
                    "constructor": constructor['name'],
                    "position": int(result['position']) if result['position'].isdigit() else None
                })

        # Save periodically (every 50 races)
        if len(all_results) % 50 == 0:
            pd.DataFrame(all_results).to_csv("core_results_progress.csv", index=False)
            print(f"✅ Saved progress with {len(all_results)} records")

    # Save final dataset after all data is fetched
    df = pd.DataFrame(all_results)
    df.to_csv("core_results.csv", index=False)
    print("✅ Race results saved to data/core_results.csv")

if __name__ == "__main__":
    fetch_race_results()
