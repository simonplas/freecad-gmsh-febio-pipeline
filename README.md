# Automated FreeCAD-Gmsh-FEBio pipeline

This repository contains the code for a Bachelor thesis project on automating
finite element simulations. The main workflow connects:

```text
FreeCAD -> STEP -> Gmsh -> MSH -> pyfebio -> FEBio -> XPLT -> HDF5 -> results
```

The reproducible main pipeline uses solid and hollow cylinders. A separate
stent route demonstrates meshing, inner-surface selection and a dynamic FEBio
pressure simulation for an imported STEP geometry.

## Features

- parameterised solid and hollow cylinder generation in FreeCAD;
- three-dimensional Gmsh meshing with named volume and surface regions;
- compression and internal-pressure FEBio model generation with pyfebio;
- command-line FEBio execution and automatic result extraction;
- mesh-convergence, Young's-modulus and cylinder-thickness studies;
- plots generated from the study CSV files;
- a separate imported-stent meshing and pressure-simulation route.

## Requirements

- Python 3.11 or newer;
- FreeCAD with command-line Python support;
- FEBio 4, with the `febio4` executable available;
- the Python packages in `requirements.txt`.

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

The executable locations can be configured when they are not on `PATH`:

```bash
export FREECAD_COMMAND=/path/to/FreeCADCmd
export FEBIO_COMMAND=/path/to/febio4
```

The local development setup may also use
`.tools/freecad-appimage/squashfs-root/AppRun`. The `.tools` directory is not
part of the repository.

## Running the cylinder pipeline

Select the geometry and load case in `config.py`, then run:

```bash
source venv/bin/activate
python main.py
```

The runner performs five steps:

1. generate a cylinder STEP file with FreeCAD;
2. generate and label a Gmsh volume mesh;
3. create the selected FEBio input model;
4. run FEBio;
5. convert the XPLT output to HDF5 and print a result summary.

The main generated files are written to:

```text
freecad_step/cylinder.step
gmsh_step/cylinder.msh
febio_step/jobs/cylinder/
```

Generated geometry, meshes, solver jobs and study results are ignored by Git.

## Configuration

The main settings are in `config.py`:

- geometry: cylinder type, outer radius, inner radius and height;
- mesh: target size, element order and MSH version;
- material: Young's modulus, Poisson's ratio and density;
- load case: compression or internal pressure;
- FEBio: time steps, step size and output stride.

Study scripts temporarily override selected settings through environment
variables. The default configuration file is not rewritten.

FEBio's default automatic time stepper may increase the configured step size
when a simulation converges easily. The number of completed solver increments
can therefore be lower than the configured number of nominal time steps.

## Parameter studies

Each study runs the main compression pipeline repeatedly and writes a CSV file
to `study_results/`:

```bash
python studies/mesh_convergence.py
python studies/youngs_modulus.py
python studies/cylinder_thickness.py
```

Generate all study plots with:

```bash
python studies/make_plots.py
```

## Imported stent route

The included stent input geometry is stored as `stent.step`. It is run
separately because it does not use the FreeCAD cylinder-generation stage:

```bash
python gmsh_step/mesh_stent_selection.py
python febio_step/create_stent_pressure_feb.py
cd febio_step/jobs/stent
febio4 -i pressure_stent.feb
```

The Gmsh script creates a volume mesh and selects the inner and outer
cylindrical surfaces from their geometry. The FEBio script applies pressure to
the labelled inner wall and uses a dynamic analysis without support nodes.
This route demonstrates that the meshing and simulation stages can process the
more complex imported geometry, but it is not yet integrated into `main.py`.
Generating the stent mesh can take several minutes.

## Tests

The lightweight tests check the result calculations without requiring FreeCAD
or FEBio:

```bash
python -m unittest discover -s tests
```

An end-to-end run still requires both external programs because it generates
the geometry, mesh and solver output from scratch.

## Project structure

```text
config.py                         shared pipeline settings
main.py                           cylinder pipeline runner
freecad_step/script.py            cylinder geometry generation
gmsh_step/mesh.py                 cylinder meshing and region labels
gmsh_step/mesh_stent_selection.py imported-stent meshing and selection
febio_step/                       FEBio model and result helpers
studies/                          parameter studies and plotting
tests/                            lightweight calculation tests
```
