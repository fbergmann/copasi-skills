---
title: 'COPASI Skills: Agent Skills for COPASI analyses through Basico'
tags:
  - Python
  - systems biology
  - computational modeling
  - simulation
  - COPASI
authors:
  - name: Frank T. Bergmann
    orcid: 0000-0001-5553-4702
    affiliation: "1"
affiliations:
  - name: BioQUANT / Heidelberg University, INF 267, Heidelberg, Germany
    index: 1
date: 10 November 2026
bibliography: paper.bib
---

# Summary

Biochemical models represent biological systems as networks of reactions that describe the production, consumption, and transformation of molecular species over time. These models provide a quantitative framework for analyzing system dynamics and enable computational experiments that complement traditional wet-lab approaches, helping researchers gain mechanistic insight and make predictive assessments of biological behavior. COPASI is a widely used program for simulating and analyzing those models. These tasks are made availabe to Python through Basico. COPASI Skills is a set of instruction files that tell an assistant how to drive Basico for one analysis at a time. Each skill is a directory containing a `SKILL.md` file. A short description at the top tells the assistant when the skill applies, and the rest of the file states which calls to make, which files to write, and which neighboring skill to choose instead. A researcher can ask for example, in ordinary language, for a time course, a fit, or a published model. The assistant follows the matching skill and leaves tables or a report next to the model. The collection is released under a two-clause BSD license from [https://github.com/fbergmann/copasi-skills](https://github.com/fbergmann/copasi-skills).

# Statement of need

The COmplex PAthway SImulator [`COPASI`; @hoops2006copasi; @bergmann_2017] simulates deterministic and stochastic time courses, computes steady states, and runs optimization, parameter estimation, sensitivity analysis, and metabolic control analysis, using SBML [@hucka2003sbml] or its own file format. Basico [@bergmann2023basico] exposes those tasks as Python functions and is the interface a script should call. But an assistant placed in front of COPASI / Basico does not, by itself, know the workflow a modeler expects. This project contributes the procedures that sit on top of both, so that an assistant will follow the same approach in a reliable way.

That procedure now has a shared file format. In October 2025, Anthropic described Agent Skills as directories whose `SKILL.md` file begins with a name and a description [@anthropic2025skills]. The assistant loads those two fields for every installed skill and loads the instructions only when a request matches the description. Anthropic argues that the same pattern suits scientific protocols, because a skill can make an assistant follow a stated procedure, and it demonstrated a skill for quality control of single-cell RNA sequencing data [@anthropic2025lifesciences]. The format is now an open specification. The specification requires the description to say both what the skill does and when to use it, and it treats further files as material to be read only when the instructions ask for them [@agentskills2026]. Scientific skill collections have since packaged that layout for other research software and databases [@kdense2026skills]. But it does not encode the functionality COPASI provides. 

This contribution is a COPASI-specific set of skills encoded in the Agent Skills format. Each description names the question it answers and the skill that should be used instead, so a fit to measurements is not treated as an optimization without data, a request for control coefficients is not treated as a parameter sensitivity, and a model with no steady state is handed to a diagnostic skill.

Anyone can write a `SKILL.md` file that drives COPASI. This collection is published and reviewed by the COPASI authors rather than from an unreviewed prompt. We invite further skills, and invite contributions whenever the present skills fail, so that the procedures can be improved.

# Software design

The main design choice is one skill per analysis. A single skill that described every COPASI task would match almost any modeling question and would load a long text whenever it matched. Separate descriptions stay specific. That matters because the description is the only text the assistant holds for every installed skill, while the body is read after a match [@anthropic2025skills; @agentskills2026]. The body then states the Basico calls, the output files, and the cases that belong to a different skill.

**Note:** As the skills install packages from the Python Package Index, and they create and run Python files, they should be used inside a sandbox.

\autoref{tab:skills} lists the seventeen skills in the collection. Together they cover the path from an empty environment and a published model through simulation and steady state, then through scans, sensitivities, control analysis, optimization, and parameter estimation, and on to structural and stochastic summaries. The overview skill is the one that reads a model and the tasks already configured inside it and writes a linked report, rather than answering a single numerical question.

Where a procedure is easy to improvise badly, the skill directory contains a Python script, and `SKILL.md` tells the assistant when to run it. The setup skill creates a virtual environment and installs `copasi-basico` together with `pandas`. Diagnosis of a missing steady state, and evaluation of a finished parameter estimation, use the same pattern. The author revised those scripts after trying them on real models. The instruction file chooses the script and explains the result. 

Results are CSV tables or, for the model overview, a linked Markdown report that can be archived with the model. The assistant keeps every skill description, opens one `SKILL.md` when a description matches, and follows it into Basico, which calls COPASI and writes the files. The same skills can be installed for more than one assistant, which is why the project does not add a private file format or a second Python API.

Table: The seventeen skills and an example question each one answers. \label{tab:skills}

| Skill | Question it answers |
| --- | --- |
| `copasi-setup` | Is the Python environment able to import Basico? |
| `copasi-model-search` | Which published model should be loaded? |
| `copasi-model-edit` | How should the model be modified for the next analysis? |
| `copasi-model-values` | How should model values be accessed or updated? |
| `copasi-timecourse` | How do the variables move over time? |
| `copasi-steadystate` | What is the steady state, if there is one? |
| `copasi-reach-steadystate` | Why is there no steady state, and what change produces one? |
| `copasi-scan` | How do results change across a parameter scan? |
| `copasi-sensitivity` | Which parameters move a chosen result the most? |
| `copasi-mca` | Which reactions control a flux or a concentration? |
| `copasi-optimization` | Which parameter values minimize or maximize a quantity? |
| `copasi-parameter-estimation` | Which parameter values agree with the measurements? |
| `copasi-parameter-estimation-evaluation` | Is that fit identifiable? |
| `copasi-efm` | Which minimal pathways can carry a steady-state flux? |
| `copasi-lyapunov` | Do nearby trajectories diverge? |
| `copasi-lna` | What is the linear-noise covariance around a steady state? |
| `copasi-model-overview` | What is in this model, and what do its configured tasks report? |


# Target audience

This project is intended for systems biologists, students and instructors using computational models encodable in SBML or COPASI models and who want a repeatable analysis rather than a one-off chat.

The results still have to be checked. COPASI Skills is there to help a modeler's own analysis and to offer suggestions along the way. It is not there so that the thinking can be handed to the assistant. The person who asked for the analysis remains responsible for deciding whether a table, a fit, or a suggested change is meaningful.

Of course, the other consumer is the assistant. The instructions do not depend on one vendor's tool protocol. They simply say which Basico functions to run and which files to write, so any host (like GitHub Copilot, Claude Code, Cursor) that reads the Agent Skills format can load these skills.

# AI usage disclosure

The manuscript and the helper scripts under `skills/` were drafted with Cursor using Grok 4.7 and with GPT-5.6 Sol through Copilot Pro. The author revised both after testing them against real analyses and discussions with team members, and checked the skill inventory, the description of COPASI and Basico, and every citation. The published software does not call a language model when it runs.

# Acknowledgements
FTB thanks the COPASI developers, currently Stefan Hoops, Ursula Kummer, Jürgen Pahle, and Sven Sahle for contribtions and discussions. This work has been possible thanks to LiBiS, the Baden-Württemberg Institute for Bioinformatics Infrastructure, and by the BMBF-funded de.NBI initiative (031L0104A, W-de.NBI-016).

# References
