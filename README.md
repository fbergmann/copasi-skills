[![DOI](https://zenodo.org/badge/1430839836.svg)](https://doi.org/10.5281/zenodo.24196851)

## COPASI Skills

This project hosts skills, to enable AI to run COPASI sensibly. The skills are written in an agnostic manner, so they will work with all AIs. As such it uses the [SKILL.md](https://skillmd.com/docs/format) format.

## Available skills

| Skill | Use for |
|---|---|
| [copasi-setup](skills/copasi-setup/SKILL.md) | Creating the `.venv` with `copasi-basico` and `pandas` |
| [copasi-timecourse](skills/copasi-timecourse/SKILL.md) | Simulating a model over time |
| [copasi-steadystate](skills/copasi-steadystate/SKILL.md) | Computing steady states |
| [copasi-reach-steadystate](skills/copasi-reach-steadystate/SKILL.md) | Diagnosing a model with no steady state and finding changes that give one |
| [copasi-optimization](skills/copasi-optimization/SKILL.md) | Minimizing or maximizing a model quantity by varying parameters |
| [copasi-parameter-estimation](skills/copasi-parameter-estimation/SKILL.md) | Fitting parameters to experimental data |
| [copasi-sensitivity](skills/copasi-sensitivity/SKILL.md) | Sensitivity of results to parameters |
| [copasi-mca](skills/copasi-mca/SKILL.md) | Metabolic control analysis (elasticities, control coefficients) |
| [copasi-efm](skills/copasi-efm/SKILL.md) | Elementary flux modes (minimal pathways and futile cycles) |
| [copasi-lyapunov](skills/copasi-lyapunov/SKILL.md) | Computing and interpreting Lyapunov exponents |
| [copasi-lna](skills/copasi-lna/SKILL.md) | Linear Noise Approximation covariance and reduced matrices |
| [copasi-model-overview](skills/copasi-model-overview/SKILL.md) | Compiling model structure, COPASI task results, and plots into a linked Markdown report |
| [copasi-model-values](skills/copasi-model-values/SKILL.md) | Inspecting and changing existing model values safely with Basico |
| [copasi-model-edit](skills/copasi-model-edit/SKILL.md) | Creating models and editing reactions, kinetics, events, and annotations |
| [copasi-model-search](skills/copasi-model-search/SKILL.md) | Searching BioModels and JWS Online and loading a published model |
| [copasi-scan](skills/copasi-scan/SKILL.md) | Configuring and running COPASI parameter scan tasks |

The task skills expect the environment from `copasi-setup`. They use the Python package [`copasi-basico`](https://basico.readthedocs.io) (not `basico`), so Python 3 is required.

## Installing

### With `npx skills`

Requires Node.js 22.20 or later.

```bash
npx skills add fbergmann/copasi-skills                              # choose skills and agents
npx skills add fbergmann/copasi-skills --skill copasi-steadystate   # one skill
npx skills add fbergmann/copasi-skills -g                           # available in all projects
npx skills update                                             # update installed skills
```

Install `copasi-setup` together with the skills that you use. Installing a single skill does not pull it in.


### Antigravity

Note that the above step didn't work for antigravity. There you'd additionally: 

 - Register via Global skills.json (Recommended)

Antigravity supports global JSON manifests to explicitly load skills stored in custom locations.

Open or create the global configuration file:

    * Windows: %USERPROFILE%\.gemini\config\skills.json
    * macOS / Linux: ~/.gemini/config/skills.json

Add ~/.agents/skills to the entries list:

```json
{
  "entries": [
    {
      "path": "~/.agents/skills"
    }
  ]
}
```

Antigravity automatically resolves ~/ to your home directory and scans each subdirectory inside ~/.agents/skills one level deep.

Alternatively, you can link `~/.agents/skills` into the standard global discovery directory:

Windows:

```bat
mkdir "%USERPROFILE%\.gemini\config"
mklink /J "%USERPROFILE%\.gemini\config\skills" "%USERPROFILE%\.agents\skills"
``

macOS / Linux:

```bash
mkdir -p ~/.gemini/config
ln -s ~/.agents/skills ~/.gemini/config/skills
```

then create a new conversation in antigravity and copasi setup should work. 

### Manually

Each skill is a folder containing a `SKILL.md`. Copy or link the folders from `skills/` into the skills directory of your tool.

| Tool | Project install | Personal install |
|---|---|---|
| GitHub Copilot / VS Code | `.github/skills/` or `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |

Example (PowerShell, project install for Copilot):

```powershell
Copy-Item -Recurse skills\copasi-* .github\skills\
```

Reload the tool afterwards so it picks up the new skills.

## Using

Ask in plain language and put the model file in the request. The skill is chosen from its description, so no command is needed.

- "Simulate `model.cps` from 0 to 100 and save the trajectory." (`copasi-timecourse`)
- "Does `model.cps` have a steady state? Give the concentrations and fluxes." (`copasi-steadystate`)
- "Maximize flux through R3 in `model.cps` by varying k1 to k4 between 0.01 and 10." (`copasi-optimization`)
- "Fit the rate constants in `model.cps` to `data.csv`." (`copasi-parameter-estimation`)
- "Which parameters most influence [X] at steady state?" (`copasi-sensitivity`)
- "Which reactions control the flux of R4?" (`copasi-mca`)
- "Why does `model.cps` have no steady state, and what is the smallest change that gives one?" (`copasi-reach-steadystate`)
- "List the elementary flux modes of `model.cps` and point out any futile cycles." (`copasi-efm`)
- "Compute the Lyapunov exponents for `model.cps` and interpret the spectrum." (`copasi-lyapunov`)
- "Compute the Linear Noise Approximation for `model.cps` and export its covariance matrices." (`copasi-lna`)
- "Set the initial value of a model parameter in `model.cps` and verify it." (`copasi-model-values`)
- "Create a model with the reaction A -> B using Michaelis-Menten kinetics and add an event at time 30 that sets the concentration of A to 2." (`copasi-model-edit`)
- "Find a curated SBML model of glycolytic oscillations and load it." (`copasi-model-search`)
- "Run the configured scan task in `model.cps` and export selected values." (`copasi-scan`)
- "Create a linked Markdown overview of `model.cps`, including COPASI task results and plots." (`copasi-model-overview`)

On the first request, the agent runs `copasi-setup` to create `.venv`. Results are written as CSV files in the working directory (e.g. `simulation_results.csv`, `steadystate_species.csv`, `optimization_results.csv`, `estimation_results.csv`, `sensitivities_scaled.csv`, `mca_flux_control.csv`).

To call a skill explicitly, name it in the request, e.g. "use copasi-steadystate on `model.cps`".




### License

This project is released under the [two clause BSD license](./LICENSE).


### Acknowledgements
This project has been possible thanks to [LiBiS](https://libis.bioquant.uni-heidelberg.de), the Baden-Württemberg Institute for Bioinformatics Infrastructure:

![LiBiS Logo](./.graphics/libis-logo.svg)


and to the BMBF funded [de.NBI](https://www.denbi.de) initiative (031L0104A, W-de.NBI-016):

![de.NBI logo](./.graphics/deNBI_logo.jpg)

