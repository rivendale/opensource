# 3D, CAD and printing

3D creation, CAD, slicers, scans and 3D on the web. 13 projects; 7 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

A code license says nothing about model weights; read each model card.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS) | copy | MIT | Python | 13774 | 2026-06-26 | Image-to-3D and text-to-3D generation that outputs meshes, Gaussian splats or radiance fields; MIT code, but read the license of each model checkpoint and of the components it downloads. |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | copy | Apache-2.0 | Python | 12049 | 2025-07-29 | Framework for NeRF and Gaussian-splat scene capture from photos. |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | copy | MIT | TypeScript | 10307 | 2026-10-05 | Browser editor for cleaning, cropping and compressing Gaussian splat captures before publishing them. |
| [google/model-viewer](https://github.com/google/model-viewer) | copy | Apache-2.0 | TypeScript | 8263 | 2026-10-06 | Web component for displaying 3D models, including AR. |
| [Mesh2Motion/mesh2motion-app](https://github.com/Mesh2Motion/mesh2motion-app) | copy (see note) | MIT (per license file) | TypeScript | 3390 | 2026-10-06 | Browser tool that fits a template skeleton to a glTF model and applies a library of ready animations, then exports glTF for a game engine. **code MIT; its bundled models, rigs and animations are CC0 per the README; GitHub reports no license (NOASSERTION), so re-read both files before copying** |
| [gumyr/build123d](https://github.com/gumyr/build123d) | copy | Apache-2.0 | Python | 3340 | 2026-10-07 | Python CAD library on OpenCascade for parametric parts defined in code, exported to STEP or STL for printing. |
| [dgreenheck/tidewater](https://github.com/dgreenheck/tidewater) | copy | MIT | JavaScript | 1153 | 2026-09-25 | Browser coastal scene built with Three.js and WebGPU: FFT ocean, shoreline waves, caustics and a dynamic sky; a readable example of agent-assisted real-time graphics. |
| [FreeCAD/FreeCAD](https://github.com/FreeCAD/FreeCAD) | library use | LGPL-2.1 | C++ | 34014 | 2026-10-07 | Parametric 3D CAD modeler. |
| [blender/blender](https://github.com/blender/blender) | study only | GPL-2.0-or-later (per license file) | C++ | 20748 | 2026-10-08 | Full 3D creation suite (mirror of the official repo). |
| [OrcaSlicer/OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) | study only | AGPL-3.0 | C++ | 15885 | 2026-10-08 | Multi-brand 3D printer slicer. |
| [openscad/openscad](https://github.com/openscad/openscad) | study only | GPL-2.0-or-later (per license file) | C++ | 10380 | 2026-10-05 | Code-first solid modeling for 3D printing. **carries a linking exception for the CGAL library** |
| [prusa3d/PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) | study only | AGPL-3.0 | C++ | 9389 | 2026-09-21 | Slicer for turning 3D models into printer instructions. |
| [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) | check first | Tencent Hunyuan 3D 2.0 Community License (per license file) | Python | 15033 | 2025-10-28 | Image-to-3D asset generation model and pipeline. |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).

Listed once elsewhere in this repository, so not repeated here:

- [mrdoob/three.js](https://github.com/mrdoob/three.js), in [catalog/engines.md](../../catalog/engines.md): The standard JavaScript library for 3D in the browser over WebGL and WebGPU; most web 3D scenes start here.
