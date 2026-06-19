"""make simple plots from the saved study results

run the study scripts first
this only reads their csv files and saves figures
"""

import csv
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", "/tmp/pipelinefebio_matplotlib")

import matplotlib.pyplot as plt

RESULTS_FOLDER = ROOT / "study_results"
FIGURE_FOLDER = RESULTS_FOLDER / "figures"

MESH_CONVERGENCE_FILE = RESULTS_FOLDER / "mesh_convergence.csv"
YOUNGS_MODULUS_FILE = RESULTS_FOLDER / "youngs_modulus.csv"
CYLINDER_THICKNESS_FILE = RESULTS_FOLDER / "cylinder_thickness.csv"


def read_csv_rows(file_path):
    """Read the CSV and return only the runs that succeeded.

    Parameters:
    file_path : pathlib.Path
        The study CSV file to read.

    Returns:
    list[dict]
        Rows where the 'status' field is 'ok'.
    """
    if not file_path.exists():
        print(f"skipping missing results file: {file_path}")
        return []

    with file_path.open() as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    return [row for row in rows if row["status"] == "ok"]


def rows_for_cylinder_type(rows, cylinder_type, x_column):
    """Get rows for one cylinder type and sort them by a column.

    Parameters:
    rows : list[dict]
        Study rows (from 'read_csv_rows').
    cylinder_type : str
        'solid' or 'hollow'.
    x_column : str
        Column name used for sorting (converted to float).

    Returns:
    list[dict]
        Matching rows sorted by the x_column.
    """
    matching_rows = [row for row in rows if row["cylinder_type"] == cylinder_type]
    return sorted(matching_rows, key=lambda row: float(row[x_column]))


def values_from_rows(rows, column, scale=1.0):
    """Pull numbers from a column and apply a scale.

    Parameters:
    rows : list[dict]
        Rows with the numeric column.
    column : str
        Column name to convert to float.
    scale : float
        Divide the numbers by this (default 1.0).

    Returns:
    list[float]
        Scaled numbers.
    """
    return [float(row[column]) / scale for row in rows]


def plot_two_cylinder_types(
    rows,
    x_column,
    y_column,
    x_label,
    y_label,
    title,
    figure_name,
    x_scale=1.0,
    y_scale=1.0,
):
    """Plot 'solid' and 'hollow' cylinders on the same figure and save it.

    Parameters are straightforward: column names, labels, title and output name.
    x_scale and y_scale let you rescale units (e.g. Pa -> GPa).
    """
    plt.figure(figsize=(7, 4.5))

    for cylinder_type in ["solid", "hollow"]:
        cylinder_rows = rows_for_cylinder_type(rows, cylinder_type, x_column)
        x_values = values_from_rows(cylinder_rows, x_column, x_scale)
        y_values = values_from_rows(cylinder_rows, y_column, y_scale)

        plt.plot(x_values, y_values, marker="o", linewidth=2, label=cylinder_type)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    if "error" in y_column:
        plt.axhline(0, color="black", linewidth=1, alpha=0.4)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_file = FIGURE_FOLDER / figure_name
    plt.savefig(output_file, dpi=200)
    plt.savefig(output_file.with_suffix(".pdf"))
    plt.close()

    print(f"saved {output_file}")


def plot_one_series(
    rows,
    x_column,
    y_column,
    x_label,
    y_label,
    title,
    figure_name,
    x_scale=1.0,
    y_scale=1.0,
    comparison_column=None,
    comparison_label=None,
):
    """plot one study series and save it"""
    if not rows:
        print(f"skipping {figure_name}, no rows")
        return

    sorted_rows = sorted(rows, key=lambda row: float(row[x_column]))
    x_values = values_from_rows(sorted_rows, x_column, x_scale)
    y_values = values_from_rows(sorted_rows, y_column, y_scale)

    plt.figure(figsize=(7, 4.5))
    plt.plot(x_values, y_values, marker="o", linewidth=2, label="FEBio")
    if comparison_column:
        comparison_values = values_from_rows(
            sorted_rows, comparison_column, y_scale
        )
        plt.plot(
            x_values,
            comparison_values,
            linestyle="--",
            linewidth=2,
            label=comparison_label,
        )
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    if "error" in y_column:
        plt.axhline(0, color="black", linewidth=1, alpha=0.4)
    plt.grid(True, alpha=0.3)
    if comparison_column:
        plt.legend()
    plt.tight_layout()

    output_file = FIGURE_FOLDER / figure_name
    plt.savefig(output_file, dpi=200)
    plt.savefig(output_file.with_suffix(".pdf"))
    plt.close()

    print(f"saved {output_file}")


