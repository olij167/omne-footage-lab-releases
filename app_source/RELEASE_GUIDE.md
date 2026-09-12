# Public release format

Public assets are delivered by the existing static-assets Worker on
`https://omne.space/downloads/footage-lab/`. No R2 subscription is used.

`release_files.json` is the explicit inventory of redistributable source files.
The owner builder snapshots those files, stamps the requested code VERSION,
merges the current UI profile, compiles Python, produces internal checksums and
a versioned ZIP, and records source fingerprints in `release_build.json`.
Unlisted Python files cause a build failure, rather than silently disappearing.

A versioned download URL is immutable: always increment the version when code
or UI data change. User preference files are not release inputs. The uploader
is distributed in the separate Owner Customiser workspace only.

The public updater validates package SHA-256, archive paths, the public inventory,
internal file checksums, Python syntax and version before replacing files. The
entry point is replaced last, after other runtime files, with backup/rollback
on handled write errors. This is not a crash-atomic filesystem transaction.

A v0.2.1 client can bootstrap v0.2.2 because the application remains self-contained
in `omne_footage_lab.py` and `ui_profile.json`; future v0.2.2 clients support the
explicit public file inventory. Optional Pillow improves scaling but is not a
new mandatory dependency for older clients.

Checksums are not signatures. Do not describe this mechanism as signed updates.
Keep Cloudflare account security and publication permissions restricted. No
Cloudflare credentials or owner tooling belong in a public application package.


## Runtime baseline

See `SYSTEM_REQUIREMENTS.md`. The current engine is CPU-first; no discrete GPU is required or used by default.
