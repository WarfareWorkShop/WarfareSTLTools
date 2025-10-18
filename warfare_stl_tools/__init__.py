"""Warfare STL Tools - Blender add-on.

This module contains the Blender registration hooks and ties together the
operators implemented for scaling, base generation and STL exporting.  It is
imported by Blender when the add-on is enabled; unit tests only depend on the
support modules located next to this file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from . import exporter, scaling

bl_info = {
    "name": "Warfare STL Tools",
    "author": "Warfare Workshop",
    "version": (1, 5, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Warfare Tools",
    "description": "Scale, base and export wargaming miniatures to STL",
    "category": "Object",
}

try:  # pragma: no cover - Blender is unavailable in the unit-test environment.
    import bpy
except ModuleNotFoundError:  # pragma: no cover - allows importing the package in tests.
    bpy = None  # type: ignore[assignment]

if bpy is None:  # pragma: no cover - exercised only when Blender is unavailable.

    def register() -> None:
        raise RuntimeError("Blender's bpy module is required to register Warfare STL Tools.")


    def unregister() -> None:
        raise RuntimeError("Blender's bpy module is required to unregister Warfare STL Tools.")

else:
    from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        PointerProperty,
        StringProperty,
    )
    from bpy.types import Context, Operator, Panel, PropertyGroup
    from mathutils import Vector

    # -------------------------------------------------------------------------
    # Helper utilities
    # -------------------------------------------------------------------------

    def _preset_items(_self, _context):
        return [
            (str(preset.ratio), preset.name, f"Scale preset {preset.name}")
            for preset in scaling.SCALE_PRESETS
        ]


    def _update_source_ratio(self, _context):
        self.source_ratio = float(self.source_ratio_preset)


    def _update_target_ratio(self, _context):
        self.target_ratio = float(self.target_ratio_preset)


    def _selected_objects(context: Context) -> Iterable[bpy.types.Object]:
        return context.selected_editable_objects or []


    def _active_object(context: Context):
        obj = context.view_layer.objects.active
        if obj is None:
            raise RuntimeError("No active object selected")
        return obj

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    class WarfareToolsSettings(PropertyGroup):
        scale_mode: EnumProperty(
            name="Scale Mode",
            items=(
                ("HEIGHT", "Target Height", "Scale to a fixed miniature height"),
                ("RATIO", "Scale Preset", "Scale between real-world ratios"),
            ),
            default="HEIGHT",
        )

        target_height: FloatProperty(
            name="Target Height",
            description="Desired miniature height in meters",
            unit="LENGTH",
            default=0.032,
            min=0.0001,
        )

        source_ratio: FloatProperty(
            name="Current Scale",
            description="Current scale denominator (e.g. 56 for 1:56)",
            default=56.0,
            min=0.0001,
        )

        target_ratio: FloatProperty(
            name="Target Scale",
            description="Target scale denominator (e.g. 100 for 1:100)",
            default=100.0,
            min=0.0001,
        )

        source_ratio_preset: EnumProperty(
            name="Current",
            items=_preset_items,
            default=str(scaling.SCALE_PRESETS[5].ratio),
            update=_update_source_ratio,
        )

        target_ratio_preset: EnumProperty(
            name="Target",
            items=_preset_items,
            default=str(scaling.SCALE_PRESETS[3].ratio),
            update=_update_target_ratio,
        )

        base_type: EnumProperty(
            name="Base Type",
            items=(
                ("CIRCLE", "Round", "Create a circular base"),
                ("RECTANGLE", "Rectangular", "Create a rectangular base"),
            ),
            default="CIRCLE",
        )

        base_diameter: FloatProperty(
            name="Diameter",
            unit="LENGTH",
            default=0.025,
            min=0.001,
        )

        base_width: FloatProperty(
            name="Width",
            unit="LENGTH",
            default=0.025,
            min=0.001,
        )

        base_depth: FloatProperty(
            name="Depth",
            unit="LENGTH",
            default=0.025,
            min=0.001,
        )

        base_height: FloatProperty(
            name="Height",
            unit="LENGTH",
            default=0.0025,
            min=0.0005,
        )

        base_bevel: FloatProperty(
            name="Bevel",
            unit="LENGTH",
            default=0.0005,
            min=0.0,
        )

        merge_base: BoolProperty(
            name="Merge with model",
            description="Join the generated base with the active object",
            default=False,
        )

        export_path: StringProperty(
            name="Export Path",
            description="Destination path for STL export",
            subtype="FILE_PATH",
        )

    # -------------------------------------------------------------------------
    # Operators
    # -------------------------------------------------------------------------

    class WARFARE_OT_scale_selection(Operator):
        bl_idname = "warfare.scale_selection"
        bl_label = "Scale Selection"
        bl_description = "Scale selected objects using the configured mode"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: Context):
            try:
                active = _active_object(context)
            except RuntimeError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

            settings = context.scene.warfare_tools
            if settings.scale_mode == "HEIGHT":
                current_height = active.dimensions.z
                factor = scaling.scale_factor_for_height(current_height, settings.target_height)
            else:
                factor = scaling.scale_factor_from_ratio(settings.source_ratio, settings.target_ratio)

            objects = list(_selected_objects(context)) or [active]
            for obj in objects:
                obj.scale = scaling.apply_scale(obj.scale, factor)
            return {"FINISHED"}

    class WARFARE_OT_center_to_ground(Operator):
        bl_idname = "warfare.center_to_ground"
        bl_label = "Center & Align"
        bl_description = "Center objects on XY and align the lowest point to Z=0"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: Context):
            objects = list(_selected_objects(context))
            if not objects:
                self.report({"ERROR"}, "Select at least one object")
                return {"CANCELLED"}

            for obj in objects:
                bbox_world = [_to_world(obj, corner) for corner in obj.bound_box]
                center_x = sum(v.x for v in bbox_world) / 8.0
                center_y = sum(v.y for v in bbox_world) / 8.0
                lowest_z = min(v.z for v in bbox_world)
                obj.location.x -= center_x
                obj.location.y -= center_y
                obj.location.z -= lowest_z
            return {"FINISHED"}

    class WARFARE_OT_add_base(Operator):
        bl_idname = "warfare.add_base"
        bl_label = "Add Base"
        bl_description = "Create a miniature base using the configured settings"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context: Context):
            try:
                active = _active_object(context)
            except RuntimeError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

            settings = context.scene.warfare_tools
            base_obj = _create_base_object(context, settings, active)
            if settings.merge_base and base_obj is not None:
                _join_objects(context, active, base_obj)
            return {"FINISHED"}

    class WARFARE_OT_export_stl(Operator):
        bl_idname = "warfare.export_stl"
        bl_label = "Export STL"
        bl_description = "Export the active object to STL using native Python"

        def execute(self, context: Context):
            try:
                active = _active_object(context)
            except RuntimeError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

            settings = context.scene.warfare_tools
            filepath = settings.export_path
            if not filepath:
                self.report({"ERROR"}, "Please set an export path")
                return {"CANCELLED"}

            try:
                exporter.export_object_to_stl(active, filepath)
            except RuntimeError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

            self.report({"INFO"}, f"Exported STL to {Path(filepath).as_posix()}")
            return {"FINISHED"}

    # -------------------------------------------------------------------------
    # Panel
    # -------------------------------------------------------------------------

    class VIEW3D_PT_warfare_tools(Panel):
        bl_label = "Warfare Tools"
        bl_idname = "VIEW3D_PT_warfare_tools"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Warfare Tools"

        @staticmethod
        def _draw_scaling(layout, settings: WarfareToolsSettings, context: Context):
            box = layout.box()
            box.label(text="Scaling")
            box.prop(settings, "scale_mode", expand=True)
            active = context.view_layer.objects.active
            if active:
                box.label(text=f"Current height: {active.dimensions.z:.3f} m")
            if settings.scale_mode == "HEIGHT":
                box.prop(settings, "target_height")
            else:
                row = box.row(align=True)
                row.prop(settings, "source_ratio_preset", text="From")
                row.prop(settings, "target_ratio_preset", text="To")
                box.prop(settings, "source_ratio")
                box.prop(settings, "target_ratio")
            box.operator(WARFARE_OT_scale_selection.bl_idname, icon="FULLSCREEN_ENTER")
            box.operator(WARFARE_OT_center_to_ground.bl_idname, icon="ORIENTATION_LOCAL")

        @staticmethod
        def _draw_base(layout, settings: WarfareToolsSettings):
            box = layout.box()
            box.label(text="Base")
            box.prop(settings, "base_type", expand=True)
            if settings.base_type == "CIRCLE":
                box.prop(settings, "base_diameter")
            else:
                box.prop(settings, "base_width")
                box.prop(settings, "base_depth")
            box.prop(settings, "base_height")
            box.prop(settings, "base_bevel")
            box.prop(settings, "merge_base")
            box.operator(WARFARE_OT_add_base.bl_idname, icon="MESH_CYLINDER")

        @staticmethod
        def _draw_export(layout, settings: WarfareToolsSettings):
            box = layout.box()
            box.label(text="STL Export")
            box.prop(settings, "export_path")
            box.operator(WARFARE_OT_export_stl.bl_idname, icon="EXPORT")

        def draw(self, context: Context):
            layout = self.layout
            settings = context.scene.warfare_tools
            self._draw_scaling(layout, settings, context)
            self._draw_base(layout, settings)
            self._draw_export(layout, settings)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _to_world(obj: bpy.types.Object, coord: Tuple[float, float, float]) -> Vector:
        return obj.matrix_world @ Vector(coord)

    def _top_edges(bm, target_z: float, tolerance: float = 1e-4):
        for edge in bm.edges:
            if all(abs(v.co.z - target_z) <= tolerance for v in edge.verts):
                yield edge

    def _create_base_object(context: Context, settings: WarfareToolsSettings, anchor: bpy.types.Object):
        import bmesh

        mesh = bpy.data.meshes.new("WarfareBase")
        bm = bmesh.new()
        height = settings.base_height

        if settings.base_type == "CIRCLE":
            bmesh.ops.create_cone(
                bm,
                segments=48,
                radius1=settings.base_diameter / 2.0,
                radius2=settings.base_diameter / 2.0,
                depth=height,
            )
        else:
            result = bmesh.ops.create_cube(bm, size=1.0)
            verts = result["verts"]
            bmesh.ops.scale(
                bm,
                vec=(settings.base_width / 2.0, settings.base_depth / 2.0, height / 2.0),
                verts=verts,
            )

        bmesh.ops.translate(bm, vec=(0.0, 0.0, height / 2.0), verts=bm.verts)

        if settings.base_bevel > 0:
            top_edges = list(_top_edges(bm, height))
            if top_edges:
                bmesh.ops.bevel(
                    bm,
                    geom=top_edges,
                    offset=min(settings.base_bevel, height / 2.0),
                    segments=2,
                    profile=0.7,
                )

        bm.to_mesh(mesh)
        bm.free()

        base_obj = bpy.data.objects.new("WarfareBase", mesh)
        base_obj.location = anchor.location.copy()
        base_obj.location.z = height / 2.0
        context.collection.objects.link(base_obj)

        base_obj.select_set(True)
        context.view_layer.objects.active = base_obj
        return base_obj

    def _join_objects(context: Context, primary: bpy.types.Object, secondary: bpy.types.Object):
        for obj in context.selected_objects:
            obj.select_set(False)
        primary.select_set(True)
        secondary.select_set(True)
        context.view_layer.objects.active = primary
        bpy.ops.object.join()

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    CLASSES = (
        WarfareToolsSettings,
        WARFARE_OT_scale_selection,
        WARFARE_OT_center_to_ground,
        WARFARE_OT_add_base,
        WARFARE_OT_export_stl,
        VIEW3D_PT_warfare_tools,
    )

    def register() -> None:  # pragma: no cover - requires Blender
        for cls in CLASSES:
            bpy.utils.register_class(cls)
        bpy.types.Scene.warfare_tools = PointerProperty(type=WarfareToolsSettings)

    def unregister() -> None:  # pragma: no cover - requires Blender
        for cls in reversed(CLASSES):
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.warfare_tools

    if __name__ == "__main__":  # pragma: no cover - Blender entry point
        register()
