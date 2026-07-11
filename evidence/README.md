# Public evidence atlas

The atlas records exactly what each public source can support at a stated cutoff. It is not a catalog of everything the private system contains.

## Record contract

Records conform to [`schemas/public-evidence.schema.json`](../schemas/public-evidence.schema.json) and are listed in [`manifest.yaml`](manifest.yaml). The manifest uses JSON syntax, which is valid YAML, so the validator can remain dependency-free.

Each record states:

- a stable evidence ID and title;
- evidence class and lineage;
- verification date and evidence cutoff;
- allowlisted public sources;
- precise supported claims;
- consumer and outcome when verified;
- verification methods and limitations;
- public sensitivity and current status.

An `internally_corroborated` record contains no private locator. It may have an empty `public_sources` list and must use `public_derived` sensitivity. All other evidence classes require at least one public HTTPS source.

## Adding a record

1. Verify the current system of record directly.
2. Add one JSON-compatible YAML file under `evidence/records/`.
3. Add its relative path to `manifest.yaml`.
4. Run `python3 tools/validate_evidence.py` and `python3 -m unittest discover -s tests`.
5. Complete the factual and disclosure reviews for the exact revision.

Chapter claims cite records with `[@evidence:artifact.example-id]`. Any paragraph in a numbered chapter that links to a GitHub artifact must contain at least one valid evidence citation in that same paragraph. A citation proves only the claims enumerated by its record; it is not a blanket endorsement of the paragraph.

Do not add a private-evidence directory, restricted locator, raw source, real sensitive test value, or private repository content anywhere in this repository.
