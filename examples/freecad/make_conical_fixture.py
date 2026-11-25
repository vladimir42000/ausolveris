"""Create an editable FreeCAD horn, its printable wall and its closed air volume.

Run with a Python interpreter able to import FreeCAD, Part and MeshPart.
The output directory must be new so an existing design cannot be overwritten.
"""
import argparse
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part  # registers the parametric Part objects


def make_fixture(directory):
    directory.mkdir(parents=True, exist_ok=False)
    doc = App.newDocument("HornFixture")
    try:
        dimensions = doc.addObject("Spreadsheet::Sheet", "Dimensions")
        for row, (name, value) in enumerate([("ThroatRadius", "10 mm"),
                                             ("MouthRadius", "30 mm"),
                                             ("HornLength", "80 mm"),
                                             ("WallThickness", "3 mm"),
                                             ("FlangeThickness", "3 mm"),
                                             ("FlangeOverhang", "12 mm"),
                                             ("BoltInset", "6 mm"),
                                             ("BoltDiameter", "3.4 mm")], 1):
            dimensions.set(f"A{row}", name)
            dimensions.set(f"B{row}", value)
            dimensions.setAlias(f"B{row}", name)
        air = doc.addObject("Part::Cone", "AirVolume")
        outer = doc.addObject("Part::Cone", "OuterEnvelope")
        for obj in (air, outer):
            extra = " + Dimensions.WallThickness" if obj == outer else ""
            obj.setExpression("Radius1", "Dimensions.ThroatRadius" + extra)
            obj.setExpression("Radius2", "Dimensions.MouthRadius" + extra)
            obj.setExpression("Height", "Dimensions.HornLength")
        flange = doc.addObject("Part::Cylinder", "MouthFlange")
        flange.setExpression("Radius", "Dimensions.MouthRadius + Dimensions.WallThickness + Dimensions.FlangeOverhang")
        flange.setExpression("Height", "Dimensions.FlangeThickness")
        flange.setExpression("Placement.Base.z", "Dimensions.HornLength - Dimensions.FlangeThickness")
        shell = doc.addObject("Part::Fuse", "FlangedEnvelope")
        shell.Base, shell.Tool = outer, flange
        tools = [air]
        for i, (axis, sign) in enumerate([("x", 1), ("y", 1), ("x", -1), ("y", -1)]):
            bolt = doc.addObject("Part::Cylinder", f"ClearanceHole{i+1}")
            bolt.setExpression("Radius", "Dimensions.BoltDiameter / 2")
            bolt.setExpression("Height", "Dimensions.FlangeThickness")
            bolt.setExpression("Placement.Base.z", "Dimensions.HornLength - Dimensions.FlangeThickness")
            bolt.setExpression(f"Placement.Base.{axis}",
                               f"{sign} * (MouthFlange.Radius - Dimensions.BoltInset)")
            tools.append(bolt)
        cuts = doc.addObject("Part::Compound", "AirAndBoltHoles")
        cuts.Links = tools
        wall = doc.addObject("Part::Cut", "PrintableWall")
        wall.Base, wall.Tool = shell, cuts
        wall.Refine = True
        doc.recompute()
        for obj, filename in ((air, "air-volume.stl"), (wall, "printable-wall.stl")):
            if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids) != 1:
                raise ValueError(f"Invalid FreeCAD solid: {obj.Name}")
            mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=.04,
                                          AngularDeflection=.15, Relative=False)
            if not mesh.isSolid():
                raise ValueError(f"Open STL for {obj.Name}")
            mesh.write(str(directory / filename))
        for obj in [*tools, outer, shell, cuts, flange]:
            obj.Visibility = False
        wall.Visibility = True
        doc.saveAs(str(directory / "horn.FCStd"))
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    make_fixture(parser.parse_args().output_directory.resolve())
