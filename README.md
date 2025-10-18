# WarfareSTLTools ⚔️

**Version:** 1.5  
**Author:** David – Warfare Workshop  
**Blender Version:** 3.0+

A complete Blender add-on to prepare wargaming miniatures for 3D printing. Includes scaling, base generation, and native STL export.

---

## ✨ Features

### 🎯 Miniature Preparation
- ✅ Scale using real-world measurements or fixed height
- ⚖️ Choose from common wargame scales (1:285, 1:100, 1:56, etc.)
- 🔁 Center and align models to the ground plane (Z=0)
- 🧱 Add rectangular or circular bases with optional beveling
- 🔗 Option to merge or separate base from model

### 💾 STL Export
- 📤 Export to STL with native Python (no dependency on Blender’s STL plugin)
- 🧠 Triangulates mesh and transforms with object matrix
- 📂 Set custom output path via UI

### 🧰 Fully Interactive Panel
- All settings available directly from the sidebar panel:
  - Scale, method, base type and size
  - Merge, bevel, and STL export options
- Access it from **View3D > Sidebar (N) > Warfare Tools**

---

## 📦 Repository Contents

- `warfare_stl_tools/` – Blender add-on package with operators, panel, and utilities.
- `tools/package_addon.py` – helper script to build the distributable ZIP archive.
- `tests/` – lightweight pytest suite validating the pure Python helpers.

---

## 🚀 Installation

1. Build the add-on archive locally with `python tools/package_addon.py` (creates `warfare_stl_tools.zip` in the project root).  
   Alternatively, download the repository ZIP directly from GitHub and install it without unpacking.
2. In Blender go to **Edit > Preferences > Add-ons > Install**.
3. Select the generated `.zip` and enable the add-on.
4. Open the sidebar in the 3D View (press `N`), tab **Warfare Tools**.

---

## 🛠️ Recommended Usage

1. Import or create a model at real-world scale (meters)
2. Set your target scale (e.g. 1:100 for 15mm wargames)
3. Optionally add a base
4. Export as STL for slicing and printing

---

## 🧪 Running Tests

This repository ships with a small automated test suite that covers the pure Python utilities.  
Run the tests locally with:

```bash
pip install pytest
pytest
```

---

## 📝 License

This add-on is released under the **GNU GPL v3**.  
You may use, modify, and redistribute it freely.

---

Created with ❤️ by [Warfare Workshop](https://warfareworkshop.com)
