"""run the hollow cylinder with several wall thicknesses

this changes the FreeCAD geometry and checks the reaction force and stiffness
"""

import csv
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from config import (
    COMPRESSION_DISPLACEMENT_Z,
    COMPRESSION_FEB_FILE,
    CYLINDER_HEIGHT,
    CYLINDER_RADIUS,
    MESH_SIZE,
    YOUNG_MODULUS,
)
from febio_step.result_helpers import (
    calculate_compression_stiffness,
    calculate_cylinder_area,
    calculate_percent_difference,
    calculate_theoretical_compression_stiffness,
    maximum_magnitude,
    read_last_result_values,
    read_reaction_forces_for_node_set,
)


MAIN_SCRIPT = ROOT / "main.py"
RESULTS_FOLDER = ROOT / "study_results"
RESULTS_FILE = RESULTS_FOLDER / "cylinder_thickness.csv"
HDF5_FILE = COMPRESSION_FEB_FILE.with_suffix(".hdf5")

# thicker walls should give higher reaction forces and stiffness
WALL_THICKNESSES = [0.5, 0.75, 1.0, 1.5, 2.0]


def calculate_result_numbers(inner_radius):
    """read the last result and calculate the thickness metrics"""
    result_values = read_last_result_values(HDF5_FILE)
    top_face_reaction_forces = read_reaction_forces_for_node_set(
        HDF5_FILE,
        result_values["reaction_forces"],
        "top_face",
    )
    _total_reaction_force, z_reaction_force, compression_stiffness = calculate_compression_stiffness(
        top_face_reaction_forces,
        COMPRESSION_DISPLACEMENT_Z,
    )
    theoretical_stiffness = calculate_theoretical_compression_stiffness(
        "hollow",
        CYLINDER_RADIUS,
        inner_radius,
        CYLINDER_HEIGHT,
        YOUNG_MODULUS,
    )
    stiffness_error_percent = calculate_percent_difference(compression_stiffness, theoretical_stiffness)
    cross_section_area = calculate_cylinder_area("hollow", CYLINDER_RADIUS, inner_radius)

    return {
        "nodes": result_values["nodes"],
        "elements": result_values["elements"],
        "max_displacement": maximum_magnitude(result_values["displacement"]),
        "max_stress": maximum_magnitude(result_values["stress"]),
        "max_strain": maximum_magnitude(result_values["strain"]),
        "z_reaction_force": z_reaction_force,
        "z_reaction_force_abs": abs(z_reaction_force),
        "cross_section_area": cross_section_area,
        "compression_stiffness": compression_stiffness,
        "theoretical_stiffness": theoretical_stiffness,
        "stiffness_error_percent": stiffness_error_percent,
    }


def remove_old_hdf5_file():
    """remove previous converted output so old data is not reused"""
    if HDF5_FILE.exists():
        HDF5_FILE.unlink()


def run_pipeline_with_settings(wall_thickness):
    """run the main pipeline once with a temporary wall thickness"""
    inner_radius = CYLINDER_RADIUS - wall_thickness

    if inner_radius <= 0:
        raise ValueError("wall thickness should be smaller than the outer radius")

    print(f"\nrunning hollow cylinder with wall thickness {wall_thickness}")

    environment = os.environ.copy()
    environment["PIPELINE_CYLINDER_TYPE"] = "hollow"
    environment["PIPELINE_CYLINDER_INNER_RADIUS"] = str(inner_radius)
    environment["PIPELINE_MESH_SIZE"] = str(MESH_SIZE)
    environment["PIPELINE_LOAD_CASE"] = "compression"
    environment["PIPELINE_PLOT_STRIDE"] = "20"
    environment["PIPELINE_OUTPUT_STRIDE"] = "20"

    remove_old_hdf5_file()

    start_time = time.perf_counter()
    subprocess.run([sys.executable, str(MAIN_SCRIPT)], cwd=ROOT, env=environment, check=True)
    end_time = time.perf_counter()

    result_numbers = calculate_result_numbers(inner_radius)
    result_numbers["cylinder_type"] = "hollow"
    result_numbers["outer_radius"] = CYLINDER_RADIUS
    result_numbers["inner_radius"] = inner_radius
    result_numbers["wall_thickness"] = wall_thickness
    result_numbers["mesh_size"] = MESH_SIZE
    result_numbers["run_time_seconds"] = end_time - start_time

    return result_numbers


def write_results(rows):
    """save the current rows to the CSV file"""
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "cylinder_type",
        "outer_radius",
        "inner_radius",
        "wall_thickness",
        "mesh_size",
        "nodes",
        "elements",
        "run_time_seconds",
        "max_displacement",
        "max_stress",
        "max_strain",
        "z_reaction_force",
        "z_reaction_force_abs",
        "cross_section_area",
        "compression_stiffness",
        "theoretical_stiffness",
        "stiffness_error_percent",
        "status",
        "error",
    ]

    with RESULTS_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """run the cylinder thickness study"""
    print("starting cylinder thickness study")

    rows = []

    for wall_thickness in WALL_THICKNESSES:
        try:
            row = run_pipeline_with_settings(wall_thickness)
            row["status"] = "ok"
            row["error"] = ""
        except Exception as error:
            row = {
                "cylinder_type": "hollow",
                "outer_radius": CYLINDER_RADIUS,
                "inner_radius": CYLINDER_RADIUS - wall_thickness,
                "wall_thickness": wall_thickness,
                "mesh_size": MESH_SIZE,
                "nodes": "",
                "elements": "",
                "run_time_seconds": "",
                "max_displacement": "",
                "max_stress": "",
                "max_strain": "",
                "z_reaction_force": "",
                "z_reaction_force_abs": "",
                "cross_section_area": "",
                "compression_stiffness": "",
                "theoretical_stiffness": "",
                "stiffness_error_percent": "",
                "status": "failed",
                "error": str(error),
            }

        rows.append(row)
        write_results(rows)

    print(f"\nthickness study results written to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
