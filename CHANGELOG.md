# Changelog

All notable changes to CoverForge will be documented here.

## [1.0.0] - 2025

### Added
- Initial release
- 14 colour themes including Matte Black, Cyberpunk, Obsidian Gold, Glacier Neon and more
- 9 procedural pattern engines: carbon fibre, hex grid, plasma, circuit board, starfield, waves, Voronoi shatter, scanlines, mesh
- `--matte` flag: flat matt black background with high-contrast pattern rendering (enhanced for carbon and hexgrid)
- `--text-pos` flag: 9 text block positions (bottom-left, center, top-right, and all combinations) with two-letter aliases
- `--theme all`: generate every theme in one command
- `--font`: custom font support via file path or directory (auto-detects bold/light weights)
- `--output`: output to file or directory, auto-creates nested paths
- Deterministic output — same playlist name always produces the same image
- Smart filenames embedding theme, pattern, position and matte flag
- 3000×3000px output at Spotify's native cover resolution
