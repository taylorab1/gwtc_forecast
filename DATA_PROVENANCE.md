# Data provenance policy

Every raw file is identified by:

- Zenodo record ID and DOI;
- release version when exposed by Zenodo;
- exact filename;
- byte size;
- official MD5 checksum;
- local destination;
- retrieval timestamp.

The resolved download plan is written to the external `manifests/` directory.
Raw inputs are immutable. Derived contracts must include source paths, source
checksums, analysis labels, coordinate conventions, software version, and a
creation timestamp.

Deletion of a large raw PE file is allowed only after:

1. its compact processed contract has passed round-trip validation;
2. the contract records the official checksum;
3. the raw file can be redownloaded from the pinned record;
4. the deletion is documented in an external manifest.
