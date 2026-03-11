# Changelog

All notable changes to CoverForge will be documented here.

---

## [1.4.0] - 2025

### Added
- `--no-label` flag: removes the "PLAYLIST" label and repositions the accent bar directly below the playlist name
- When `--no-label` is active, the accent bar automatically matches the full pixel width of the widest text line instead of using a fixed quarter-canvas width

---

## [1.3.0] - 2025

### Added
- `--compress` / `-c` flag: PNG compression level 0–10
  - Levels 0–9: lossless zlib compression — resolution stays 3000×3000 at all levels
  - Level 10: TinyPNG-style lossy palette quantisation (256-colour adaptive palette + Floyd-Steinberg dithering + zlib level 9) — typically 60–80% smaller than level 9 with minimal visual difference
- `--font-size` / `-s` flag: override the auto-fit font size with a specific pixel value on the 3000×3000 canvas (e.g. `--font-size 300`)

---

## [1.2.0] - 2025

### Added
- `--text-pos` / `-x` flag: 9-position text block placement on a 3×3 grid
  - Full names: `bottom-left`, `bottom-center`, `bottom-right`, `center-left`, `center`, `center-right`, `top-left`, `top-center`, `top-right`
  - Two-letter aliases: `bl`, `bc`, `br`, `cl`, `c`, `cr`, `tl`, `tc`, `tr`
  - Additional aliases: `bottom`, `top`, `middle`
- Accent bar and "PLAYLIST" label track the same horizontal alignment as the text block
- For top-zone positions, the decoration (bar + label) renders below the text instead of above
- Non-default text positions are embedded in the output filename (e.g. `_top_right`)

---

## [1.1.0] - 2025

### Added
- `matte` theme (`--theme matte`): fully achromatic palette — pure near-black background with cool silver accents and white glow. No colour. Works with any pattern.
- `--matte` / `-m` flag: flat near-black background, kills all radial glows, increases pattern contrast
  - `carbon` matte mode: two-pass render with dark strand body and bright accent peak layer
  - `hexgrid` matte mode: crisp high-opacity edges, doubled line width, Gaussian blur halo for neon glow effect
  - Vignette strength reduced to 45% in matte mode (vs 68%) so pattern stays visible at edges
- Pattern name is now always included in the output filename when `--pattern` is set explicitly, preventing overwrite collisions when generating multiple variations

### Fixed
- Output filename collision when generating multiple patterns or themes to the same directory

---

## [1.0.0] - 2025

### Added
- Initial release
- 13 colour themes: Cyberpunk, Void Crimson, Glacier Neon, Obsidian Gold, Violet Dusk, Forest Pulse, Rust & Ice, Midnight Rose, Arctic Chrome, Solar Flare, Deep Abyss, Sakura Mist, Toxic Lime
- 9 procedural pattern engines: carbon fibre weave, honeycomb hex grid, plasma field, circuit board traces, starfield bokeh, concentric waves, Voronoi shatter, CRT scanlines, geometric mesh
- `--theme all`: generate every theme in one command (requires `--output` to be a directory)
- `--font` / `-f`: custom font support via `.ttf`/`.otf` file or directory — bold and light weights auto-detected from filename suffixes
- `--output` / `-o`: output to file or directory, auto-creates nested paths
- `--list-themes`: print all theme keys and exit
- `--list-patterns`: print all pattern keys and exit
- Deterministic output — same playlist name always produces the same image via MD5 hash seed
- Smart filenames embedding theme, pattern, position, and matte flag — files never silently overwrite each other
- 3000×3000px PNG output at Spotify's native cover resolution
- Layered composition: background → pattern → geometry → grain → vignette → typography
- Font auto-detection from `~/.fonts/` and system `/usr/share/fonts/` paths
- Auto theme and pattern selection based on playlist name hash (different hash bits used for each to ensure they vary independently)