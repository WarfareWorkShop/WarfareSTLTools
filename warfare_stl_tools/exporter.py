"""Utilities to export Blender meshes to STL."""
from __future__ import annotations

from typing import Iterable, Tuple

try:  # pragma: no cover - Blender is not available during unit tests.
    import bpy
except ModuleNotFoundError:  # pragma: no cover - allows importing in unit tests.
    bpy = None  # type: ignore[assignment]
Triangle = Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]


def triangles_to_ascii_stl(triangles: Iterable[Triangle], name: str = "Mesh") -> str:
    """Return an ASCII STL representation for ``triangles``.

    The function accepts an iterable of triangles, where every triangle is a
    tuple with three XYZ vertices.  Normals are computed using a simple cross
    product which is sufficient for the add-on's use case.
    """

    lines = [f"solid {name}"]
    for v1, v2, v3 in triangles:
        normal = _calculate_normal(v1, v2, v3)
        lines.append(
            "  facet normal {:.6f} {:.6f} {:.6f}".format(*normal)
        )
        lines.append("    outer loop")
        lines.append("      vertex {:.6f} {:.6f} {:.6f}".format(*v1))
        lines.append("      vertex {:.6f} {:.6f} {:.6f}".format(*v2))
        lines.append("      vertex {:.6f} {:.6f} {:.6f}".format(*v3))
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines) + "\n"


def write_ascii_stl(triangles: Iterable[Triangle], filepath: str, name: str = "Mesh") -> None:
    """Write triangles to ``filepath`` in ASCII STL format."""

    data = triangles_to_ascii_stl(triangles, name=name)
    with open(filepath, "w", encoding="utf8") as handle:
        handle.write(data)


def export_object_to_stl(obj, filepath: str, *, apply_modifiers: bool = True) -> None:  # pragma: no cover - requires Blender
    """Export ``obj`` to STL using Blender's evaluated mesh."""

    if bpy is None:
        raise RuntimeError("Blender's bpy module is required to export meshes")

    depsgraph = bpy.context.evaluated_depsgraph_get() if apply_modifiers else None
    evaluated = obj.evaluated_get(depsgraph) if depsgraph else obj
    mesh = evaluated.to_mesh()

    try:
        triangles = tuple(_mesh_to_triangles(mesh))
    finally:
        if depsgraph:
            evaluated.to_mesh_clear()
        else:
            obj.to_mesh_clear()

    write_ascii_stl(triangles, filepath, name=obj.name)


def _mesh_to_triangles(mesh) -> Iterable[Triangle]:  # pragma: no cover - requires Blender
    mesh.calc_loop_triangles()
    vertices = mesh.vertices
    for loop_triangle in mesh.loop_triangles:
        yield (
            tuple(vertices[loop_triangle.vertices[0]].co),
            tuple(vertices[loop_triangle.vertices[1]].co),
            tuple(vertices[loop_triangle.vertices[2]].co),
        )


def _calculate_normal(v1, v2, v3) -> Tuple[float, float, float]:
    """Return a normal vector for triangle ``(v1, v2, v3)``."""

    ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
    bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    length = (nx ** 2 + ny ** 2 + nz ** 2) ** 0.5
    if length == 0:
        return 0.0, 0.0, 0.0
    return nx / length, ny / length, nz / length
