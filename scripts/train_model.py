import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import shap
import matplotlib.pyplot as plt
import os
import joblib 

# Load dataset
df = pd.read_csv("C:/Users/avant/OneDrive/Desktop/f1-podium-predictor/f1_master_dataset.csv")

# Drop rows with missing target or essential info
df.dropna(subset=["position"], inplace=True)

# Convert target to binary (1 = podium, 0 = not podium)
df["podium"] = df["position"].apply(lambda x: 1 if x <= 3 else 0)

# Features to use
features = [
    "year", "round", "grid", "qualifying_position", "dnf", "pit_stops",
    "temperature", "humidity", "wind_speed", "precipitation",
    "driver_podiums", "constructor_podiums", "driver_wins", "constructor_wins"
]

# Optional: convert categorical identifiers if you want (not used for CatBoost but useful for exploration)
cat_features = []  # All features above are numeric or ordinal

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    df[features], df["podium"], test_size=0.2, random_state=42, stratify=df["podium"]
)

# Create CatBoost pool
train_pool = Pool(X_train, y_train, cat_features=cat_features)
test_pool = Pool(X_test, y_test, cat_features=cat_features)

# Train model
model = CatBoostClassifier(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    loss_function="Logloss",
    eval_metric="AUC",
    early_stopping_rounds=50,
    verbose=100
)
model.fit(train_pool, eval_set=test_pool)

# Evaluate
y_pred = model.predict(X_test)
print("\n🔍 Classification Report:")
print(classification_report(y_test, y_pred))
print("✅ Accuracy:", accuracy_score(y_test, y_pred))
print("📉 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# SHAP explainability
explainer = shap.Explainer(model)
shap_values = explainer(X_test)
os.makedirs("models", exist_ok=True)

# Save as CatBoost binary model
model.save_model("models/catboost_podium_model.cbm")

# Optionally, save as joblib for use with joblib.load()
joblib.dump(model, "models/catboost_podium_model.pkl")

print("✅ Model saved to models/ directory")

print("\n📊 SHAP summary plot:")
shap.summary_plot(shap_values, X_test)
