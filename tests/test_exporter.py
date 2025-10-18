from warfare_stl_tools import exporter


def test_triangles_to_ascii_stl_generates_facets(tmp_path):
    triangles = (
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0)),
    )
    data = exporter.triangles_to_ascii_stl(triangles, name="Test")
    assert data.startswith("solid Test\n")
    assert data.endswith("endsolid Test\n")
    assert "facet normal" in data

    outfile = tmp_path / "mesh.stl"
    exporter.write_ascii_stl(triangles, outfile.as_posix(), name="Test")
    assert outfile.read_text().count("facet normal") == 2
