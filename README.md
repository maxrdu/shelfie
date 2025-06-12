# 📚 Shelfie

**Simple filesystem-based structured storage for data with metadata**

Shelfie helps you organize your data files in a structured, hierarchical way while automatically managing metadata. Think of it as a filing system that creates organized directories based on your data's characteristics and keeps track of important information about each dataset.

## 🎯 Why Shelfie?

- **Organized**: Automatically creates directory structures based on your data's fields
- **Metadata-aware**: Stores attributes alongside your data files
- **Flexible**: Works with any data that can be saved as CSV, JSON, or pickle
- **Simple**: Intuitive API for creating and reading structured datasets
- **Discoverable**: Easy to browse and understand your data organization in the filesystem

Shelfie is meant to be an in between a full database and having to create a wrapper for a filesystem based storage for
each project.

## 🏗️ How It Works

### **Conceptual Model: Database Relations → Directory Structure**

Shelfie translates database-style relationships into filesystem organization:

```
Database Thinking          →    Filesystem Result
─────────────────────────────────────────────────────
Tables: [experiments]      →    Directory Level 1
Tables: [models]           →    Directory Level 2  
Tables: [dates]            →    Directory Level 3
Columns: epochs, lr        →    metadata.json
Data: results.csv          →    Attached files
```

### Visual Concept

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

### The Pattern

**Shelfie = Filesystem-Based Relational Design**

1. **Fields** → Directory hierarchy (what you'd normalize into separate **tables**)
2. **Attributes** → Stored metadata (what you'd store as **columns** in those tables)
3. **Data** → Files attached to each record (the actual **data** your database would reference)
4. **File Paths** → Automatically tracked as `filename_path__` in metadata

**Traditional Database:**
```sql
SELECT r.accuracy, e.name, m.type, r.epochs 
FROM results r
JOIN experiments e ON r.experiment_id = e.id  
JOIN models m ON r.model_id = m.id
WHERE e.date = '2025-06-12'
```

**Shelfie Equivalent:**
```python
data = load_from_shelf("./experiments")
results_df = data['results']  # Already has experiment, model, date columns!
filtered = results_df[results_df['date'] == '2025-06-12']
```

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
    learning_rate=0.001  # Typical learning rate for neural networks
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
            ├── metadata.json  # {"epochs": 100, "learning_rate": 0.001, "results_path__": "/path/to/results.csv"}
            └── results.csv    # Your data
```

## 📖 Detailed Examples

### 1. ML Experiment Tracking

**Think of this as three related database tables:**
- `experiments` table → `project` field  
- `models` table → `model_type` field
- `runs` table → `date` field
- Attributes: `dataset`, `hyperparams`, `notes`

```python
from shelfie import Shelf, DateField, TimestampField
import pandas as pd

# Set up experiment tracking (defines your "table" relationships)
experiments = Shelf(
    root="./ml_experiments",
    fields=["project", "model_type", DateField("date")],  # Your table hierarchy
    attributes=["dataset", "hyperparams", "notes"]        # Your table columns
)

# Log different experiments
mlp_experiment = experiments.create(
    project="customer_churn",
    model_type="mlp",
    dataset="v2_cleaned",
    hyperparams={"hidden_layers": [128, 64, 32], "dropout": 0.3, "activation": "relu"},
    notes="Multi-layer perceptron with dropout regularization"
)

# Attach multiple files
mlp_experiment.attach(train_results, "training_metrics.csv")
mlp_experiment.attach(test_results, "test_results.csv")
mlp_experiment.attach(feature_importance, "feature_importance.csv")

# Try a different model
cnn_experiment = experiments.create(
    project="customer_churn",
    model_type="cnn",
    dataset="v2_cleaned", 
    hyperparams={"filters": [32, 64, 128], "kernel_size": 3, "learning_rate": 0.0001},
    notes="Convolutional neural network approach"
)
```

### 2. Sales Data by Region and Time

**Database equivalent:**
- `regions` table → `region` field
- `time_periods` table → `year`, `quarter` fields  
- Attributes: `analyst`, `report_type`, `data_source`

```python
# Organize sales data by geography and time (multi-table relationship)
sales_shelf = Shelf(
    root="./sales_data",
    fields=["region", "year", "quarter"],                    # Geographic + temporal tables
    attributes=["analyst", "report_type", "data_source"]     # Report metadata columns
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

**Database tables:** `survey_types` → `demographics` → `timestamps`

```python
# Organize survey responses by type and demographics
surveys = Shelf(
    root="./survey_data",
    fields=["survey_type", "demographic", TimestampField("timestamp")],  # Survey taxonomy
    attributes=["sample_size", "methodology", "response_rate"]            # Survey metadata
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

**The Magic: Automatic JOIN Operations**

Unlike databases where you need explicit JOINs, Shelfie automatically combines your "table" relationships:

```python
from shelfie import load_from_shelf

# Load all data from experiments shelf
data = load_from_shelf("./ml_experiments")

# Returns a dictionary of DataFrames - like running multiple JOINed queries:
# {
#   'metadata': All experiment metadata with project+model+date info,
#   'training_metrics': Training data with experiment context automatically joined,
#   'test_results': Test data with experiment context automatically joined,
#   ...
# }

# Analyze all your experiments - no JOINs needed!
print(data['metadata'])  # Overview of all experiments
print(data['training_metrics'])  # All training metrics with full context

# Note: File paths are stored as filename_path__ columns (e.g., 'training_metrics_path__')
```

**What you get automatically:**
- **Denormalized DataFrames**: Each CSV gets experiment+model+date columns added
- **Full Context**: Every row knows its complete "relational" context  
- **No JOIN complexity**: Relationships are already materialized
- **Pandas-ready**: Immediate analysis without SQL knowledge

Each DataFrame automatically includes:
- **Original data columns**: Your actual data
- **Attribute columns**: Metadata from your "table columns" (hyperparams, notes, etc.)  
- **Field columns**: Directory structure as relational context (project, model_type, date)
- **File path columns**: References as `filename_path__` columns

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
# Metadata includes: version_path__ for any attached files
```

### Multiple File Types

```python
# Attach different file types
record.attach(results_df, "results.csv")           # CSV
record.attach(model_config, "config.json")         # JSON  
record.attach(trained_model, "model.pkl")          # Pickle
record.attach(report_text, "summary.txt")          # Text
```

### Loading Existing Shelves

```python
# Load a shelf that was created elsewhere
existing_shelf = Shelf.load_from_root("./experiments")

# Continue adding to it
new_experiment = existing_shelf.create(
    experiment="advanced",
    model="transformer",
    epochs=50,
    learning_rate=0.0001  # Lower learning rate for transformer models
)
```

## 🗂️ Directory Structure Examples

### Before Shelfie
```
my_project/
├── experiment1_mlp_results.csv
├── experiment1_mlp_model.pkl  
├── experiment2_cnn_results.csv
├── experiment2_cnn_model.pkl
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
│   │       ├── metadata.json      # {"epochs": 100, "lr": 0.001, "results_path__": "/path/results.csv"}
│   │       ├── results.csv
│   │       └── model.pkl
│   └── cnn/
│       └── 2025-06-12/
│           ├── metadata.json      # {"epochs": 200, "lr": 0.0001, "results_path__": "/path/results.csv"}
│           ├── results.csv
│           └── model.pkl
└── advanced/
    └── transformer/
        └── 2025-06-12/
            ├── metadata.json      # {"epochs": 50, "lr": 0.0001, "results_path__": "/path/results.csv"}
            ├── results.csv
            └── model.pkl
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---

**Happy organizing! 📚✨**