import streamlit as st
import pandas as pd
import joblib
import numpy as np

# Load model and dataset
model = joblib.load("scripts/models/catboost_podium_model.pkl")
dataset = pd.read_csv("f1_master_dataset.csv")

# Driver image and team logo maps (example)
driver_images = {
    "Max Verstappen": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Max_Verstappen_2023.jpg",
    "Lewis Hamilton": "https://upload.wikimedia.org/wikipedia/commons/8/86/Lewis_Hamilton_2023.jpg",
    "Charles Leclerc": "https://upload.wikimedia.org/wikipedia/commons/3/34/Charles_Leclerc_2023.jpg",
    # Add more drivers as needed
}

constructor_logos = {
    "Red Bull": "https://upload.wikimedia.org/wikipedia/en/0/01/Red_Bull_Racing_logo.svg",
    "Mercedes": "https://upload.wikimedia.org/wikipedia/commons/5/58/Mercedes-Benz_star_2022.svg",
    "Ferrari": "https://upload.wikimedia.org/wikipedia/en/d/d2/Scuderia_Ferrari_Logo.svg",
    # Add more constructors as needed
}

# Extend year range to include 2025
all_years = sorted(dataset['year'].unique().tolist() + [2025], reverse=True)

# Theme styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', system-ui, sans-serif;
        background-color: #000;
        color: #fff;
    }
    .main-title {
        color: #ff0000;
        text-align: center;
        font-size: 3em;
        margin-bottom: 0.5em;
    }
    .podium-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("""<div class='main-title'>F1 Podium Predictor 🏁</div>""", unsafe_allow_html=True)
st.markdown("Predict whether a driver will finish on the podium for a given race.")

# Inputs
col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("Select Year", all_years)
with col2:
    rounds_available = sorted(dataset[dataset['year'] == selected_year]['round'].unique()) if selected_year in dataset['year'].values else list(range(1, 24))
    selected_round = st.selectbox("Select Round", rounds_available)

# Filter race data
race_df = dataset[(dataset['year'] == selected_year) & (dataset['round'] == selected_round)]

if race_df.empty:
    st.warning("No historical race data available for this selection.")
    st.stop()

# Predict
if st.button("🚦 Predict Podium"):
    with st.spinner("Predicting podium finishers..."):
        features = [
            'year', 'round', 'grid', 'qualifying_position', 'dnf', 'pit_stops',
            'temperature', 'humidity', 'wind_speed', 'precipitation',
            'driver_podiums', 'constructor_podiums', 'driver_wins', 'constructor_wins'
        ]
        X = race_df[features]
        preds = model.predict(X)
        race_df['podium_pred'] = preds

        podium_df = race_df[race_df['podium_pred'] == 1].sort_values(by='qualifying_position').head(3)

        if len(podium_df) < 3:
            st.error(f"Only {len(podium_df)} podium finishers predicted. Try tuning or adding more data.")
        else:
            st.success("🏁 Predicted Podium")
            podium_icons = ['🥇', '🥈', '🥉']
            for i, row in podium_df.reset_index(drop=True).iterrows():
                driver_img = driver_images.get(row['driver'], f"https://via.placeholder.com/80x80?text={row['driver'].split()[-1]}")
                constructor_logo = constructor_logos.get(row['constructor'], f"https://via.placeholder.com/100x40?text={row['constructor'].split()[0]}")

                st.markdown(f"""
                    <div class='podium-card'>
                        <h3>{podium_icons[i]} Position {i+1}</h3>
                        <img src="{driver_img}" alt="driver" style="border-radius: 50%; height: 80px; width: 80px;"><br>
                        <strong>{row['driver']}</strong><br>
                        <img src="{constructor_logo}" alt="team logo" style="margin: 10px 0; max-height: 50px;"><br>
                        <em>{row['constructor']}</em><br>
                        Qualifying: {row['qualifying_position']} | Grid: {row['grid']}
                    </div>
                """, unsafe_allow_html=True)
