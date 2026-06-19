"""
This is the main script to run the full pipeline. 

It calls each step in turn and checks that the expected files are created.
"""
import subprocess
import sys
from pathlib import Path

from config import (
    FEB_FILE,
    FEBIO_COMMAND,
    FREECAD_COMMAND,
    LOAD_CASE,
    MSH_FILE,
    STEP_FILE,
    validate_config,
)

# scripts used by the pipeline
ROOT = Path(__file__).resolve().parent
FREECAD_SCRIPT = ROOT / "freecad_step" / "script.py"
GMSH_SCRIPT = ROOT / "gmsh_step" / "mesh.py"
COMPRESSION_SCRIPT = ROOT / "febio_step" / "create_compression_feb.py"
PRESSURE_SCRIPT = ROOT / "febio_step" / "create_pressure_feb.py"
RESULT_SCRIPT = ROOT / "febio_step" / "extract_results.py"

FEBIO_SCRIPTS = {
    "compression": COMPRESSION_SCRIPT,
    "pressure": PRESSURE_SCRIPT,
}


def run_command(command, working_directory=ROOT):
    """Run a command and stop the pipeline if the command fails"""
    print(" ".join(str(part) for part in command))

    try:
        result = subprocess.run(command, cwd=working_directory)
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Required executable was not found: {command[0]}. "
            "Check FREECAD_COMMAND or FEBIO_COMMAND."
        ) from error

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline command failed: {' '.join(str(part) for part in command)}")


def check_file_exists(file_path, description):
    """Check that the previous step created the file we expected."""
    if not file_path.exists():
        raise FileNotFoundError(f"{description} was not created: {file_path}")

    print(f"{description}: {file_path}")


def remove_file_if_present(file_path):
    """Remove output from an earlier run so it cannot be mistaken for new data."""
    file_path.unlink(missing_ok=True)


def main():
    """Orchestrate the full pipeline from geometry to results.

    Effects:
    - Runs the FreeCAD script to produce 'STEP_FILE'.
    - Runs the Gmsh script to produce 'MSH_FILE'.
    - Runs the appropriate FEBio builder to create 'FEB_FILE'.
    - Runs 'febio4' to execute the solver and generate '.xplt' results.
    - Runs the result extraction script to produce summary output.
    """

    validate_config()
    print("starting the pipeline")

    # create the cylinder geometry
    print("\nstep 1: create the geometry with FreeCAD")
    remove_file_if_present(STEP_FILE)
    run_command([*FREECAD_COMMAND, str(FREECAD_SCRIPT)])

    check_file_exists(STEP_FILE, "STEP file")

    # turn the STEP geometry into a mesh
    print("\nstep 2: create the Gmsh mesh")
    remove_file_if_present(MSH_FILE)
    gmsh_command = [sys.executable, str(GMSH_SCRIPT)]
    run_command(gmsh_command)
    check_file_exists(MSH_FILE, "Gmsh mesh")

    # build the FEBio input file
    print(f"\nstep 3: create the FEBio {LOAD_CASE} model")
    remove_file_if_present(FEB_FILE)
    febio_input_command = [sys.executable, str(FEBIO_SCRIPTS[LOAD_CASE])]
    run_command(febio_input_command)
    check_file_exists(FEB_FILE, "FEBio input file")

    # run the simulation
    print("\nstep 4: run the FEBio solver")
    for suffix in [".xplt", ".hdf5", ".log"]:
        remove_file_if_present(FEB_FILE.with_suffix(suffix))
    febio_command = [FEBIO_COMMAND, "-i", FEB_FILE.name]
    run_command(febio_command, working_directory=FEB_FILE.parent)
    check_file_exists(FEB_FILE.with_suffix(".xplt"), "FEBio result file")

    # read and summarize the results
    print("\nstep 5: extract result values")
    result_command = [sys.executable, str(RESULT_SCRIPT)]
    run_command(result_command)

    print("\npipeline finished successfully")


if __name__ == "__main__":
    main()
