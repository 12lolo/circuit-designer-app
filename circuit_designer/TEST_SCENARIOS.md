# Complete Test Scenarios - Circuit Designer v1.0.0

**Application**: Circuit Designer (ECIS-full)
**Version**: 1.0.0
**Test Date**: ___________
**Tester Name**: ___________
**Platform**: [ ] Windows  [ ] Linux 

---
## Test Legend

- [ ] Not Tested
- [x] Pass
- ❌ Fail
- ⚠️ Partial (works with issues)
- 🔄 Needs Retest

**Priority Levels:**
- 🔴 Critical (Must work)
- 🟡 High (Should work)
- 🟢 Medium (Nice to have)
- 🔵 Low (Edge case)

---

## 1. Application Lifecycle

### 1.1 Application Startup 🔴

| ID     | Test Case                                 | Expected Result                                                          | Status | Notes |
| ------ | ----------------------------------------- | ------------------------------------------------------------------------ | ------ | ----- |
| APP-01 | Double-click app icon                     | App launches within 5 seconds                                            | ✅      |       |
| APP-02 | Launch from command line `python3 app.py` | App starts with no errors                                                | ✅      |       |
| APP-03 | Launch from `./run.sh`                    | App starts with no errors                                                | ✅      |       |
| APP-04 | First launch (no settings)                | App creates default configuration                                        | ✅      |       |
| APP-05 | Launch with existing settings             | Settings are loaded correctly                                            | ✅      |       |
| APP-06 | Main window appears                       | All panels visible: Components, Sandbox, Inspect, Log, Simulation Output | ✅      |       |
| APP-07 | Empty sandbox on startup                  | Sandbox starts clean with no components                                  | ✅      |       |
| APP-08 | Menubar visible                           | File, Edit, View, Simulation, Settings, Help menus present               | ✅      |       |
| APP-09 | Toolbar visible                           | Quick access toolbar with pinned actions visible                         | ✅      |       |
| APP-10 | Window title                              | Shows "ECis-full" or "Circuit Designer"                                  | ✅      |       |

### 1.2 Application Shutdown 🔴

| ID     | Test Case                               | Expected Result                                                                  | Status | Notes |
| ------ | --------------------------------------- | -------------------------------------------------------------------------------- | ------ | ----- |
| APP-11 | Close via X button (no changes)         | App closes immediately                                                           | ✅        |       |
| APP-12 | Close via File → Exit (no changes)      | App closes immediately                                                           | ✅        |       |
| APP-13 | Close with unsaved changes → Save       | Shows "Do you want to save?" → Save → File dialog → Save successful → App closes | ✅        |       |
| APP-14 | Close with unsaved changes → Don't Save | Shows prompt → Don't Save → App closes without saving                            | ✅        |       |
| APP-15 | Close with unsaved changes → Cancel     | Shows prompt → Cancel → App stays open                                           | ✅        |       |
| APP-16 | Alt+F4 (Windows)                        | Same behavior as X button                                                        | ✅        |       |
| APP-17 | Multiple close attempts                 | No crashes or duplicate prompts                                                  | ✅        |       |

---

## 2. User Interface - Panels & Layout

### 2.1 Components Panel Switch:2:1(Left) 🔴

| ID    | Test Case                     | Expected Result                                | Status | Notes |
| ----- | ----------------------------- | ---------------------------------------------- | ------ | ----- |
| UI-01 | Components panel visible      | Panel shows on left side of window             | ✅        |       |
| UI-02 | Available components listed   | Resistor, Vdc, LED, Switch, Ground displayed   | ✅        |       |
| UI-03 | Component icons/names         | Each component has clear label                 | ✅        |       |
| UI-04 | Drag component from panel     | Component follows cursor                       | ✅        |       |
| UI-05 | Component restocks after drag | Component reappears in panel (infinite supply) | ✅        |       |
| UI-06 | Panel resize                  | Drag right edge to resize panel                | ✅        |       |
| UI-07 | Panel minimum width           | Cannot resize smaller than minimum             | ✅        |       |
| UI-08 | Scroll if needed              | If components overflow, scrollbar appears      | ✅        |       |
| UI-09 | Panel collapse/expand         | Can minimize panel to save space               | ✅        |       |

### 2.2 Sandbox / Canvas (Center) 🔴

| ID    | Test Case              | Expected Result                           | Status | Notes |
| ----- | ---------------------- | ----------------------------------------- | ------ | ----- |
| UI-10 | Sandbox visible        | Large central area with grid              | ✅        |       |
| UI-11 | Grid lines visible     | Grid lines show 15x15 placement area      | ✅        |       |
| UI-12 | Border area visible    | 1-cell gray border around placement area  | ✅        |       |
| UI-13 | Border non-interactive | Cannot place components in border         | ✅        |       |
| UI-14 | Grid centered          | Grid centered in sandbox viewport         | ✅        |       |
| UI-15 | Empty sandbox          | Starts with no components                 | ✅        |       |
| UI-16 | Background color       | Light/neutral background color            | ✅        |       |
| UI-17 | Scrollbars appear      | Scrollbars when zoomed in beyond viewport | ✅        |       |
| UI-18 | Cursor changes         | Cursor changes over draggable items       | ✅        |       |

