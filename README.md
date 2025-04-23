# 🏎️ F1 Podium Predictor

A machine learning web app that predicts Formula 1 podium finishers (🥇🥈🥉) based on historical race data, qualifying results, weather conditions, and team/driver performance.

## 🔍 Features
- Predicts top 3 podium finishers for any F1 race (2000–2025)
- CatBoost model trained on a custom dataset with:
  - Qualifying position, grid, DNF, pit stops
  - Weather: temperature, humidity, wind, precipitation
  - Driver & constructor stats (podiums, wins)
- Clean Streamlit frontend with red/black racing UI
- Driver images, team logos, and stylish podium visuals
- Deployed live on Streamlit Cloud

## 🛠️ Tech Stack
- **Frontend**: Streamlit (custom themed)
- **Model**: CatBoostClassifier
- **Data**: Ergast API + Meteostat + manual mappings
- **Deployment**: Streamlit Cloud

