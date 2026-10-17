# ⌨️ Laptop Swipe (Swipe Type for macOS)

[![macOS](https://img.shields.io/badge/macOS-Sonoma%20%7C%20Sequoia%20%7C%20Ventura-black?logo=apple)](https://apple.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Release-brightgreen)]()

Bring **smartphone-style continuous swipe typing (glide typing)** to physical MacBook and Apple Magic Keyboards! 

Instead of pecking keys one by one, simply **slide your finger across physical keys** on your laptop keyboard. Laptop Swipe tracks your finger's physical trajectory across the QWERTY matrix, detects geometric direction turns (inflections), and replaces the brushed keys with the intended word in **under 2 milliseconds**.

---

## 🌟 Key Features

* 🖐️ **Hands-Free Continuous Detection**: No need to hold any modifier keys! Simply slide your finger across the physical keys and **pause for ~0.35s** or **tap Spacebar**—the app automatically decodes and types the word.
* 🖥️ **Native macOS Menu Bar App**: Lives discreetly in your menu bar (`⌨️ ON`), toggleable with a single click or keyboard shortcut (`Cmd + Option + S`).
* ⚡ **Ultra-Fast Offline Engine (< 2ms)**: Powered by a spatial geometry decoder and an authoritative 9,300+ frequency-ranked vocabulary. 100% private with zero network calls required.
* 📐 **Physical Spatial Inflection Engine**: Calculates vector angles and velocity changes across physical key coordinates to identify intentional target keys versus brushed bystander keys.
* 🎯 **Exact Word Priority**: Explicit typed words (like `menu`, `app`, `text`, `code`, `bar`) are recognized immediately without unintended auto-replacement.
* 🤖 **Optional Gemini 2.5 Flash AI Mode**: Set `GEMINI_API_KEY` in your environment to enable advanced generative multi-word gesture decoding (e.g. `hgrertyhjklothgrere` $\rightarrow$ `hello there`).
* 🚀 **Launch at Login**: Enable automatic background startup directly from the menu bar dropdown.

---

## 📥 Installation

### Option 1: Standalone macOS App (Recommended)

1. Download **[`LaptopSwipe-Installer.dmg`](LaptopSwipe-Installer.dmg)** from this repository (or from [Releases](https://github.com/Ahmed-Farook/swipe-type/releases)).
2. Double-click the DMG and drag **Laptop Swipe.app** into your **`/Applications`** folder.
3. Open **Laptop Swipe.app** from Spotlight or Applications.
4. Grant the required permissions when prompted (see [macOS Permissions](#-macos-permissions-setup) below).

---

### Option 2: Run from Source (Developers)

```bash
# 1. Clone the repository
git clone https://github.com/Ahmed-Farook/swipe-type.git
cd swipe-type

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify local tests
python test_swipe.py

# 5. Launch the Menu Bar App
python main.py
```

> **Optional AI Mode**:
> ```bash
> export GEMINI_API_KEY="your-gemini-api-key"
> python main.py
> ```

---

## 🔒 macOS Permissions Setup

Because macOS protects keyboard input and simulated keystrokes for system security, Laptop Swipe requires two standard permissions:

1. **Accessibility (`AXIsProcessTrusted`)**: Needed to backspace the noisy brushed characters and inject the clean decoded word.
2. **Input Monitoring (`CGEventTap`)**: Needed to detect continuous keyboard slides when typing into other applications (Notes, Chrome, Slack, etc.).

### How to enable:
1. Open **System Settings** $\rightarrow$ **Privacy & Security**.
2. Click **Accessibility** $\rightarrow$ ensure **Laptop Swipe** (or your Terminal / Python if running from source) is toggled **ON** ✅.
3. Click **Input Monitoring** $\rightarrow$ ensure **Laptop Swipe** is toggled **ON** ✅.

> 💡 *Note: If you recompile or update the binary, macOS may require you to toggle the permission OFF and ON once to refresh the binary code-signature trust.*

---

## 🎮 How to Use

1. Ensure the menu bar icon shows **`⌨️ ON`**.
2. Click into any text field, document, or browser prompt box.
3. **Slide your finger** across your physical keys in a continuous motion:
   * **Gesture Example**: Slide across `t` $\rightarrow$ `g` $\rightarrow$ `h` $\rightarrow$ `i` $\rightarrow$ `u` $\rightarrow$ `y` $\rightarrow$ `d` $\rightarrow$ `s`.
4. Trigger word decoding:
   * **Option A (Pause)**: Lift your finger and pause for **0.35s**.
   * **Option B (Spacebar)**: Tap **Spacebar** immediately after sliding.
   * **Option C (Right Shift)**: Hold **Right Shift** while sliding, and release it when finished.
5. The noisy characters disappear and the clean word (**`this `**) is typed instantly!

### Quick Controls:
* **Toggle Swipe Typing ON / OFF**: Click the menu bar item $\rightarrow$ click **Turn OFF**, or press **`Cmd + Option + S`**.
* **Check Last Decoded Word**: Open the menu bar dropdown to see `Last Swiped: "<word>"`.
* **Quit App**: Click menu bar icon $\rightarrow$ **Quit Laptop Swipe** (`Cmd + Q`).

---

## 🧠 How It Works (Under the Hood)

Laptop Swipe is engineered specifically for physical laptop keyboards rather than capacitive touchscreens:

```
[Physical Slide on Keyboard]
           │
           ▼
[Low-Level Quartz Event Tap]  <── Captures raw brushed keys (e.g. "tghiuytds")
           │
           ▼
[Spatial Inflection Engine]   <── Analyzes (x, y) vectors & angular turns
           │
           ▼
[Candidate Scoring Pipeline]  <── Continuous Inverse-Rank Frequency Curve
           │                      + Exact Subsequence LCS Check
           │                      + Stream Coverage Ratio Bonus
           │                      + Exact Boundary (Start/End) Match
           ▼
[Clean Text Replacement]      <── Quartz Backspace + Unicode Virtual Key Injection
```

### 1. Physical Keyboard Matrix (`spatial_engine.py`)
Each QWERTY key is mapped to precise 2D coordinates $(x, y)$ accounting for physical keyboard row offsets (staggered layouts).

### 2. Angular Inflection Detection
When sliding across a physical keyboard, your finger slows down and changes direction abruptly over intended letters:
$$\vec{v}_1 = P_i - P_{i-1}, \quad \vec{v}_2 = P_{i+1} - P_i$$
$$\text{cross\_product} = \vec{v}_1 \times \vec{v}_2$$
Keys where angular direction shifts significantly are flagged as **high-probability anchor letters**.

### 3. Continuous Inverse-Rank Frequency Weighting (`decoder.py`)
Common words are given priority via a smooth inverse-rank distribution:
$$\text{frequency\_score} = \frac{140.0}{1.0 + \frac{\text{rank}}{250.0}}$$
* Top 100 everyday English words receive **+100 to +140 bonus points**.
* Full gesture coverage bonus: $\text{coverage} = \frac{\text{len}(word)}{\text{len}(stream)} \times 60.0$.
* Exact character matches (`menu` $\rightarrow$ `menu`) receive an immediate **+100 point** priority boost.

---

## 📦 Building the Standalone App & DMG

If you modify the source code and wish to build a new `.app` bundle and `.dmg` installer:

```bash
# 1. Build the .app bundle with PyInstaller
pyinstaller --noconfirm LaptopSwipe.spec

# 2. Package into a distributable compressed DMG
hdiutil create -volname "Laptop Swipe Installer" \
  -srcfolder "dist/Laptop Swipe.app" \
  -ov -format UDZO "LaptopSwipe-Installer.dmg"
```

The resulting `LaptopSwipe-Installer.dmg` will be ready for distribution.

---

## 🧪 Verification & Testing

Run the included automated verification suite:

```bash
python test_swipe.py
```

Test results:
| Raw Brushed Keystrokes | Output | Expected | Result |
| :--- | :--- | :--- | :---: |
| `tghiuyds` | `this` | `this` | ✅ |
| `hgertjklo` | `hello` | `hello` | ✅ |
| `thgrere` | `there` | `there` | ✅ |
| `noiuyt` | `not` | `not` | ✅ |
| `menu` | `menu` | `menu` | ✅ |
| `bvfrewasdrtgh` | `breadth` | `breadth` | ✅ |
| `twwerjklbvcde` | `twelve` | `twelve` | ✅ |
| `cvouhngt` | `count` | `count` | ✅ |
| `crazxdfty` | `crazy` | `crazy` | ✅ |
| `lonbfderhjklkuy` | `lonely` | `lonely` | ✅ |

---

## 📄 License

MIT License. Feel free to use, modify, and distribute.
