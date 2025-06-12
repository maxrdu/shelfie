# 📚 Shelfie

**Simple filesystem-based structured storage for data with metadata**

Shelfie helps you organize your data files in a structured, hierarchical way while automatically managing metadata. 
Think of it as a filing system that creates organized directories based on your data's characteristics and keeps 
track of important information about each dataset.

## 🎯 Why Shelfie?

- **Organized**: Automatically creates directory structures based on your data's fields
- **Metadata-aware**: Stores attributes alongside your data files
- **Flexible**: Works with any data that can be saved as CSV, JSON, or pickle
- **Simple**: Intuitive API for creating and reading structured datasets
- **Discoverable**: Easy to browse and understand your data organization in the filesystem

Shelfie is meant to be an in between a full database and having to create a wrapper for a filesystem based storage for
each project.

## 🏗️ How It Works

```
Root Directory
├── .shelfie.pkl                    # Shelf configuration
├── experiment_1/                   # Field 1 value
│   ├── random_forest/              # Field 2 value  
│   │   ├── 2025-06-12/             # Field 3 value (auto-generated date)
│   │   │   ├── metadata.json       # Stored attributes
│   │   │   ├── results.csv         # Your data files
│   │   │   └── model.pkl          # More data files
│   │   └── gradient_boost/
│   │       └── 2025-06-12/
│   │           ├── metadata.json
│   │           └── results.csv
│   └── neural_network/
│       └── 2025-06-12/
│           ├── metadata.json
│           └── predictions.csv
└── experiment_2/
    └── ...
```
Fields are more static attributes, while attributes are more specific based on the fields. You can think of each field
having their own attributes. In other words, when using a database for each field you would probably create their own
table.

### The Pattern

1. **Fields** → Directory structure (experiment/model/date)
2. **Attributes** → Metadata stored in JSON (learning_rate, epochs, etc.)
3. **Data** → Files attached to each record (CSV, JSON, pickle, etc.)

## 🚀 Quick Start

### Installation

```bash
pip install shelfie
```

### Basic Example

```python
import pandas as pd
from shelfie import Shelf, DateField

# Create a shelf for ML experiments
ml_shelf = Shelf(
    root="./experiments",
    fields=["experiment", "model", DateField("date")],  # Directory structure
    attributes=["epochs", "learning_rate"]              # Required metadata
)

# Create a new experiment record
experiment = ml_shelf.create(
    experiment="baseline",
    model="mlp", 
    epochs=100,
    learning_rate=0.01
)

# Attach your results
results_df = pd.DataFrame({
    "accuracy": [0.85, 0.87, 0.89], 
    "loss": [0.45, 0.32, 0.28],
    "epoch": [1, 2, 3]
})

experiment.attach(results_df, "results.csv")
```

This creates:
```
experiments/
└── baseline/
    └── mlp/
        └── 2025-06-12/
            ├── metadata.json  # {"epochs": 100, "learning_rate": 0.01}
            └── results.csv    # Your data
```

## 📖 Detailed Examples

### 1. ML Experiment Tracking

```python
from shelfie import Shelf, DateField, TimestampField
import pandas as pd

# Set up experiment tracking
experiments = Shelf(
    root="./ml_experiments",
    fields=["project", "model_type", DateField("date")],
    attributes=["dataset", "hyperparams", "notes"]
)

# Log different experiments
rf_experiment = experiments.create(
    project="customer_churn",
    model_type="random_forest",
    dataset="v2_cleaned",
    hyperparams={"n_estimators": 100, "max_depth": 10},
    notes="Baseline model with feature engineering"
)

# Attach multiple files
rf_experiment.attach(train_results, "training_metrics.csv")
rf_experiment.attach(test_results, "test_results.csv")
rf_experiment.attach(feature_importance, "feature_importance.csv")

# Try a different model
nn_experiment = experiments.create(
    project="customer_churn",
    model_type="neural_network",
    dataset="v2_cleaned", 
    hyperparams={"layers": [64, 32, 16], "dropout": 0.2},
    notes="Deep learning approach"
)
```

### 2. Sales Data by Region and Time

