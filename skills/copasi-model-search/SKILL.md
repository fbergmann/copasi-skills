---
name: copasi-model-search
description: Searches BioModels and JWS Online for published models with copasi-basico, building each BioModels call to search_for_model in the BioModels search syntax, then loads a chosen SBML model. Use when asked to find, search, or download an existing published model, a BioModels or biomodel id, a curated or non-curated model, or a JWS Online model. Not for editing a local model or running an analysis.
---

# Searching published models

Requires the `.venv` from `copasi-setup`. Needs network access to BioModels and JWS Online. References: https://basico.readthedocs.io/en/latest/notebooks/Accessing_Models_from_Databases.html and https://www.biomodels.org/user-guide/model_search.html

BioModels is the default database. Use JWS Online when the user names JWS, a JWS slug, or a species or reaction known from that collection.

## BioModels

```python
import basico.biomodels as biomodels
from basico import load_biomodel
```

### Query syntax

`search_for_model` sends `query` unchanged (spaces are URL-encoded). Write `query` in the [BioModels search syntax](https://www.biomodels.org/user-guide/model_search.html), the same language as the biomodels.org search box.

| Element | Use | Example |
|---|---|---|
| `" "` | Exact phrase | `"MAPK cascade"` |
| `AND` `OR` `NOT` | Combine terms | `"MAPK cascade" AND cancer` |
| `( )` | Group | `(mapk OR mapk3) AND ERK` |
| `*` | Wildcard | `mapk*` |
| `field:term` | Restrict to one field | `description:dopamine` |

Quote a field value that contains a space: `curationstatus:"Manually curated"`. Escape a character that is syntax when it is part of the text: `+ - && || ! ( ) { } [ ] ^ " ~ * ? : \`. Example: `name:\(EGFR overexpression\)`.

| Field | Example |
|---|---|
| `curationstatus` | `curationstatus:"Manually curated"` or `curationstatus:"Non-curated"` |
| `modelformat` | `modelformat:"SBML"` |
| `modellingapproach` | `modellingapproach:"Ordinary differential equation model"` (also `"Constraint-based model"`, `"Logical model"`, `"Petri net"`) |
| `name` | `name:"Diabetes"` |
| `description` | `description:"Parkinson"` |
| `submitter` | `submitter:"Sheriff"` |
| `publication_authors` | `publication_authors:"Dalle Pezze"` |
| `pubmed_title` | `pubmed_title:"Ultrasensitivity in the mitogen-activated protein kinase cascade"` |
| `PUBMED` | `PUBMED:"27869123"` |
| `TAXONOMY` | `TAXONOMY:9606` (Homo sapiens) |
| `disease` | `disease:"Down Syndrome"` |
| `GO` | `GO:GO:0016049` |
| `CHEBI` | `CHEBI:CHEBI:15343` |
| `UNIPROT` | `UNIPROT:P30084` |
| `ENSEMBL` | `ENSEMBL:ENSG00000111640` |
| `modelflag` | `modelflag:"Non Miriam"` (also `"Non Kinetic"`, `"Sbml Extended"`) |

Build the narrowest query that matches the request: a title, author, organism, disease, or identifier goes in its field; a multi-word name goes in quotes; a model meant to be loaded into COPASI adds `modelformat:"SBML"`. Curated entries use `curationstatus:"Manually curated"`; non-curated entries use `curationstatus:"Non-curated"`. A bare word searches the whole record and is reserved for a general keyword such as `glycolysis` or `repressilator`.

### Search, inspect, load

1. If the user already gave an id, skip the search. A curated id is an integer (`206`) or a `BIOMD…` string (`BIOMD0000000206`). A non-curated id is the full `MODEL…` string. An integer is formatted as `BIOMD` plus ten digits, so a `MODEL…` id stays a string.
2. Otherwise call `biomodels.search_for_model(query, offset=0, num_results=10, sort='id-asc')`. It returns a list of dicts with `id`, `name`, `format`, `submitter`, `submissionDate`, `lastModified`, and `url`. The function returns that page only; the database `matches` count is dropped. The API treats `num_results` below 10 as 10. When the list length equals `num_results`, fetch the next page with `offset` increased by that length, and raise `num_results` to take a larger page. Stop paging once the user has the models they asked for.
3. `sort` is `<field>-<asc|desc>`. Working values: `id-asc` (default), `id-desc`, `name-asc`, `name-desc`, `first_author-asc`, `first_author-desc`, `publication_year-asc`, `publication_year-desc`, `relevance-desc`. The default `id-asc` lists `BIOMD…` ids before `MODEL…` ids, so the first page of a broad query is mostly curated. An unrecognized sort is ignored and the API orders by relevance.
4. Report each hit as id, name, format, submitter, and url. State which query was sent. When a full page came back, say that further hits exist.
5. For one chosen model, read `biomodels.get_model_info(model_id)`. Summarize `name` and `description` (`description` is the SBML notes as XHTML). The main file is `info['files']['main'][0]` (`name`, `fileSize` in bytes). `get_files_for_model(model_id)` returns the same file lists.
6. Load an SBML model with `load_biomodel(model_id)`, which downloads the main file and sets it as the current model. Confirm the load with `basico.overview()`, which returns the model name and the compartment, species, parameter, and reaction counts. `get_content_for_model(model_id, file_name=None)` returns that file as text when the SBML itself is needed; omit `file_name` to take the main file.
7. Keep the model in memory. When the user asks for a file, save with `basico.save_model(path)` to a new path and reload it to confirm.

Done when the reported hits come from the query that was sent, every listed id is one of those hits, and a requested load reads back a model name.

```python
biomodels.search_for_model('glycolysis')
biomodels.search_for_model('kummer2000')
biomodels.search_for_model('Hodgkin AND curationstatus:"Non-curated"')
biomodels.search_for_model('"MAPK cascade" AND curationstatus:"Manually curated" AND modelformat:"SBML"')
info = biomodels.get_model_info(206)
load_biomodel(206)
```

## JWS Online

```python
import basico.jws_online as jws
from basico import load_model_from_string
```

Search by species or reaction name, then read the manuscript before loading.

- `jws.get_models_for_species('atp')` and `jws.get_models_for_reaction('pfk')` return models whose `slug` identifies the entry.
- `jws.get_manuscript(slug)` has `title` and `abstract`. `jws.get_model_info(slug)` has `name`, `status`, `species_set`, and `reaction_set`.
- `jws.get_sbml_model(slug)` returns the SBML string. Load it with `load_model_from_string(sbml)`.
- `jws.get_all_models()` downloads the whole catalog and is slow. Use it when a species or reaction search cannot express the request.

Done when each reported slug was returned by the search, and a requested load reads back that slug's model.

## Gotchas

- `search_for_model` applies no curation filter of its own. Add `curationstatus:…` to restrict the set. The first page under `id-asc` is not the full result.
- Pass `MODEL…` ids as strings to `get_model_info`, `get_content_for_model`, and `load_biomodel`.
- Load SBML. A hit whose `format` is not SBML stays a search result; `load_biomodel` expects the main SBML file.
- `fileSize` is the value from the JSON, in bytes.
- JWS slugs (`wolf`, `teusink`) are not BioModels ids, and the BioModels query syntax does not apply to `get_models_for_species` or `get_models_for_reaction`.