### 2.3 Inspect Panel (Right) 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UI-19 | Inspect panel visible | Panel shows on right side | ✅ | |
| UI-20 | Default state | Shows "No component selected" when nothing selected | ✅ | |
| UI-21 | Component selected | Shows component properties | ✅ | |
| UI-22 | Name field | Editable text field for component name | ✅ | |
| UI-23 | Value field (Resistor) | Shows resistance value, editable | ✅ | |
| UI-24 | Value field (Vdc) | Shows voltage value, editable | ✅ | |
| UI-25 | Value field (LED) | Shows threshold voltage, editable | ✅ | |
| UI-26 | Value field (Switch) | Shows Open/Closed dropdown | ✅ | |
| UI-27 | Value field (Ground) | No value field (not applicable) | ✅ | |
| UI-28 | Orientation field | Dropdown: 0°, 90°, 180°, 270° | ✅ | |
| UI-29 | Position display | Shows grid position (read-only) | ✅ | |
| UI-30 | Real-time updates | Changes reflect immediately in sandbox | ✅ | |
| UI-31 | Wire selected | Shows wire properties (start/end points) | ✅ | |

### 2.4 Log Panel (Bottom Left) 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UI-32 | Log panel visible | Panel shows at bottom left | ✅ | |
| UI-33 | Timestamp on logs | Each log entry has timestamp | ✅ | |
| UI-34 | Component placement logged | "[INFO] Resistor1 added to sandbox" | ✅ | |
| UI-35 | Component selection logged | "[INFO] Resistor selected" | ✅ | |
| UI-36 | Wire connection logged | "[INFO] Wire connected" | ✅ | |
| UI-37 | Simulation start logged | "[INFO] Simulation started" | ✅ | |
| UI-38 | Simulation errors logged | "[ERROR] ..." or "[WARN] ..." | ✅ | |
| UI-39 | Auto-scroll | New logs appear at bottom, auto-scroll | ✅ | |
| UI-40 | Scrollable history | Can scroll up to see old logs | ✅ | |
| UI-41 | Log cleared on restart | Logs don't persist between sessions | ✅ | |
| UI-42 | Copy log text | Can select and copy log entries | ✅ | |

### 2.5 Simulation Output Panel (Bottom Right) 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UI-43 | Output panel visible | Panel shows at bottom right | ✅ | |
| UI-44 | Default state | Shows placeholder or "No simulation results" | ✅ | |
| UI-45 | After simulation | Shows node voltages in text format | ✅ | |
| UI-46 | Node voltage format | "node_name: X.XXV" format | ✅ | |
| UI-47 | Multiple nodes | All nodes listed vertically | ✅ | |
| UI-48 | Scrollable results | Scrollbar if many nodes | ✅ | |
| UI-49 | Selectable text | Can select and copy results | ✅ | |
| UI-50 | Copy output button | Button copies all results to clipboard | ✅ | |
| UI-51 | Clear on new simulation | Old results replaced by new ones | ✅ | |

### 2.6 Splitters & Resize 🟢

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UI-52 | Vertical splitter (left) | Drag to resize Components panel | ✅ | |
| UI-53 | Vertical splitter (right) | Drag to resize Inspect panel | ✅ | |
| UI-54 | Horizontal splitter (bottom) | Drag to resize log/output panels | ✅ | |
| UI-55 | Splitter minimum size | Panels don't collapse below minimum | ✅ | |
| UI-56 | Splitter restore | Position saved and restored between sessions | ✅ | |
| UI-57 | Window resize | All panels resize proportionally | ✅ | |
| UI-58 | Maximize window | Layout adapts to full screen | ✅ | |
| UI-59 | Minimize/restore | Layout preserved after restore | ✅ | |

---

## 3. Components

### 3.1 Component Placement 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-01 | Drag Resistor to empty cell | Resistor placed, snaps to grid | ✅ | |
| COMP-02 | Drag Vdc to empty cell | Vdc placed, snaps to grid | ✅ | |
| COMP-03 | Drag LED to empty cell | LED placed, snaps to grid | ✅ | |
| COMP-04 | Drag Switch to empty cell | Switch placed, snaps to grid | ✅ | |
| COMP-05 | Drag Ground to empty cell | Ground placed, snaps to grid | ✅ | |
| COMP-06 | Drop on occupied cell | Component finds nearest free cell | ✅ | |
| COMP-07 | Drop outside sandbox | Component not placed, no error | ✅ | |
| COMP-08 | Drop in border area | Component not placed (border is forbidden) | ✅ | |
| COMP-09 | Rapid placement (5 components) | All placed without delay | ✅ | |
| COMP-10 | Fill entire grid | Can place components in all 225 cells | ✅ | |
| COMP-11 | Place beyond capacity | Proper warning or behavior | ✅ | |

### 3.2 Component Properties 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-12 | Resistor default name | "Resistor1", "Resistor2", etc. | ✅ | |
| COMP-13 | Resistor default value | "1k" or "1000" ohms | ✅ | |
| COMP-14 | Vdc default name | "Voltage_source1", etc. | ✅ | |
| COMP-15 | Vdc default value | "5V" or "5" volts | ✅ | |
| COMP-16 | LED default name | "LED1", "LED2", etc. | ✅ | |
| COMP-17 | LED default threshold | "1.5V" | ✅ | |
| COMP-18 | Switch default name | "Switch1", etc. | ✅ | |
| COMP-19 | Switch default state | "Closed" or "Open" | ✅ | |
| COMP-20 | Ground default name | "Ground1", etc. | ✅ | |
| COMP-21 | Ground has no value | No value field in inspect panel | ✅ | |
| COMP-22 | Unique numbering | Each component gets unique sequential number | ✅ | |

