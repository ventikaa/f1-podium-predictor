import requests
import pandas as pd
from time import sleep
from tqdm import tqdm
from datetime import datetime
from meteostat import Point, Daily
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_race_results(start_year=2000, end_year=2025):
    base_url = "https://ergast.com/api/f1"
    all_results = []

    for year in tqdm(range(start_year, end_year + 1), desc="Fetching race results"):
        try:
            r = requests.get(f"{base_url}/{year}.json?limit=1000", timeout=10)
            r.raise_for_status()
            year_data = r.json()

            if 'MRData' not in year_data or 'RaceTable' not in year_data['MRData']:
                print(f"Warning: Unexpected API response structure for year {year}")
                continue

            rounds = year_data['MRData']['RaceTable']['Races']

            for race in rounds:
                try:
                    round_num = race['round']
                    race_date = race['date']
                    circuit = race['Circuit']
                    circuit_name = circuit['circuitName']
                    location = circuit['Location']['locality']
                    country = circuit['Location']['country']

                    results_url = f"{base_url}/{year}/{round_num}/results.json?limit=100"
                    res = requests.get(results_url, timeout=10)
                    try:
                        res_json = res.json()
                    except ValueError:
                        clean_text = re.sub(r'\\[^"\\/bfnrtu]', '', res.text)
                        res_json = json.loads(clean_text)

                    sleep(0.25)

                    if 'MRData' not in res_json or 'RaceTable' not in res_json['MRData']:
                        continue

                    races = res_json['MRData']['RaceTable']['Races']
                    if not races:
                        continue

                    # For each race result
                    for result in races[0]['Results']:
                        driver = result['Driver']
                        constructor = result['Constructor']

                        position = None
                        if isinstance(result['position'], str) and result['position'].isdigit():
                            position = int(result['position'])

                        grid = int(result.get('grid', -1))  # starting grid position
                        qual_position = int(result.get('QualifyingPosition', -1))  # placeholder for qualifying, will overwrite later
                        dnf = result.get('status', '').lower() != 'finished'
                        pit_stops = 0  # placeholder, will overwrite later

                        all_results.append({
                            "year": int(year),
                            "round": int(round_num),
                            "circuit": circuit_name,
                            "location": location,
                            "country": country,
                            "date": race_date,
                            "driver": f"{driver['givenName']} {driver['familyName']}",
                            "constructor": constructor['name'],
                            "position": position,
                            "grid": grid,
                            "qualifying_position": qual_position,
                            "dnf": dnf,
                            "pit_stops": pit_stops
                        })
                except Exception as race_error:
                    print(f"Error processing race {round_num} in {year}: {race_error}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Request failed for year {year}: {e}")
            continue
        except Exception as year_error:
            print(f"Error processing year {year}: {year_error}")
            continue

    return pd.DataFrame(all_results)

def get_circuit_coordinates():
    return {
        "Albert Park Grand Prix Circuit": (-37.8497, 144.968),
        "Autódromo Internacional do Algarve": (37.227, -8.6267),
        "Autódromo José Carlos Pace": (-23.7036, -46.6997),
        "Bahrain International Circuit": (26.0325, 50.5106),
        "Baku City Circuit": (40.3725, 49.8533),
        "Circuit de Barcelona-Catalunya": (41.57, 2.26111),
        "Circuit de Monaco": (43.7347, 7.42056),
        "Circuit de Spa-Francorchamps": (50.4372, 5.97139),
        "Circuit Gilles Villeneuve": (45.5, -73.5228),
        "Circuit of the Americas": (30.1328, -97.6411),
        "Hockenheimring": (49.3307, 8.56583),
        "Hungaroring": (47.5819, 19.2486),
        "Istanbul Park": (40.9517, 29.405),
        "Jeddah Corniche Circuit": (21.6319, 39.1044),
        "Las Vegas Strip Circuit": (36.1147, -115.172),
        "Marina Bay Street Circuit": (1.2914, 103.864),
        "Miami International Autodrome": (25.9581, -80.2389),
        "Circuit de Nevers Magny-Cours": (46.8642, 3.16361),
        "Nürburgring": (50.3356, 6.9475),
        "Red Bull Ring": (47.2197, 14.7647),
        "Autodromo Internazionale del Mugello": (43.9975, 11.3719),
        "Autodromo Enzo e Dino Ferrari": (44.3439, 11.7167),
        "Circuit Paul Ricard": (43.2506, 5.79167),
        "Shanghai International Circuit": (31.3389, 121.22),
        "Silverstone Circuit": (52.0786, -1.01694),
        "Suzuka Circuit": (34.8431, 136.541),
        "Yas Marina Circuit": (24.4672, 54.6031),
        "Zandvoort": (52.3888, 4.54092),
        "Circuit Zolder": (50.9894, 5.25694),
        "Sepang International Circuit": (2.76083, 101.738),
        "Sochi Autodrom": (43.4057, 39.9578),
        "Korean International Circuit": (34.7333, 126.417),
        "Buddh International Circuit": (28.3487, 77.5331),
        "Indianapolis Motor Speedway": (39.795, -86.2347)
    }