def make_mesh_convergence_plots():
    """Make the mesh convergence figures from the CSV results.

    Reads 'MESH_CONVERGENCE_FILE' and writes images into the figures folder.
    """
    rows = read_csv_rows(MESH_CONVERGENCE_FILE)

    plot_two_cylinder_types(
        rows,
        x_column="mesh_size",
        y_column="run_time_seconds",
        x_label="mesh size",
        y_label="run time (s)",
        title="mesh size vs run time",
        figure_name="mesh_size_vs_runtime.png",
    )
    plot_two_cylinder_types(
        rows,
        x_column="mesh_size",
        y_column="max_stress",
        x_label="mesh size",
        y_label="max stress (GPa)",
        title="mesh size vs max stress",
        figure_name="mesh_size_vs_max_stress.png",
        y_scale=1e9,
    )
    plot_two_cylinder_types(
        rows,
        x_column="mesh_size",
        y_column="max_strain",
        x_label="mesh size",
        y_label="max Lagrange strain",
        title="mesh size vs max strain",
        figure_name="mesh_size_vs_max_strain.png",
    )
    plot_two_cylinder_types(
        rows,
        x_column="mesh_size",
        y_column="compression_stiffness",
        x_label="mesh size",
        y_label="compression stiffness",
        title="mesh size vs compression stiffness",
        figure_name="mesh_size_vs_stiffness.png",
    )
    plot_two_cylinder_types(
        rows,
        x_column="mesh_size",
        y_column="stiffness_error_percent",
        x_label="mesh size",
        y_label="difference from theory (%)",
        title="mesh size vs stiffness difference",
        figure_name="mesh_size_vs_stiffness_error.png",
    )


def make_youngs_modulus_plots():
    """Make plots that show how changing Young's modulus affects results.

    Reads 'YOUNGS_MODULUS_FILE' and writes images into the figures folder.
    """
    rows = read_csv_rows(YOUNGS_MODULUS_FILE)

    plot_two_cylinder_types(
        rows,
        x_column="young_modulus",
        y_column="max_stress",
        x_label="Young's modulus (GPa)",
        y_label="max stress (GPa)",
        title="Young's modulus vs max stress",
        figure_name="youngs_modulus_vs_max_stress.png",
        x_scale=1e9,
        y_scale=1e9,
    )
    plot_two_cylinder_types(
        rows,
        x_column="young_modulus",
        y_column="max_strain",
        x_label="Young's modulus (GPa)",
        y_label="max Lagrange strain",
        title="Young's modulus vs max strain",
        figure_name="youngs_modulus_vs_max_strain.png",
        x_scale=1e9,
    )
    plot_two_cylinder_types(
        rows,
        x_column="young_modulus",
        y_column="compression_stiffness",
        x_label="Young's modulus (GPa)",
        y_label="compression stiffness",
        title="Young's modulus vs compression stiffness",
        figure_name="youngs_modulus_vs_stiffness.png",
        x_scale=1e9,
    )
    plot_two_cylinder_types(
        rows,
        x_column="young_modulus",
        y_column="stiffness_error_percent",
        x_label="Young's modulus (GPa)",
        y_label="difference from theory (%)",
        title="Young's modulus vs stiffness difference",
        figure_name="youngs_modulus_vs_stiffness_error.png",
        x_scale=1e9,
    )


def make_cylinder_thickness_plots():
    """Make plots for the wall thickness geometry study"""
    rows = read_csv_rows(CYLINDER_THICKNESS_FILE)

    plot_one_series(
        rows,
        x_column="wall_thickness",
        y_column="z_reaction_force_abs",
        x_label="wall thickness",
        y_label="reaction force magnitude",
        title="wall thickness vs reaction force",
        figure_name="wall_thickness_vs_reaction_force.png",
    )
    plot_one_series(
        rows,
        x_column="wall_thickness",
        y_column="compression_stiffness",
        x_label="wall thickness",
        y_label="compression stiffness",
        title="wall thickness vs compression stiffness",
        figure_name="wall_thickness_vs_stiffness.png",
        comparison_column="theoretical_stiffness",
        comparison_label="theoretical",
    )
    plot_one_series(
        rows,
        x_column="wall_thickness",
        y_column="stiffness_error_percent",
        x_label="wall thickness",
        y_label="difference from theory (%)",
        title="wall thickness vs stiffness difference",
        figure_name="wall_thickness_vs_stiffness_error.png",
    )


def main():
    """Make the figures folder (if needed) and save all plots.

    This is the simple script entry point used when running the module.
    """
    print("making plots")
    FIGURE_FOLDER.mkdir(parents=True, exist_ok=True)

    make_mesh_convergence_plots()
    make_youngs_modulus_plots()
    make_cylinder_thickness_plots()

    print(f"\nfigures saved in: {FIGURE_FOLDER}")


if __name__ == "__main__":
    main()