### 3.3 Component Selection 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-23 | Click component | Red border appears, inspect panel updates | ✅ | |
| COMP-24 | Click another component | First deselects, second selects | ✅ | |
| COMP-25 | Click empty space | Selection clears | ✅ | |
| COMP-26 | Click connection point | Connection point highlights (don't select component) | ✅ | |
| COMP-27 | Ctrl+A (Select All) | All components selected | ✅ | |
| COMP-28 | Escape (Deselect All) | All selections cleared | ✅ | |
| COMP-29 | Multiple selection | Shift+click or drag box selects multiple | ✅ | |
| COMP-30 | Selected component visual | Clear visual indicator (border/highlight) | ✅ | |

### 3.4 Component Rotation 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-31 | Select component → Press R | Rotates 90° clockwise | ✅ | |
| COMP-32 | Rotate 4 times | Returns to 0° (full circle) | ✅ | |
| COMP-33 | Rotate via Inspect panel | Dropdown changes orientation | ✅ | |
| COMP-34 | Orientation values | 0°, 90°, 180°, 270° available | ✅ | |
| COMP-35 | Connection points rotate | Connection points move with rotation | ✅ | |
| COMP-36 | Wires stay connected | Wires adjust to new connection point positions | ✅ | |
| COMP-37 | Rotate without selection | No action, no error | ✅ | |
| COMP-38 | Rotate multiple selected | All selected components rotate | ✅ | |
| COMP-39 | Undo rotation | Ctrl+Z returns to previous orientation | ✅ | |

### 3.5 Component Movement 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-40 | Drag component to empty cell | Moves to new position, snaps to grid | ✅ | |
| COMP-41 | Drag component to occupied cell | Returns to original position | ✅ | |
| COMP-42 | Drag component outside sandbox | Returns to original position | ✅ | |
| COMP-43 | Move connected component | Wires stretch/follow component | ✅ | |
| COMP-44 | Rapid movement | Wires update smoothly, no lag | ✅ | |
| COMP-45 | Undo movement | Ctrl+Z returns to previous position | ✅ | |
| COMP-46 | Move to border area | Not allowed, returns to valid position | ✅ | |

### 3.6 Component Editing 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-47 | Edit Resistor name | Type in Inspect panel → Name updates | ✅ | |
| COMP-48 | Edit Resistor value to "4.7k" | Accepts, parses as 4700 ohms | ✅ | |
| COMP-49 | Edit Resistor value to "1M" | Accepts, parses as 1,000,000 ohms | ✅ | |
| COMP-50 | Edit Resistor value to "100" | Accepts, parses as 100 ohms | ✅ | |
| COMP-51 | Edit Vdc value to "12V" | Accepts, parses as 12 volts | ✅ | |
| COMP-52 | Edit LED threshold | Accepts new threshold voltage | ✅ | |
| COMP-53 | Switch state to "Open" | Dropdown changes to Open | ✅ | |
| COMP-54 | Switch state to "Closed" | Dropdown changes to Closed | ✅ | |
| COMP-55 | Invalid value (text) | Shows error or rejects input | ✅ | |
| COMP-56 | Negative value | Shows error or rejects input | ✅ | |
| COMP-57 | Zero value | Accepts or shows appropriate warning | ✅ | |
| COMP-58 | Very large value | Handles without overflow | ✅ | |
| COMP-59 | Undo value change | Ctrl+Z restores previous value | ✅ | |

### 3.7 Component Deletion 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-60 | Select component → Delete key | Component removed | ✅ | |
| COMP-61 | Delete connected component | Component AND connected wires removed | ✅ | |
| COMP-62 | Delete multiple selected | All selected components removed | ✅ | |
| COMP-63 | Delete via context menu | Right-click → Delete works | ✅ | |
| COMP-64 | Undo deletion | Ctrl+Z restores component | ✅ | |
| COMP-65 | Undo deletion with wires | Ctrl+Z restores component AND wires | ✅ | |
| COMP-66 | Delete without selection | No action, no error | ✅ | |

### 3.8 Component Copy/Paste 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| COMP-67 | Select component → Ctrl+C | Component copied to clipboard | ✅ | |
| COMP-68 | Ctrl+V after copy | Component pasted with offset, new name | ✅ | |
| COMP-69 | Copy multiple components | All selected components copied | ✅ | |
| COMP-70 | Paste multiple | All copied components pasted | ✅ | |
| COMP-71 | Paste preserves properties | Name (with _copy), value, orientation copied | ✅ | |
| COMP-72 | Paste without copy | Nothing happens or appropriate message | ✅ | |
| COMP-73 | Copy via menu Edit → Copy | Same as Ctrl+C | ✅ | |
| COMP-74 | Paste via menu Edit → Paste | Same as Ctrl+V | ✅ | |

---

## 4. Wires & Connections

### 4.1 Wire Creation 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| WIRE-01 | Click connection point A | Point highlights green | ✅ | |
| WIRE-02 | Click connection point B | Wire created A→B, points unhighlight | ✅ | |
| WIRE-03 | Wire visual | Blue line, 3px thickness | ✅ | |
| WIRE-04 | Wire selectable | Can click to select wire | ✅ | |
| WIRE-05 | Selected wire | Turns red, thicker | ✅ | |
| WIRE-06 | Wire hover | Changes color on hover (lighter blue) | ✅ | |
| WIRE-07 | Create multiple wires | All wires render correctly | ✅ | |
| WIRE-08 | Wires don't overlap components | Wires render under components (z-order) | ✅ | |

### 4.2 Wire Validation 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| WIRE-09 | Connect "out" to "out" | Error: "out -> out is not allowed" | ✅ | |
| WIRE-10 | Connect component to itself | Error: "cannot connect component to itself" | ✅ | |
| WIRE-11 | Connect "in" to "out" | Allowed, wire created | ✅ | |
| WIRE-12 | Connect "in" to "in" | Allowed, wire created | ✅ | |
| WIRE-13 | Connect Ground to Resistor | Allowed, wire created | ✅ | |
| WIRE-14 | Connect Vdc to LED | Allowed, wire created | ✅ | |
| WIRE-15 | Click same point twice | Resets selection, no wire | ✅ | |
| WIRE-16 | Click point → click empty space | Resets selection, no wire | ✅ | |

### 4.3 Wire Bend Points 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| WIRE-17 | Right-click wire | Bend point added at click location | ✅ | |
| WIRE-18 | Bend point visual | Small circle/dot at bend location | ✅ | |
| WIRE-19 | Wire segments | Wire splits into segments around bend points | ✅ | |
| WIRE-20 | Drag bend point | Bend point moves, wire adjusts | ✅ | |
| WIRE-21 | Multiple bend points | Can add multiple bends to one wire | ✅ | |
| WIRE-22 | Delete bend point | Right-click bend point → Delete | ✅ | |
| WIRE-23 | Move component with bent wire | Wire and bend points adjust | ✅ | |
| WIRE-24 | Select wire with bends | All segments highlight | ✅ | |
| WIRE-25 | Undo add bend point | Ctrl+Z removes bend point | ✅ | |
| WIRE-26 | Undo delete bend point | Ctrl+Z restores bend point | ✅ | |

### 4.4 Wire Deletion 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| WIRE-27 | Select wire → Delete key | Wire removed | ✅ | |
| WIRE-28 | Delete component with wires | Component and all connected wires removed | ✅ | |
| WIRE-29 | Undo wire deletion | Ctrl+Z restores wire | ✅ | |
| WIRE-30 | Undo wire deletion with bend points | Wire restored with all bend points | ✅ | |
| WIRE-31 | Delete via context menu | Right-click wire → Delete | ✅ | |

### 4.5 Wire Dynamic Behavior 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| WIRE-32 | Move connected component | Wire stretches/adjusts dynamically | ✅ | |
| WIRE-33 | Rotate connected component | Wire reattaches to rotated connection point | ✅ | |
| WIRE-34 | Component with multiple wires | All wires update correctly | ✅ | |
| WIRE-35 | Complex circuit movement | No wire artifacts or disconnections | ✅ | |
| WIRE-36 | Rapid component movement | Wires update smoothly, no lag | ✅ | |

---

## 5. Simulation

### 5.1 Valid Simulations 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| SIM-01 | Simple circuit: Vdc → Resistor → Ground | Simulation succeeds, shows voltages | ✅ | |
| SIM-02 | Voltage divider: Vdc → R1 → R2 → Ground | Shows correct voltage division | ✅ | |
| SIM-03 | LED circuit: Vdc → Resistor → LED → Ground | Shows voltages, LED state updates | ✅ | |
| SIM-04 | Switch circuit (closed) | Current flows, simulation shows values | ✅ | |
| SIM-05 | Switch circuit (open) | No current, shows appropriate values | ✅ | |
| SIM-06 | Parallel resistors | Correct voltage/current values | ✅ | |
| SIM-07 | Series resistors | Correct voltage drops | ✅ | |
| SIM-08 | Complex circuit (10+ components) | Simulation completes successfully | ✅ | |
| SIM-09 | Simulation time | Results appear within 30 seconds | ✅ | |
| SIM-10 | Multiple simulations | Can run simulation multiple times | ✅ | |

### 5.2 LED Behavior 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| SIM-11 | LED above threshold | LED visual changes to ON state | ✅ | |
| SIM-12 | LED below threshold | LED visual shows OFF state | ✅ | |
| SIM-13 | LED exactly at threshold | Defined behavior (ON or OFF) | ✅ | |
| SIM-14 | Change LED threshold → resimulate | LED state updates accordingly | ✅ | |
| SIM-15 | Multiple LEDs | Each LED state calculated independently | ✅ | |

### 5.3 Error Handling 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| SIM-16 | Empty sandbox → Simulate | Error: "No components found in circuit" | ✅ | |
| SIM-17 | No ground → Simulate | Error: "Circuit requires at least one ground component" | ✅ | |
| SIM-18 | No voltage source → Simulate | Error or warning about no power source | ✅ | |
| SIM-19 | Short circuit (Vdc → wire → Ground) | Error: "Short circuit detected" or similar | ✅ | |
| SIM-20 | Invalid component value (0 ohms) | Error or appropriate warning | ✅ | |
| SIM-21 | Disconnected components | Warning or error about unconnected components | ✅ | |
| SIM-22 | Floating nodes | Appropriate error or warning | ✅ | |
| SIM-23 | Simulation failure | Error message displayed in output panel | ✅ | |
| SIM-24 | Error logged | Error appears in log panel | ✅ | |

### 5.4 Simulation Performance 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| SIM-25 | 10 components | Simulation < 5 seconds | ✅ | |
| SIM-26 | 50 components | Simulation < 15 seconds | ✅ | |
| SIM-27 | 100 components | Simulation < 30 seconds | ✅ | |
| SIM-28 | App responsiveness during simulation | UI remains responsive | ✅ | |
| SIM-29 | Cancel simulation (if supported) | Simulation stops gracefully | ✅ | |

---

## 6. Project Management

### 6.1 New Project 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-01 | File → New (no changes) | Creates new empty sandbox immediately | ✅ | |
| PROJ-02 | File → New (with changes) | Shows "Are you sure?" confirmation | ✅ | |
| PROJ-03 | New → Yes | Sandbox cleared, new project started | ✅ | |
| PROJ-04 | New → No | Keeps current sandbox | ✅ | |
| PROJ-05 | Ctrl+N shortcut | Same behavior as File → New | ✅ | |
| PROJ-06 | New project title | Window title updates to "Untitled" or similar | ✅ | |

### 6.2 Save Project 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-07 | File → Save (first time) | File dialog opens | ✅ | |
| PROJ-08 | Choose location → Save | .ecis file created | ✅ | |
| PROJ-09 | File exists on disk | Can find file in file explorer | ✅ | |
| PROJ-10 | File → Save (existing file) | Saves without dialog | ✅ | |
| PROJ-11 | Save As | Always opens file dialog | ✅ | |
| PROJ-12 | Ctrl+S shortcut | Same as File → Save | ✅ | |
| PROJ-13 | Overwrite existing file | Shows confirmation | ✅ | |
| PROJ-14 | Cancel save dialog | No file created/modified | ✅ | |
| PROJ-15 | Unsaved changes indicator | Window title shows * or "unsaved" | ✅ | |
| PROJ-16 | After save, indicator clears | No more unsaved indicator | ✅ | |

### 6.3 Open Project 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-17 | File → Open | Project browser dialog appears | ✅ | |
| PROJ-18 | Project browser shows thumbnails | Each saved project has preview image | ✅ | |
| PROJ-19 | Project browser shows names | Project names clearly visible | ✅ | |
| PROJ-20 | Project browser shows dates | Last modified date visible | ✅ | |
| PROJ-21 | Select project → Open | Project loads into sandbox | ✅ | |
| PROJ-22 | Loaded project matches saved | All components, wires, positions correct | ✅ | |
| PROJ-23 | Component properties restored | Values, names, orientations match | ✅ | |
| PROJ-24 | Wire bend points restored | All bend points preserved | ✅ | |
| PROJ-25 | Ctrl+O shortcut | Opens project browser | ✅ | |
| PROJ-26 | Cancel project browser | Returns to current project | ✅ | |
| PROJ-27 | Browse button | Opens file explorer for external files | ✅ | |

### 6.4 Project Browser Features 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-28 | Search projects | Type name → Projects filtered | ✅ | |
| PROJ-29 | Sort by name (A-Z) | Projects sorted alphabetically | ✅ | |
| PROJ-30 | Sort by name (Z-A) | Projects sorted reverse | ✅ | |
| PROJ-31 | Sort by date (newest) | Most recent first | ✅ | |
| PROJ-32 | Sort by date (oldest) | Oldest first | ✅ | |
| PROJ-33 | Right-click project → Rename | Rename dialog appears | ✅ | |
| PROJ-34 | Rename project → OK | Project name updated | ✅ | |
| PROJ-35 | Rename to existing name | Shows "Name already exists" error | ✅ | |
| PROJ-36 | Right-click project → Delete | Confirmation dialog appears | ✅ | |
| PROJ-37 | Delete → Yes | Project removed from browser | ✅ | |
| PROJ-38 | Delete → No | Project not deleted | ✅ | |
| PROJ-39 | Double-click project | Opens project directly | ✅ | |

### 6.5 Clear / Reset 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-40 | File → Clear | Confirmation dialog appears | ✅ | |
| PROJ-41 | Clear → Yes | All components and wires removed | ✅ | |
| PROJ-42 | Clear → No | Sandbox unchanged | ✅ | |
| PROJ-43 | Clear doesn't affect file | Cleared sandbox not automatically saved | ✅ | |
| PROJ-44 | Undo after clear | Cannot undo clear operation | ✅ | |

### 6.6 File Format & Corruption 🔵

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PROJ-45 | Valid .ecis file structure | JSON format with components, wires | ✅ | |
| PROJ-46 | Open corrupted JSON | Error: "Failed to load project" | ✅ | |
| PROJ-47 | Open non-.ecis file | Error: "Invalid file format" | ✅ | |
| PROJ-48 | Open empty file | Error or empty project | ✅ | |
| PROJ-49 | File permissions issue | Appropriate error message | ✅ | |
| PROJ-50 | Network drive / external storage | Can save/load from external locations | ✅ | |

---

## 7. Undo / Redo System

### 7.1 Undo Operations 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UNDO-01 | Add component → Ctrl+Z | Component removed | ✅ | |
| UNDO-02 | Delete component → Ctrl+Z | Component restored | ✅ | |
| UNDO-03 | Move component → Ctrl+Z | Component returns to original position | ✅ | |
| UNDO-04 | Rotate component → Ctrl+Z | Component returns to original orientation | ✅ | |
| UNDO-05 | Edit value → Ctrl+Z | Original value restored | ✅ | |
| UNDO-06 | Add wire → Ctrl+Z | Wire removed | ✅ | |
| UNDO-07 | Delete wire → Ctrl+Z | Wire restored | ✅ | |
| UNDO-08 | Add bend point → Ctrl+Z | Bend point removed | ✅ | |
| UNDO-09 | Delete component with wires → Ctrl+Z | Component AND wires restored | ✅ | |
| UNDO-10 | Multiple operations → Multiple Ctrl+Z | Each operation undone in reverse order | ✅ | |
| UNDO-11 | Undo at start of history | No action, no error | ✅ | |
| UNDO-12 | Undo via menu Edit → Undo | Same as Ctrl+Z | ✅ | |

### 7.2 Redo Operations 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UNDO-13 | Ctrl+Z → Ctrl+Shift+Z | Operation re-applied | ✅ | |
| UNDO-14 | Undo add → Redo | Component reappears | ✅ | |
| UNDO-15 | Undo delete → Redo | Component deleted again | ✅ | |
| UNDO-16 | Undo move → Redo | Component moves again | ✅ | |
| UNDO-17 | Multiple undo → Multiple redo | All operations re-applied | ✅ | |
| UNDO-18 | Redo at end of history | No action, no error | ✅ | |
| UNDO-19 | Redo via menu Edit → Redo | Same as Ctrl+Shift+Z | ✅ | |
| UNDO-20 | Ctrl+Y alternative | Works as redo (if supported) | ✅ | |

### 7.3 Undo History Management 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| UNDO-21 | New action after undo | Redo history cleared | ✅ | |
| UNDO-22 | Undo limit (50 operations) | Oldest operations removed | ✅ | |
| UNDO-23 | Clear/New project | Undo history cleared | ✅ | |
| UNDO-24 | Open project | Undo history cleared | ✅ | |
| UNDO-25 | Complex operation (delete multi) | Single undo restores all | ✅ | |

---

## 8. View & Navigation

### 8.1 Zoom Operations 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| ZOOM-01 | Ctrl+Scroll up (on canvas) | Zooms in | ✅ | |
| ZOOM-02 | Ctrl+Scroll down (on canvas) | Zooms out | ✅ | |
| ZOOM-03 | Ctrl++ | Zooms in | ✅ | |
| ZOOM-04 | Ctrl+- | Zooms out | ✅ | |
| ZOOM-05 | View → Zoom In | Zooms in | ✅ | |
| ZOOM-06 | View → Zoom Out | Zooms out | ✅ | |
| ZOOM-07 | Ctrl+0 | Resets zoom to 100% | ✅ | |
| ZOOM-08 | View → Reset Zoom | Resets to 100% | ✅ | |
| ZOOM-09 | Zoom buttons in toolbar | +/- buttons work | ✅ | |
| ZOOM-10 | Maximum zoom in | Stops at reasonable maximum | ✅ | |
| ZOOM-11 | Maximum zoom out | Stops at minimum (fits grid) | ✅ | |
| ZOOM-12 | Zoom on empty area | Zooms canvas centered on cursor | ✅ | |
| ZOOM-13 | Zoom on component | Zooms centered on cursor position | ✅ | |
| ZOOM-14 | Scroll outside canvas | Doesn't zoom | ✅ | |

### 8.2 Pan Operations 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PAN-01 | Drag scrollbar horizontal | Canvas moves left/right | ✅ | |
| PAN-02 | Drag scrollbar vertical | Canvas moves up/down | ✅ | |
| PAN-03 | Two-finger touchpad gesture | Canvas pans | ✅ | |
| PAN-04 | Mouse wheel horizontal | Canvas pans horizontally (if supported) | ✅ | |
| PAN-05 | Arrow keys | Canvas pans in direction | ✅ | |
| PAN-06 | Middle mouse button drag | Canvas pans (if supported) | ✅ | |
| PAN-07 | Pan to edge | Stops at canvas boundary | ✅ | |
| PAN-08 | Center view command | View → Center centers the grid | ✅ | |

### 8.3 View Menu 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| VIEW-01 | View → Zoom In | Works | ✅ | |
| VIEW-02 | View → Zoom Out | Works | ✅ | |
| VIEW-03 | View → Reset Zoom | Works | ✅ | |
| VIEW-04 | View → Center View | Centers grid in viewport | ✅ | |
| VIEW-05 | View → Show Grid | Toggles grid visibility (if supported) | ✅ | |
| VIEW-06 | View → Show Connection Points | Toggles connection point visibility (if supported) | ✅ | |

---

## 9. Keyboard Shortcuts

### 9.1 File Operations 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-01 | Ctrl+N | New project | ✅ | |
| KEY-02 | Ctrl+O | Open project | ✅ | |
| KEY-03 | Ctrl+S | Save project | ✅ | |
| KEY-04 | Ctrl+Shift+S | Save As (if supported) | ✅ | |

### 9.2 Edit Operations 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-05 | Ctrl+Z | Undo | ✅ | |
| KEY-06 | Ctrl+Shift+Z | Redo | ✅ | |
| KEY-07 | Ctrl+Y | Redo (alternative) | ✅ | |
| KEY-08 | Ctrl+C | Copy selected | ✅ | |
| KEY-09 | Ctrl+V | Paste | ✅ | |
| KEY-10 | Ctrl+X | Cut (if supported) | ✅ | |
| KEY-11 | Delete | Delete selected | ✅ | |
| KEY-12 | Backspace | Delete selected (alternative) | ✅ | |
| KEY-13 | Ctrl+A | Select all | ✅ | |
| KEY-14 | Escape | Deselect all | ✅ | |

### 9.3 Component Operations 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-15 | R | Rotate selected component | ✅ | |
| KEY-16 | Ctrl+R | Rotate (alternative) | ✅ | |

### 9.4 View Operations 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-17 | Ctrl++ | Zoom in | ✅ | |
| KEY-18 | Ctrl+= | Zoom in (alternative) | ✅ | |
| KEY-19 | Ctrl+- | Zoom out | ✅ | |
| KEY-20 | Ctrl+0 | Reset zoom | ✅ | |
| KEY-21 | Arrow keys | Pan view | ✅ | |

### 9.5 Simulation Operations 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-22 | F5 | Run simulation | ✅ | |
| KEY-23 | Ctrl+R | Run simulation (if R not used for rotate) | ✅ | |

### 9.6 Application 🔴

| ID | Shortcut | Expected Action | Status | Notes |
|----|----------|-----------------|--------|-------|
| KEY-24 | Ctrl+Q | Quit application (if supported) | ✅ | |
| KEY-25 | Alt+F4 | Close window (Windows) | ✅ | |
| KEY-26 | F1 | Help (if supported) | ✅ | |

---

## 10. Menus & Dialogs

### 10.1 File Menu 🔴

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-01 | File → New | New project dialog/action | ✅ | |
| MENU-02 | File → Open | Project browser opens | ✅ | |
| MENU-03 | File → Save | Saves project | ✅ | |
| MENU-04 | File → Save As | Save with new name | ✅ | |
| MENU-05 | File → Clear | Clear sandbox confirmation | ✅ | |
| MENU-06 | File → Export → PNG | Export dialog opens | ✅ | |
| MENU-07 | File → Exit | Close application | ✅ | |
| MENU-08 | Recent files (if supported) | Shows recent projects | ✅ | |

### 10.2 Edit Menu 🔴

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-09 | Edit → Undo | Undo last action | ✅ | |
| MENU-10 | Edit → Redo | Redo action | ✅ | |
| MENU-11 | Edit → Cut | Cut selected (if supported) | ✅ | |
| MENU-12 | Edit → Copy | Copy selected | ✅ | |
| MENU-13 | Edit → Paste | Paste from clipboard | ✅ | |
| MENU-14 | Edit → Delete | Delete selected | ✅ | |
| MENU-15 | Edit → Select All | Select all components | ✅ | |

### 10.3 View Menu 🟡

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-16 | View → Zoom In | Zooms in | ✅ | |
| MENU-17 | View → Zoom Out | Zooms out | ✅ | |
| MENU-18 | View → Reset Zoom | Reset to 100% | ✅ | |
| MENU-19 | View → Center | Center view on grid | ✅ | |
| MENU-20 | View → Show Grid | Toggle grid (if supported) | ✅ | |
| MENU-21 | View → Quick Access Toolbar | Toggle toolbar visibility | ✅ | |

### 10.4 Simulation Menu 🔴

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-22 | Simulation → Run | Start simulation (F5) | ✅ | |
| MENU-23 | Simulation → Stop | Stop simulation (if supported) | ✅ | |

### 10.5 Settings Menu 🟡

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-24 | Settings → Edit Shortcuts | Shortcuts dialog opens | ✅ | |
| MENU-25 | Settings → Preferences | Preferences dialog (if exists) | ✅ | |

### 10.6 Help Menu 🟢

| ID | Menu Item | Expected Behavior | Status | Notes |
|----|-----------|-------------------|--------|-------|
| MENU-26 | Help → Shortcuts | Shortcuts reference opens | ✅ | |
| MENU-27 | Help → About | About dialog with version | ✅ | |
| MENU-28 | Help → Documentation | Opens README or help | ✅ | |

### 10.7 Quick Access Toolbar 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| QAT-01 | Toolbar visible | Toolbar shows above menus | ✅ | |
| QAT-02 | Pin/unpin actions | Click pin icon → action pinned to toolbar | ✅ | |
| QAT-03 | Pinned actions persist | Toolbar saved between sessions | ✅ | |
| QAT-04 | Unpin action | Click unpin → removed from toolbar | ✅ | |
| QAT-05 | Right-click menu → Quick Access | Can show/hide toolbar | ✅ | |
| QAT-06 | Click toolbar button | Action executes | ✅ | |

### 10.8 Shortcuts Dialog 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| DIALOG-01 | Settings → Edit Shortcuts | Dialog opens with shortcuts list | ✅ | |
| DIALOG-02 | Click shortcut field | Can type new key combination | ✅ | |
| DIALOG-03 | Set duplicate shortcut | Shows warning or prevents | ✅ | |
| DIALOG-04 | Apply button | Saves changes | ✅ | |
| DIALOG-05 | Cancel button | Discards changes | ✅ | |
| DIALOG-06 | Reset to defaults | All shortcuts reset | ✅ | |
| DIALOG-07 | Shortcuts persist | Changes saved between sessions | ✅ | |

---

## 11. Error Handling & Edge Cases

### 11.1 General Errors 🔵

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| ERR-01 | Disk full during save | Clear error message, doesn't crash | ✅ | |
| ERR-02 | Read-only file system | Appropriate error message | ✅ | |
| ERR-03 | Out of memory (large circuit) | Graceful degradation or error | ✅ | |
| ERR-04 | Rapid repeated actions | No crashes, proper queuing | ✅ | |
| ERR-05 | Invalid clipboard data | Paste does nothing or shows error | ✅ | |
| ERR-06 | Concurrent file access | Proper file locking or warning | ✅ | |

### 11.2 UI Edge Cases 🔵

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| EDGE-01 | Resize window to minimum | UI remains usable | ✅ | |
| EDGE-02 | Resize window to maximum | UI scales properly | ✅ | |
| EDGE-03 | Rapid window resize | No crashes, smooth adaptation | ✅ | |
| EDGE-04 | Multiple monitors | Window moves between screens correctly | ✅ | |
| EDGE-05 | High DPI display | UI scales appropriately | ✅ | |
| EDGE-06 | Low resolution display | UI adapts or scrolls | ✅ | |
| EDGE-07 | Component names > 50 chars | Truncated or scrollable | ✅ | |
| EDGE-08 | Very long log history (1000+ entries) | Performance remains good | ✅ | |

### 11.3 Data Edge Cases 🔵

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| EDGE-09 | Resistor value 1e-12 (tiny) | Handled correctly | ✅ | |
| EDGE-10 | Resistor value 1e12 (huge) | Handled correctly | ✅ | |
| EDGE-11 | Voltage 0V | Handled correctly | ✅ | |
| EDGE-12 | Voltage 10000V | Handled correctly | ✅ | |
| EDGE-13 | Circuit with 200+ components | Loads and simulates | ✅ | |
| EDGE-14 | Circuit with 500+ wires | Renders without lag | ✅ | |

---

## 12. Performance & Responsiveness

### 12.1 UI Responsiveness 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PERF-01 | Component drag | No lag, follows cursor smoothly | ✅ | |
| PERF-02 | Wire creation | Instant feedback | ✅ | |
| PERF-03 | Component selection | Highlights immediately | ✅ | |
| PERF-04 | Menu opens | Opens within 100ms | ✅ | |
| PERF-05 | Dialog opens | Opens within 200ms | ✅ | |
| PERF-06 | Zoom operation | Smooth, no jerks | ✅ | |
| PERF-07 | Pan operation | Smooth scrolling | ✅ | |

### 12.2 Load Times 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PERF-08 | Application startup | < 5 seconds | ✅ | |
| PERF-09 | Open small project (< 10 components) | < 1 second | ✅ | |
| PERF-10 | Open medium project (50 components) | < 3 seconds | ✅ | |
| PERF-11 | Open large project (100+ components) | < 5 seconds | ✅ | |
| PERF-12 | Save project | < 2 seconds | ✅ | |
| PERF-13 | Project browser load | < 1 second | ✅ | |

### 12.3 Memory Usage 🔵

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PERF-14 | Initial memory usage | < 200MB | ✅ | |
| PERF-15 | With 100 components | < 400MB | ✅ | |
| PERF-16 | Memory leaks after 1 hour use | No significant increase | ✅ | |
| PERF-17 | Close project | Memory freed | ✅ | |

---

## 13. Compatibility & Platform

### 13.1 Operating Systems 🟡

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| PLAT-01 | Windows 10/11 | Runs without issues | ✅ | |
| PLAT-02 | Linux (Ubuntu/Arch/Debian) | Runs without issues | ✅ | |
| PLAT-03 | macOS (if tested) | Runs without issues | ✅ | |
| PLAT-04 | Platform-specific shortcuts | Work correctly on each platform | ✅ | |
| PLAT-05 | File paths | Handle platform differences (/ vs \) | ✅ | |

### 13.2 Dependencies 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| DEP-01 | Python 3.8+ installed | Application runs | ✅ | |
| DEP-02 | PyQt6 installed | UI displays correctly | ✅ | |
| DEP-03 | PySpice installed | Simulations work | ✅ | |
| DEP-04 | ngspice installed | Simulations work | ✅ | |
| DEP-05 | Missing ngspice | Clear error message | ✅ | |
| DEP-06 | NumPy installed | Simulations work | ✅ | |

---

## 14. Regression Tests (After Changes)

### 14.1 Critical Paths 🔴

| ID | Test Case | Expected Result | Status | Notes |
|----|-----------|-----------------|--------|-------|
| REG-01 | Create circuit → Save → Close → Open | Circuit restored exactly | ✅ | |
| REG-02 | Add 5 components → Connect all → Simulate | Works end-to-end | ✅ | |
| REG-03 | Create circuit → Undo all → Redo all | Returns to final state | ✅ | |
| REG-04 | Copy circuit → New project → Paste | Circuit duplicated in new project | ✅ | |
| REG-05 | Rotate all components → Simulate | Simulation still works | ✅ | |

---

## Test Summary

### Test Statistics

- **Total Test Cases**: _____ (fill after counting)
- **Tests Passed**: _____ (✅)
- **Tests Failed**: _____ (❌)
- **Tests Partial**: _____ (⚠️)
- **Tests Not Run**: _____ ([ ])

**Pass Rate**: _____%

### Critical Issues Found

| ID | Issue Description | Severity | Status |
|----|------------------|----------|--------|
| | | | |
| | | | |

### Non-Critical Issues Found

| ID | Issue Description | Severity | Status |
|----|------------------|----------|--------|
| | | | |

### Recommendations

1.
2.
3.

### Tester Sign-Off

**Tester Name**: ___________
**Date**: ___________
**Signature**: ___________

**Status**: [ ] Ready for Production  [ ] Needs Fixes  [ ] Needs Retest

---

## Notes

Use this section for any additional observations, suggestions, or feedback about the application.

