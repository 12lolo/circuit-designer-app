# Bend Point Undo/Redo Fix

## Issue

Undo/redo functionality was not working correctly for wires with bend points. When a wire with bend points was deleted and then restored via undo, the bend points and wire segments would not be properly restored, resulting in broken wires.

## Root Cause

Wires in the circuit designer consist of three types of objects:
1. **Main Wire** - The primary `Wire` object
2. **Bend Points** - `BendPoint` objects that define intermediate routing points
3. **Wire Segments** - `QGraphicsLineItem` objects connecting the points

When a wire has bend points:
- Bend points are separate scene items that need to be added/removed
- Wire segments are dynamically created to connect start → bend points → end
- The main wire becomes transparent (segments handle the visual display)

The undo commands (`AddWireCommand`, `DeleteWireCommand`, `MultiDeleteCommand`) were only handling the main Wire object, not the bend points or segments.

## Problem Details

### Before Fix

**AddWireCommand.undo():**
- ❌ Only removed the main wire
- ❌ Did not remove bend points (left orphaned in scene)
- ❌ Did not remove wire segments (left orphaned in scene)

**DeleteWireCommand.undo():**
- ❌ Only restored the main wire
- ❌ Did not restore bend points
- ❌ Did not recreate wire segments
- Result: Wire appeared broken after undo

**MultiDeleteCommand.undo():**
- ❌ Only restored wires to scene
- ❌ Did not restore bend points or segments
- Result: Multiple broken wires after undo

## Solution

### Updated AddWireCommand

**redo()** - When adding a wire back:
```python
# Restore bend points if they exist
if hasattr(self.wire, 'bend_points'):
    for bend_point in self.wire.bend_points:
        if bend_point.scene() != self.scene:
            self.scene.addItem(bend_point)

# Recreate wire segments
if hasattr(self.wire, 'update_wire_path'):
    self.wire.update_wire_path()
```

**undo()** - When removing a wire:
```python
# Remove bend points
if hasattr(self.wire, 'bend_points'):
    for bend_point in self.wire.bend_points:
        if bend_point.scene() == self.scene:
            self.scene.removeItem(bend_point)

# Remove wire segments
if hasattr(self.wire, 'wire_segments'):
    for segment in self.wire.wire_segments:
        if segment.scene() == self.scene:
            self.scene.removeItem(segment)

# Remove main wire
if self.wire.scene() == self.scene:
    self.scene.removeItem(self.wire)
```

### Updated DeleteWireCommand

**redo()** - When deleting a wire:
```python
# Remove bend points
if hasattr(self.wire, 'bend_points'):
    for bend_point in self.wire.bend_points:
        if bend_point.scene() == self.scene:
            self.scene.removeItem(bend_point)

# Remove wire segments
if hasattr(self.wire, 'wire_segments'):
    for segment in self.wire.wire_segments:
        if segment.scene() == self.scene:
            self.scene.removeItem(segment)

# Remove main wire
if self.wire.scene() == self.scene:
    self.scene.removeItem(self.wire)
```

**undo()** - When restoring a deleted wire:
```python
self.scene.addItem(self.wire)

# Restore bend points
if hasattr(self.wire, 'bend_points'):
    for bend_point in self.wire.bend_points:
        if bend_point.scene() != self.scene:
            self.scene.addItem(bend_point)

# Recreate wire segments
if hasattr(self.wire, 'update_wire_path'):
    self.wire.update_wire_path()
```

### Updated MultiDeleteCommand

**undo()** - When restoring multiple items:
```python
for wire in wires:
    self.scene.addItem(wire)

    # If wire is a Wire instance, restore bend points and segments
    if isinstance(wire, Wire):
        # Restore bend points
        if hasattr(wire, 'bend_points'):
            for bend_point in wire.bend_points:
                if bend_point.scene() != self.scene:
                    self.scene.addItem(bend_point)

        # Recreate wire segments
        if hasattr(wire, 'update_wire_path'):
            wire.update_wire_path()
```

## Key Implementation Details

### Why Not Delete Bend Points from Wire Object?

The bend points remain in the `wire.bend_points` list even when removed from the scene. This allows them to be restored during redo/undo without recreating them.

### Why Call `update_wire_path()`?

The `update_wire_path()` method:
1. Clears existing wire segments
2. Recreates segments based on current bend points
3. Sets up proper event filtering
4. Handles wire appearance (transparency, z-order)

This ensures segments are properly initialized when the wire is restored.

### Scene Membership Checks

All operations check `if item.scene() == self.scene` to avoid:
- Removing items not in the scene (causes errors)
- Adding items already in the scene (causes errors)
- Operating on items from different scenes

## Testing

### Test Cases Verified

✅ **Create wire → Add bend point → Undo**: Wire and bend point removed
✅ **Create wire → Add bend point → Undo → Redo**: Wire and bend point restored
✅ **Create wire → Add bend point → Delete wire → Undo**: Wire with bend point restored
✅ **Create multiple wires with bend points → Select all → Delete → Undo**: All wires with bend points restored

### Edge Cases Handled

- Wires without bend points (still work normally)
- Multiple bend points per wire
- Bend points already in scene (don't add twice)
- Segments already removed (don't remove twice)

## Files Modified

- ✅ `circuit_designer/project/undo_commands.py`
  - `AddWireCommand.redo()` - Added bend point and segment restoration
  - `AddWireCommand.undo()` - Added bend point and segment removal
  - `DeleteWireCommand.redo()` - Added bend point and segment removal
  - `DeleteWireCommand.undo()` - Added bend point and segment restoration
  - `MultiDeleteCommand.undo()` - Added wire bend point and segment restoration

## Impact

**Before**: Undo/redo on wires with bend points would result in broken wires that were invisible or had missing segments.

**After**: Undo/redo fully restores wires with all bend points and segments intact, maintaining proper visual appearance and functionality.

## Related Code

- `circuit_designer/components/wire.py` - Wire class with `bend_points`, `wire_segments`, and `update_wire_path()`
- `circuit_designer/components/connection_points.py` - BendPoint class definition
