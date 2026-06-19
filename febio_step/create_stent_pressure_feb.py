"""First FEBio pressure model for the experimental stent mesh.

This is a small, separate script used to test whether the labelled stent
mesh can be translated to FEBio and run. It's not part of the normal
cylinder pipeline.
"""

from pathlib import Path
import sys

import meshio
import pyfebio as feb

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    FEBIO_OUTPUT_STRIDE,
    FEBIO_PLOT_STRIDE,
    FEBIO_STEP_SIZE,
    FEBIO_TIME_STEPS,
    ROOT,
)
from febio_step.febio_helpers import (
    add_load_curve,
    add_output_requests,
    add_stainless_steel_material,
    print_febio_mesh_summary,
)


STENT_MSH_FILE = ROOT / "gmsh_step" / "stent_inner_selection.msh"
STENT_JOB_DIR = ROOT / "febio_step" / "jobs" / "stent"
STENT_FEB_FILE = STENT_JOB_DIR / "pressure_stent.feb"

PRESSURE_SURFACE = "inner_wall"
# keep the pressure low to avoid inverting small elements
INTERNAL_PRESSURE = 1.0e5


def read_stent_mesh():
    """Read the labelled stent '.msh' and return a pyfebio mesh."""
    print(f"reading stent mesh: {STENT_MSH_FILE}")

    gmsh_mesh = meshio.gmsh.read(STENT_MSH_FILE)
    febio_mesh = feb.mesh.translate_meshio(gmsh_mesh)

    return febio_mesh


def add_dynamic_solver_control(model):
    """Use a dynamic analysis for the free stent pressure test."""
    model.control_ = feb.control.Control(
        analysis="DYNAMIC",
        time_steps=FEBIO_TIME_STEPS,
        step_size=FEBIO_STEP_SIZE,
        plot_stride=FEBIO_PLOT_STRIDE,
        output_stride=FEBIO_OUTPUT_STRIDE,
        time_stepper=None,
    )


def add_internal_pressure(model):
    """Apply a PressureLoad to the surface named by 'PRESSURE_SURFACE'.

    Parameters:
    model : feb.model.Model
        The pyfebio model to update.
    """
    model.loads_.add_surface_load(
        feb.loads.PressureLoad(
            surface=PRESSURE_SURFACE,
            pressure=feb.loads.Scale(lc=1, text=INTERNAL_PRESSURE),
        )
    )


def main():
    """Create and save a FEBio input file for the labelled stent mesh.

    Side effects:
    - Reads the stent '.msh' file.
    - Uses a dynamic analysis without extra support nodes.
    - Writes the FEB file to 'STENT_FEB_FILE'.
    """
    febio_mesh = read_stent_mesh()
    print_febio_mesh_summary(febio_mesh)

    model = feb.model.Model(mesh_=febio_mesh)

    add_dynamic_solver_control(model)
    add_stainless_steel_material(model)
    add_internal_pressure(model)
    add_load_curve(model)
    add_output_requests(model)

    STENT_JOB_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(STENT_FEB_FILE))

    print(f"\nstent pressure FEBio file written: {STENT_FEB_FILE}")


if __name__ == "__main__":
    main()
