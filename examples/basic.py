import pandas as pd

from shelfie import Shelf, DateField, TimestampField


# Example usage
if __name__ == "__main__":
    # ML Experiments
    ml_storage = Shelf(
        root="./experiments",
        fields=["experiment", "model", DateField("date")],
        attributes=["epochs", "learning_rate"],
    )

    experiment = ml_storage.create(
        experiment="baseline", model="rf", epochs=100, learning_rate=0.01
    )

    # Sales Data by Region and Quarter
    sales_storage = Shelf(
        root="./sales_data",
        fields=["region", "year", "quarter"],
        attributes=["analyst", "report_type"]
    )

    sales_record = sales_storage.create(
        region="north_america",
        year="2025",
        quarter="Q2",
        analyst="john_doe",
        report_type="monthly",
    )

    # Survey Results by Demographics
    survey_storage = Shelf(
        root="./surveys",
        fields=["survey_type", "demographic", TimestampField("timestamp")],
        attributes=["sample_size", "methodology"],
    )

    survey = survey_storage.create(
        survey_type="customer_satisfaction",
        demographic="18-25",
        sample_size=500,
        methodology="online",
    )

    # Create an ML experiment - metadata is saved immediately
    experiment = ml_storage.create(
        experiment="baseline",
        model="rf",
        epochs=100,
        learning_rate=0.01,
        n_estimators=50,
    )

    # Create sample results
    sample_results = pd.DataFrame(
        {"accuracy": [0.85, 0.87, 0.89], "loss": [0.45, 0.32, 0.28], "epoch": [1, 2, 3]}
    )

    # Save only the results CSV
    experiment.attach(sample_results, "data.csv")

    # Save sales data
    sales_data = pd.DataFrame(
        {
            "product": ["A", "B", "C"],
            "revenue": [10000, 15000, 12000],
            "units_sold": [100, 150, 120],
        }
    )

    sales_record.attach(sales_data, "sales.csv")