def fetch_weather_data(lat, lon, date):
    retry_count = 3
    for _ in range(retry_count):
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            point = Point(lat, lon)
            data = Daily(point, date_obj, date_obj)
            data = data.fetch()

            if not data.empty:
                row = data.iloc[0]
                return (
                    row.get('tavg', None),
                    row.get('rhum', None),
                    row.get('wspd', None),
                    row.get('prcp', None)
                )
        except Exception as e:
            print(f"Weather retry error for {date} at {lat},{lon}: {e}")
            sleep(1)
    return None, None, None, None

def get_driver_id(full_name):
    parts = full_name.lower().split()
    if len(parts) == 2:
        return parts[1]
    return full_name.lower().replace(" ", "_")

def fetch_driver_stats(driver_name):
    try:
        driver_id = get_driver_id(driver_name)
        url = f"https://ergast.com/api/f1/drivers/{driver_id}/results.json?limit=1000"
        res = requests.get(url, timeout=10)
        sleep(0.25)
        try:
            data = res.json()
        except ValueError:
            clean_text = re.sub(r'\\[^"\\/bfnrtu]', '', res.text)
            data = json.loads(clean_text)

        races = data['MRData']['RaceTable']['Races']
        podiums = 0
        wins = 0

        for race in races:
            for result in race.get('Results', []):
                pos = result.get('position', '')
                if pos.isdigit():
                    position = int(pos)
                    if position <= 3:
                        podiums += 1
                    if position == 1:
                        wins += 1

        return {"podiums": podiums, "wins": wins}
    except Exception as e:
        print(f"Error fetching stats for {driver_name}: {e}")
        return {"podiums": 0, "wins": 0}

def fetch_constructor_stats(constructor_name):
    try:
        constructor_id = constructor_name.lower().replace(" ", "_")
        url = f"https://ergast.com/api/f1/constructors/{constructor_id}/results.json?limit=1000"
        res = requests.get(url, timeout=10)
        sleep(0.25)
        try:
            data = res.json()
        except ValueError:
            clean_text = re.sub(r'\\[^"\\/bfnrtu]', '', res.text)
            data = json.loads(clean_text)

        races = data['MRData']['RaceTable']['Races']
        podiums = 0
        wins = 0

        for race in races:
            for result in race.get('Results', []):
                pos = result.get('position', '')
                if pos.isdigit():
                    position = int(pos)
                    if position <= 3:
                        podiums += 1
                    if position == 1:
                        wins += 1

        return {"podiums": podiums, "wins": wins}
    except Exception as e:
        print(f"Error fetching stats for {constructor_name}: {e}")
        return {"podiums": 0, "wins": 0}

def enrich_row(row, circuit_coords):
    try:
        circuit = row['circuit']
        lat, lon = circuit_coords.get(circuit, (None, None))

        temp_c, humidity, wind_speed, precip_mm = (None, None, None, None)
        if lat and lon:
            temp_c, humidity, wind_speed, precip_mm = fetch_weather_data(lat, lon, row['date'])

        driver_stats = fetch_driver_stats(row['driver'])
        constructor_stats = fetch_constructor_stats(row['constructor'])

        return {
            "year": row['year'],
            "round": row['round'],
            "driver": row['driver'],
            "constructor": row['constructor'],
            "circuit": circuit,
            "location": row['location'],
            "country": row['country'],
            "date": row['date'],
            "position": row['position'],
            "grid": row.get("grid", None),
            "qualifying_position": row.get("qualifying_position", None),
            "dnf": row.get("dnf", False),
            "pit_stops": row.get("pit_stops", 0),
            "temperature": temp_c,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation": precip_mm,
            "driver_podiums": driver_stats['podiums'],
            "constructor_podiums": constructor_stats['podiums'],
            "driver_wins": driver_stats['wins'],
            "constructor_wins": constructor_stats['wins']
        }
    except Exception as e:
        print(f"❌ Error enriching row: {e}")
        return None

def build_master_dataset(start_year=2000, end_year=2025):
    print("🔄 Starting data collection...")

    checkpoint_file = "progress_checkpoint.csv"
    race_results = fetch_race_results(start_year, end_year)
    if race_results.empty:
        raise ValueError("No race results were fetched. Check API connectivity.")

    circuit_coords = get_circuit_coordinates()
    all_data = []

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(enrich_row, row, circuit_coords): idx
            for idx, row in race_results.iterrows()
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Enriching"):
            result = future.result()
            if result:
                all_data.append(result)

    df = pd.DataFrame(all_data)

    output_paths = [
        "data/f1_master_dataset.csv",
        "f1_master_dataset.csv",
        os.path.expanduser("~/f1_master_dataset.csv")
    ]

    saved = False
    for path in output_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df.to_csv(path, index=False)
            print(f"✅ Successfully saved to {os.path.abspath(path)}")
            saved = True
            break
        except Exception as e:
            print(f"⚠️ Could not save to {path}: {e}")

    if not saved:
        raise Exception("Failed to save CSV to all attempted locations")

    return df

if __name__ == "__main__":
    try:
        master_df = build_master_dataset(2000, 2023)
        print("Data collection complete!")
        print(f"Total records collected: {len(master_df)}")
    except Exception as e:
        print(f"❌ Script failed: {e}")