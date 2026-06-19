from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent


# used for output files and the FEBio job folder
GEOMETRY_NAME = "cylinder"

# choose which load case main.py should run
# options are "compression" and "pressure"
LOAD_CASE = os.environ.get("PIPELINE_LOAD_CASE", "compression")

# compression setting
COMPRESSION_DISPLACEMENT_Z = -0.1

# pressure settings
# pressure is applied to the inner wall of the hollow cylinder
PRESSURE_SURFACE = "inner_wall"
INTERNAL_PRESSURE = float(os.environ.get("PIPELINE_INTERNAL_PRESSURE", 2.0e10))


# material settings

MATERIAL_NAME = "stainless_steel"
YOUNG_MODULUS = float(os.environ.get("PIPELINE_YOUNG_MODULUS", 193e9))
POISSON_RATIO = 0.3
DENSITY = 8000


# FEBio control and output settings
# the automatic time stepper can use fewer steps when convergence is easy
FEBIO_TIME_STEPS = 20
FEBIO_STEP_SIZE = 0.05
FEBIO_PLOT_STRIDE = int(os.environ.get("PIPELINE_PLOT_STRIDE", 1))
FEBIO_OUTPUT_STRIDE = int(os.environ.get("PIPELINE_OUTPUT_STRIDE", 1))


# FreeCAD settings

# commands used by main.py
# environment variables can point to installations in another location
LOCAL_FREECAD_APPIMAGE = (
    ROOT / ".tools" / "freecad-appimage" / "squashfs-root" / "AppRun"
)

if "FREECAD_COMMAND" in os.environ:
    FREECAD_COMMAND = [os.environ["FREECAD_COMMAND"]]
elif LOCAL_FREECAD_APPIMAGE.exists():
    FREECAD_COMMAND = [str(LOCAL_FREECAD_APPIMAGE), "freecadcmd"]
else:
    FREECAD_COMMAND = ["FreeCADCmd"]

FEBIO_COMMAND = os.environ.get("FEBIO_COMMAND", "febio4")


# geometry settings

# options are "solid" and "hollow"
CYLINDER_TYPE = os.environ.get("PIPELINE_CYLINDER_TYPE", "hollow")
CYLINDER_RADIUS = float(os.environ.get("PIPELINE_CYLINDER_RADIUS", 3))
CYLINDER_INNER_RADIUS = float(os.environ.get("PIPELINE_CYLINDER_INNER_RADIUS", 2))
CYLINDER_HEIGHT = float(os.environ.get("PIPELINE_CYLINDER_HEIGHT", 15))


# basic mesh settings

MESH_SIZE = float(os.environ.get("PIPELINE_MESH_SIZE", 0.5))

# use one target mesh size for the cylinder
MESH_SIZE_MIN = MESH_SIZE
MESH_SIZE_MAX = MESH_SIZE
MESH_ELEMENT_ORDER = int(os.environ.get("PIPELINE_MESH_ELEMENT_ORDER", 1))
MESH_FORMAT_VERSION = 4.1


# output paths

STEP_FILE = ROOT / "freecad_step" / "cylinder.step"
MSH_FILE = ROOT / "gmsh_step" / f"{GEOMETRY_NAME}.msh"
FEB_JOB_DIR = ROOT / "febio_step" / "jobs" / GEOMETRY_NAME
COMPRESSION_FEB_FILE = FEB_JOB_DIR / f"compression_{GEOMETRY_NAME}.feb"
PRESSURE_FEB_FILE = FEB_JOB_DIR / f"pressure_{GEOMETRY_NAME}.feb"

if LOAD_CASE == "compression":
    FEB_FILE = COMPRESSION_FEB_FILE
elif LOAD_CASE == "pressure":
    FEB_FILE = PRESSURE_FEB_FILE
else:
    raise ValueError('LOAD_CASE should be either "compression" or "pressure"')


def validate_config():
    """Validate settings that would otherwise fail later in the pipeline."""
    if CYLINDER_TYPE not in {"solid", "hollow"}:
        raise ValueError('CYLINDER_TYPE should be either "solid" or "hollow"')

    if CYLINDER_RADIUS <= 0 or CYLINDER_HEIGHT <= 0:
        raise ValueError("Cylinder radius and height must be positive")

    if (
        CYLINDER_TYPE == "hollow"
        and not 0 < CYLINDER_INNER_RADIUS < CYLINDER_RADIUS
    ):
        raise ValueError(
            "For a hollow cylinder, the inner radius must be between 0 "
            "and the outer radius"
        )

    if LOAD_CASE == "pressure" and CYLINDER_TYPE != "hollow":
        raise ValueError('The pressure load case requires CYLINDER_TYPE = "hollow"')

    if MESH_SIZE_MIN <= 0 or MESH_SIZE_MAX <= 0:
        raise ValueError("Mesh sizes must be positive")

    if MESH_SIZE_MIN > MESH_SIZE_MAX:
        raise ValueError("MESH_SIZE_MIN cannot be larger than MESH_SIZE_MAX")

    if MESH_ELEMENT_ORDER < 1:
        raise ValueError("MESH_ELEMENT_ORDER must be at least 1")

    if YOUNG_MODULUS <= 0 or DENSITY <= 0:
        raise ValueError("Young's modulus and density must be positive")

    if not -1 < POISSON_RATIO < 0.5:
        raise ValueError(
            "POISSON_RATIO must be between -1 and 0.5 for an isotropic "
            "elastic material"
        )

    if FEBIO_TIME_STEPS <= 0 or FEBIO_STEP_SIZE <= 0:
        raise ValueError("FEBio time steps and step size must be positive")
