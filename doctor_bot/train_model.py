"""Train a simple ML model to predict doctor specialty from text"""
import pandas as pd
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

CSV_FILE = "doctors_data.csv"
MODEL_FILE = "specialty_model.joblib"
LABEL_ENCODER_FILE = "label_encoder.joblib"


def load_data():
    """Load and preprocess data from CSV"""
    if not os.path.isfile(CSV_FILE):
        raise FileNotFoundError(
            f"CSV file '{CSV_FILE}' not found. "
            f"Run collect_data.py first to gather data."
        )
    
    df = pd.read_csv(CSV_FILE)
    print(f"📊 Loaded {len(df)} rows from {CSV_FILE}")
    
    # Drop rows with missing specialty (required for training)
    initial_count = len(df)
    df = df.dropna(subset=["specialty"])
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"⚠️  Dropped {dropped} rows with missing specialty")
    
    if len(df) == 0:
        raise ValueError("No data with specialty field. Cannot train model.")
    
    # Combine fields into one text input for the model
    df["text"] = (
        df.get("name", pd.Series("")).fillna("") + " " +
        df.get("address", pd.Series("")).fillna("") + " " +
        df.get("specialty", pd.Series("")).fillna("")
    )
    
    # Remove empty text rows
    df = df[df["text"].str.strip() != ""]
    
    print(f"✅ {len(df)} rows ready for training")
    print(f"📈 Unique specialties: {df['specialty'].nunique()}")
    print(f"   Specialties: {', '.join(df['specialty'].value_counts().head(10).index.tolist())}")
    
    return df


def train():
    """Train the specialty prediction model"""
    print("\n" + "="*60)
    print("=== Training Doctor Specialty Model ===")
    print("="*60 + "\n")
    
    df = load_data()
    
    # Check minimum data requirements
    if len(df) < 20:
        print("⚠️  Warning: Very small dataset. Model may not perform well.")
        print("   Consider collecting more data first.\n")
    
    X = df["text"]
    y = df["specialty"]
    
    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    print(f"📚 Training on {len(X)} samples...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    
    print(f"   Train: {len(X_train)} samples")
    print(f"   Test: {len(X_test)} samples\n")
    
    # Create model pipeline
    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])
    
    print("🔄 Training model...")
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n📊 Model Performance:")
    print("-" * 60)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2%}\n")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    # Save model
    joblib.dump(model, MODEL_FILE)
    joblib.dump(le, LABEL_ENCODER_FILE)
    print(f"\n✅ Saved model to {MODEL_FILE}")
    print(f"✅ Saved label encoder to {LABEL_ENCODER_FILE}")
    
    return model, le


def demo_predict():
    """Interactive prediction demo"""
    if not os.path.isfile(MODEL_FILE) or not os.path.isfile(LABEL_ENCODER_FILE):
        print("❌ Model files not found. Run train() first.")
        return
    
    print("\n" + "="*60)
    print("=== Doctor Specialty Predictor ===")
    print("="*60)
    print("\nEnter doctor information to predict their specialty.")
    print("Type 'q' to quit.\n")
    
    model = joblib.load(MODEL_FILE)
    le = joblib.load(LABEL_ENCODER_FILE)
    
    while True:
        txt = input("Enter doctor description (name, address, etc.): ").strip()
        
        if txt.lower() == "q":
            break
        
        if not txt:
            continue
        
        try:
            pred = model.predict([txt])[0]
            proba = model.predict_proba([txt])[0]
            label = le.inverse_transform([pred])[0]
            confidence = proba[pred] * 100
            
            print(f"\n🎯 Predicted specialty: {label}")
            print(f"   Confidence: {confidence:.1f}%")
            
            # Show top 3 predictions
            top3_indices = proba.argsort()[-3:][::-1]
            print("\n   Top 3 predictions:")
            for idx in top3_indices:
                specialty = le.inverse_transform([idx])[0]
                conf = proba[idx] * 100
                print(f"   - {specialty}: {conf:.1f}%")
            
            print()
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        # Just run predictions
        demo_predict()
    else:
        # Train model
        try:
            model, le = train()
            
            # Ask if user wants to test predictions
            print("\n" + "="*60)
            response = input("Test predictions now? (yes/no): ").strip().lower()
            if response == "yes":
                demo_predict()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

