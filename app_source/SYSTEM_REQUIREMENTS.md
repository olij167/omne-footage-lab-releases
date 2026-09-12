# OmN-e Footage Lab — System Requirements

OmN-e Footage Lab is intentionally CPU-first. A discrete graphics card is not
required and GPU acceleration is not used by the default processing pipeline.

## Minimum practical baseline

- 64-bit desktop operating system.
- 2 CPU cores, roughly 2 GHz or better.
- 4 GB RAM.
- Integrated graphics or any normal desktop display adapter.
- 1280 × 720 display.
- At least 2 GB free application/temp space, plus enough free space for the
  converted media you choose to create.
- FFmpeg/FFprobe (bundled inside native Windows/macOS packages; system-provided
  in the Linux/source package).

## Recommended

- 4 or more modern CPU cores.
- 8 GB RAM or more.
- SSD storage.
- 1920 × 1080 display or larger.

No CUDA, Metal-compute, discrete Radeon/GeForce GPU, or dedicated video card is
required. Integrated Intel, AMD or Apple graphics are sufficient for the UI.

## Performance expectations

The interface itself is lightweight. Workload is dominated by FFmpeg and varies
with the operation:

- Lossless minimal clipping (`-c copy`) is primarily storage/I/O bound and is
  suitable for older processors.
- H.264 glitch derivatives, blur, displacement, temporal echo and repeated codec
  generations are CPU-bound and may run slower than real time on older CPUs.
- Motion interpolation (`minterpolate`) is the most expensive built-in effect
  and can be several times slower than real time on low-power or older systems.
- Preview mode deliberately uses a smaller proxy/fewer frames so the editor
  remains practical on integrated-graphics laptops and older processors.

Footage Lab processes one batch job at a time by design, avoiding multiple FFmpeg
encodes competing for CPU, RAM and disk bandwidth.

## Platform targets

- Linux/source: currently validated on the Ubuntu/Zorin family.
- Windows native: Windows 10/11 64-bit x64 is the primary public target.
- macOS native: Apple Silicon and Intel builds are produced separately.
  Final minimum macOS-version claims should be based on real-device testing of
  the generated signed/notarized artifacts before public promotion.

The exact native installer compatibility floor can be tightened later without
changing the processing model.
