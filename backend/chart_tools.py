from pathlib import Path
import uuid
from typing import Literal
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for server environments

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "generated_charts"
CHART_DIR.mkdir(exist_ok=True)


ChartType = Literal["bar", "line", "pie"]


def validate_chart_data(data: dict[str, float]) -> tuple[list[str], list[float]]:
    if not data:
        raise ValueError("Data is empty.")

    labels = []
    values = []

    for key, value in data.items():
        labels.append(str(key))

        try:
            values.append(float(value))
        except ValueError:
            raise ValueError(f"Value for {key} is not numeric.")

    return labels, values


def create_chart_file(
    title: str,
    data: dict[str, float],
    chart_type: ChartType = "bar",
    x_label: str = "Category",
    y_label: str = "Value",
) -> dict:
    """
    Create a chart image from structured data.

    Example data:
    {
        "Tumor A": 12,
        "Tumor B": 8,
        "Tumor C": 15
    }
    """

    labels, values = validate_chart_data(data)

    file_id = uuid.uuid4().hex
    file_name = f"{file_id}.png"
    file_path = CHART_DIR / file_name

    plt.figure(figsize=(8, 5))

    if chart_type == "bar":
        plt.bar(labels, values)
        plt.xlabel(x_label)
        plt.ylabel(y_label)

    elif chart_type == "line":
        plt.plot(labels, values, marker="o")
        plt.xlabel(x_label)
        plt.ylabel(y_label)

    elif chart_type == "pie":
        plt.pie(values, labels=labels, autopct="%1.1f%%")
        plt.axis("equal")

    else:
        raise ValueError("chart_type must be bar, line, or pie.")

    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(file_path, dpi=150)
    plt.close()

    return {
        "message": "Chart created successfully.",
        "file_name": file_name,
        "file_path": str(file_path),
        "chart_type": chart_type,
    }