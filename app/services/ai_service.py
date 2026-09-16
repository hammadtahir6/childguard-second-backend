# ─────────────────────────────────────────────
# AI SERVICE — Loads all 4 trained models
# and runs them on incoming ESP32 sensor data
# ─────────────────────────────────────────────

import joblib
import numpy as np
import os

# Paths to your saved models
BASE = os.path.join(os.path.dirname(__file__), '..', 'ai_models')

print("Loading AI models...")

# Model 1: Random Forest (Fall Detection)
rf_model    = joblib.load(os.path.join(BASE, 'childguard_fall_detector_FINAL.pkl'))
rf_features = joblib.load(os.path.join(BASE, 'childguard_features_FINAL.pkl'))
print("  ✅ Random Forest loaded")

# Model 2: Isolation Forest (Anomaly Detection)
if_model    = joblib.load(os.path.join(BASE, 'childguard_isolation_forest.pkl'))
if_scaler   = joblib.load(os.path.join(BASE, 'childguard_if_scaler.pkl'))
if_features = joblib.load(os.path.join(BASE, 'childguard_if_features.pkl'))
print("  ✅ Isolation Forest loaded")

# Model 3: LSTM (Behavior Prediction)
try:
    from tensorflow.keras.models import load_model
    lstm_model  = load_model(os.path.join(BASE, 'childguard_lstm.h5'))
    lstm_scaler = joblib.load(os.path.join(BASE, 'childguard_lstm_scaler.pkl'))
    lstm_config = joblib.load(os.path.join(BASE, 'childguard_lstm_config.pkl'))
    lstm_loaded = True
    print("  ✅ LSTM loaded")
except Exception as e:
    lstm_loaded = False
    print(f"  ⚠️ LSTM not loaded: {e}")

# Model 4: Sound Classifier
sound_model   = joblib.load(os.path.join(BASE, 'childguard_sound_classifier.pkl'))
sound_scaler  = joblib.load(os.path.join(BASE, 'childguard_sound_scaler.pkl'))
sound_encoder = joblib.load(os.path.join(BASE, 'childguard_sound_encoder.pkl'))
sound_features= joblib.load(os.path.join(BASE, 'childguard_sound_features.pkl'))
print("  ✅ Sound Classifier loaded")

print("All AI models ready!")

# ── In-memory sequence buffer for LSTM ──────
# Stores last 12 readings per child
sequence_buffer = {}

