# 🌟 Nodal

A cozy, high-performance nodal playground built with PySide6 — designed with love and a single shared braincell.

Nodal is an exploration of "Cyber-Obsidian" aesthetics, blending the elegance of Windows 11 Mica effects with a tactile, rubbery nodal interface. It serves as a foundation for deep thought, visual organization, and enjoying the process of building software.

---

### ✨ Current State: The Obsidian Arc

- **Mica Integration:** Deep OS-level transparency using Windows HostBackdrop (State 5).
- **The Focus Dial:** A real-time "Abstraction Slider" that balances background diffusion and Gaussian blur.
- **Obsidian Nodes:** Solid, high-contrast sticky notes with dynamic rim lighting and shadow depth.
- **The Nerve System:** Elastic, glowing Bezier connections that stretch and flex with a "rubbery" physical feel.
- **GPU Optimized:** Viewport-syncing blur layers to keep the UI "buttery" at 60fps.

---

### 🚀 Technical Foundation

- **Entry Point:** `main.py`
- **Architecture:** Frameless, multi-layered UI with custom Windows DWM attribute management.
- **Rendering:** Custom `QGraphicsScene` and `QGraphicsView` implementation with optimized software-calculated diffusion layers.

---

### 🚀 How to run

```bash
python main.py