```python
# Organize sales data by geography and time
sales_shelf = Shelf(
    root="./sales_data",
    fields=["region", "year", "quarter"],
    attributes=["analyst", "report_type", "data_source"]
)

# Store Q1 data for North America
na_q1 = sales_shelf.create(
    region="north_america",
    year="2025", 
    quarter="Q1",
    analyst="john_doe",
    report_type="quarterly_summary",
    data_source="salesforce"
)

sales_data = pd.DataFrame({
    "product": ["A", "B", "C"],
    "revenue": [150000, 200000, 180000],
    "units_sold": [1500, 2000, 1800]
})

na_q1.attach(sales_data, "quarterly_sales.csv")
```

### 3. Survey Data Organization

```python
# Organize survey responses by type and demographics
surveys = Shelf(
    root="./survey_data",
    fields=["survey_type", "demographic", TimestampField("timestamp")],
    attributes=["sample_size", "methodology", "response_rate"]
)

# Store customer satisfaction survey
survey = surveys.create(
    survey_type="customer_satisfaction",
    demographic="millennials",
    sample_size=1000,
    methodology="online_panel", 
    response_rate=0.23
)

responses = pd.DataFrame({
    "question_id": [1, 2, 3, 4, 5],
    "avg_score": [4.2, 3.8, 4.1, 3.9, 4.0],
    "response_count": [920, 915, 898, 901, 911]
})

survey.attach(responses, "responses.csv")
```

## 📊 Reading Your Data Back

Use `load_from_shelf()` to read all data from a shelf:

```python
from shelfie import load_from_shelf

# Load all data from experiments shelf
data = load_from_shelf("./ml_experiments")

# Returns a dictionary of DataFrames:
# {
#   'metadata': DataFrame with all metadata + field values,
#   'training_metrics': Combined DataFrame from all training_metrics.csv files,
#   'test_results': Combined DataFrame from all test_results.csv files,
#   ...
# }

# Analyze all your experiments
print(data['metadata'])  # Overview of all experiments
print(data['training_metrics'])  # All training metrics combined
```

Each DataFrame automatically includes:
- All your original data columns
- Metadata fields (hyperparams, notes, etc.)  
- Directory structure fields (project, model_type, date)

## 🛠️ Advanced Features

### Custom Fields with Defaults

```python
from shelfie import Field, DateField, TimestampField

# Field with a default value
shelf = Shelf(
    root="./data",
    fields=[
        "experiment",
        Field("environment", default="production"),  # Always "production" unless specified
        DateField("date"),                          # Auto-generates today's date
        TimestampField("timestamp")                 # Auto-generates current timestamp
    ],
    attributes=["version"]
)

# Only need to specify non-default fields
record = shelf.create(
    experiment="test_1",
    version="1.0"
)
# Creates: ./data/test_1/production/2025-06-12/2025-06-12_14-30-45/
```

### Multiple File Types

```python
# Attach different file types
record.attach(results_df, "results.csv")           # CSV
record.attach(model_config, "config.json")         # JSON  
record.attach(trained_model, "model.pkl")          # Pickle
record.attach(report_text, "summary.txt")          # Text
```

By default only CSV files will be loaded, but the file paths of all other files are available.

### Loading Existing Shelves

```python
# Load a shelf that was created elsewhere
existing_shelf = Shelf.load_from_root("./experiments")

# Continue adding to it
new_experiment = existing_shelf.create(
    experiment="advanced",
    model="xgboost",
    epochs=200,
    learning_rate=0.05
)
```

## 🗂️ Directory Structure Examples

### Before Shelfie
```
my_project/
├── experiment1_rf_results.csv
├── experiment1_rf_model.pkl  
├── experiment2_nn_results.csv
├── experiment2_nn_model.pkl
├── baseline_test_data.csv
├── advanced_test_data.csv
└── notes.txt  # Which file belongs to what?
```

### After Shelfie
```
my_project/
├── baseline/
│   ├── mlp/
│   │   └── 2025-06-12/
│   │       ├── metadata.json      # {"epochs": 100, "lr": 0.01}
│   │       ├── results.csv
│   │       └── model.pkl
│   └── cnn/
│       └── 2025-06-12/
│           ├── metadata.json      # {"epochs": 200, "lr": 0.001}
│           ├── results.csv
│           └── model.pkl
└── advanced/
    └── xgboost/
        └── 2025-06-12/
            ├── metadata.json      # {"n_estimators": 500, "max_depth": 8}
            ├── results.csv
            └── model.pkl
```

## 📄 License

This project is licensed under the MIT License.

---

**Happy organizing! 📚✨**