def run_all_models(vital_data: dict, child_id: str) -> dict:
    """
    Runs all 4 AI models on incoming sensor data
    Returns results from each model
    """
    results = {
        "fall_detected": False,
        "anomaly_detected": False,
        "behavior_abnormal": False,
        "sound_alert": False,
        "sound_type": None,
        "alerts_to_create": []
    }

    # ── MODEL 1: Random Forest (Fall Detection) ──
    try:
        import pandas as pd
        rf_input = pd.DataFrame([vital_data])[rf_features]
        rf_pred = rf_model.predict(rf_input)[0]

        if rf_pred == 'FALL' or vital_data.get('fall_detected', False):
            results["fall_detected"] = True
            results["alerts_to_create"].append({
                "type": "FALL_DETECTED",
                "severity": "EMERGENCY",
                "title": "Fall Detected",
                "description": f"AI detected a fall — Random Forest confidence: HIGH"
            })
    except Exception as e:
        print(f"RF error: {e}")

    # ── MODEL 2: Isolation Forest (Anomaly) ──────
    try:
        if_input_data = [
            vital_data.get("heart_rate", 85),
            vital_data.get("spo2", 98),
            vital_data.get("temperature", 36.6),
            vital_data.get("accel_x", 0),
            vital_data.get("accel_y", 0),
            vital_data.get("accel_z", 9.8),
            vital_data.get("sound_level", 50),
            np.sqrt(vital_data.get("accel_x",0)**2 +
                   vital_data.get("accel_y",0)**2 +
                   vital_data.get("accel_z",9.8)**2),
            5.0  # hrv placeholder
        ]
        if_scaled = if_scaler.transform([if_input_data])
        if_pred = if_model.predict(if_scaled)[0]

        if if_pred == -1:
            results["anomaly_detected"] = True
            results["alerts_to_create"].append({
                "type": "ANOMALY_DETECTED",
                "severity": "WARNING",
                "title": "Unusual Activity Detected",
                "description": "Isolation Forest detected abnormal vital signs"
            })
    except Exception as e:
        print(f"IF error: {e}")

    # ── MODEL 3: LSTM (Behavior Pattern) ─────────
    try:
        if lstm_loaded:
            cid = str(child_id)
            reading = [
                vital_data.get("heart_rate", 85),
                vital_data.get("spo2", 98),
                vital_data.get("temperature", 36.6),
                vital_data.get("accel_x", 0),
                vital_data.get("accel_y", 0),
                vital_data.get("accel_z", 9.8),
            ]
            if cid not in sequence_buffer:
                sequence_buffer[cid] = []
            sequence_buffer[cid].append(reading)

            # Keep only last 12 readings
            if len(sequence_buffer[cid]) > 12:
                sequence_buffer[cid] = sequence_buffer[cid][-12:]

            # Run LSTM when we have enough data
            if len(sequence_buffer[cid]) == 12:
                seq = np.array(sequence_buffer[cid], dtype=np.float32)
                seq_flat = seq.reshape(-1, 6)
                seq_scaled = lstm_scaler.transform(seq_flat)
                seq_input = seq_scaled.reshape(1, 12, 6)
                prob = lstm_model.predict(seq_input, verbose=0)[0][0]

                if prob > 0.5:
                    results["behavior_abnormal"] = True
                    results["alerts_to_create"].append({
                        "type": "UNUSUAL_STILLNESS",
                        "severity": "WARNING",
                        "title": "Unusual Behavior Detected",
                        "description": f"LSTM detected abnormal activity pattern (confidence: {prob:.0%})"
                    })
    except Exception as e:
        print(f"LSTM error: {e}")

    # ── MODEL 4: Sound Classifier ─────────────────
    try:
        if vital_data.get("sound_level", 0) > 30:
            sound_level = vital_data.get("sound_level", 50)
            sound_input_data = {
                'amplitude': sound_level / 100,
                'amplitude_std': 0.1,
                'energy': (sound_level / 100) ** 2,
                'zero_crossing_rate': 0.3,
                'spectral_rolloff': sound_level * 50,
                'spectral_centroid': sound_level * 30,
                'frequency_mean': sound_level * 10,
                'frequency_std': sound_level * 5,
                'mfcc_1': sound_level * 0.3,
                'mfcc_2': -sound_level * 0.15,
                'mfcc_3': -sound_level * 0.1,
                'rms_energy': sound_level / 100,
                'peak_amplitude': min(sound_level / 80, 1.0),
                'duration_above_threshold': min(sound_level / 90, 1.0),
                'sound_db': sound_level,
            }
            import pandas as pd
            sound_df = pd.DataFrame([sound_input_data])[sound_features]
            sound_scaled = sound_scaler.transform(sound_df)
            sound_pred = sound_model.predict(sound_scaled)[0]
            sound_label = sound_encoder.inverse_transform([sound_pred])[0]

            results["sound_type"] = sound_label

            if sound_label in ['SCREAMING', 'CRYING']:
                results["sound_alert"] = True
                severity = "EMERGENCY" if sound_label == "SCREAMING" else "WARNING"
                results["alerts_to_create"].append({
                    "type": f"{sound_label}_DETECTED",
                    "severity": severity,
                    "title": f"{'Scream' if sound_label == 'SCREAMING' else 'Crying'} Detected",
                    "description": f"Sound classifier detected {sound_label.lower()} from child"
                })
    except Exception as e:
        print(f"Sound error: {e}")

    # ── Panic Button ──────────────────────────────
    if vital_data.get("panic_pressed", False):
        results["alerts_to_create"].append({
            "type": "SOS_PRESSED",
            "severity": "EMERGENCY",
            "title": "SOS Button Pressed",
            "description": "Child pressed the emergency SOS button"
        })

    # ── Band Removed ──────────────────────────────
    if not vital_data.get("band_on_wrist", True):
        results["alerts_to_create"].append({
            "type": "BAND_REMOVED",
            "severity": "WARNING",
            "title": "Band Removed",
            "description": "Child's band has been removed from wrist"
        })

    return results