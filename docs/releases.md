# Immutable releases

Release archives are deterministic projections of one clean Git tree. They
contain every tracked file, including `LICENSE`, `THIRD_PARTY.md`, and
`third_party/MIT-NOTICES.md`, plus a generated manifest that binds the release
version, source tree, paths, modes, and file SHA-256 values.
File modes come from the Git index, so checkout permission drift cannot change
the bytes assembled from an otherwise identical Git tree. Verification
regenerates the complete manifest from tracked Git files and rejects unsafe or
duplicate archive and manifest paths.

From the exact commit that will receive the release tag, run:

```text
make release VERSION=v0.0.10
make release-verify VERSION=v0.0.10
```

`make release` runs the full repository check first and writes the archive and
`SHA256SUMS` to `dist/` by default. Set `OUTPUT_DIR` to write elsewhere. The
builder rejects a dirty tree, symlinks, invalid release versions, and unsafe
tracked paths.

Build the archive twice into separate empty directories and compare both files
before publication. Attach the archive and checksum file to the GitHub release
for the matching immutable tag. Release publication does not install, load, or
execute any skill.
