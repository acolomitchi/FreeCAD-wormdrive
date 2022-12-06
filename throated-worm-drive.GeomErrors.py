# (c) 2022 Adrian Colomitchi <acolomitchi@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License (LGPL)
#   as published by the Free Software Foundation; either version 2 of
#   the License, or (at your option) any later version.
#   for detail see the LICENCE text file.
#
#   FCGear is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Library General Public License for more details.
#
#   You should have received a copy of the GNU Library General Public
#   License along with FCGear; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307

import FreeCAD as App
import Part, PartDesign
import Mesh, MeshPart

import math

# Gui.activeView().setActiveObject('pdbody', bodyObj)
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(bodyObj)
# Gui.ActiveDocument.ActiveView.setAxisCross(True)

def makeThroatedWormGear( \
    bodyObj, \
    sweepAngleStep = 7.5, \
    module = 1.25, \
    teethCount = 36, \
    threads = 1, \
    gearOD = 25, \
    gearID = 10, \
    gearHeight = 40, \
    pressureAngleDeg = 20, \
    clearance = 0.0, \
    wormGearName = '' \
) :

    import InvoluteGearFeature as gf

    numSteps = math.floor(360/sweepAngleStep)

    wirePrefix = f"{bodyObj.Name}w"
    barName  = f"{bodyObj.Name}_barStock"
    trimCylPrefix = f"{bodyObj.Name}tc"
    subtractorPrefix = f"{bodyObj.Name}fs"
    trimmedSubPrefix = f"{bodyObj.Name}Ts"
    trimmerToolName = f"{bodyObj.Name}_tool"
    if (wormGearName is None) or (len(f"{wormGearName}") == 0) :
        wormGearName = f"{bodyObj.Name}_WormGear"
    if clearance > 0 :
        origWirePrefix = f"{bodyObj.Name}rw"
    

    i = 0
        
    rotAngle = 360 / teethCount * threads
    rotAngleStep = rotAngle / numSteps

    wOD = (teethCount + 2)*module
    wID = (teethCount - 2.5)*module

    radius = (wOD + gearID) / 2.0

    gearBar = App.ActiveDocument.addObject("Part::Cylinder", barName)
    bodyObj.Group = bodyObj.Group + [gearBar]
    gearBar.Radius = gearOD / 2.0
    gearBar.Height = gearHeight
    plMatrix = App.Matrix()
    plMatrix.move(App.Vector(0, 0, -gearHeight/2.0))
    plMatrix.rotateX(math.pi /2)
    gearBar.Placement.Matrix = plMatrix

    wires = [];

    sweepAngle = 0
    for i in range(0, numSteps+1)  :
        wheelNam = f"{origWirePrefix}{i}" if clearance > 0 else f"{wirePrefix}{i}"
        wwheel = gf.makeInvoluteGear(wheelNam)
        bodyObj.Group = bodyObj.Group + [wwheel]
        wwheel.NumberOfTeeth = teethCount
        wwheel.Modules.Value = module
        wwheel.PressureAngle.Value = pressureAngleDeg
        if wwheel.ViewObject is not None :
            wwheel.ViewObject.Visibility = False
        if clearance > 0 :
            owheel = App.ActiveDocument.addObject("Part::Offset2D",f"{wirePrefix}{i}")
            bodyObj.Group = bodyObj.Group + [owheel]
            owheel.Value = - clearance / 2.0
            owheel.Source = wwheel
            wwheel = owheel
            if wwheel.ViewObject is not None :
                wwheel.ViewObject.Visibility = False
        plMatrix = App.Matrix()
        if i == 0 :
            plMatrix.move(radius, 0, 0)
        else :
            sweepAngle += sweepAngleStep
            plMatrix.rotateZ(i*rotAngleStep*math.pi/180)
            plMatrix.move(radius, 0, 0)
            plMatrix.rotateY(sweepAngle*math.pi/180)
        wwheel.Placement.Matrix = plMatrix
        wires.append(wwheel)

    wireCount = len(wires)
    wiresPerSub = 12
    numSubtractors = wireCount // wiresPerSub
    wiresPerSub = wireCount // numSubtractors
    if wireCount % numSubtractors > 0 :
        wiresPerSub = wiresPerSub + 1

    # print(f"Num subtractors: {numSubtractors}")
    # print(f"wires per sub: {wiresPerSub}")
    # print(f"Wire count: {wireCount}")

    subWireRanges = []
    subtractors = []
    rangeStart = 0
    for i in range(numSubtractors) :
        rangeMax = min(rangeStart + wiresPerSub + 1, wireCount)
        subWireRanges.append(rangeMax)
        rangeStart = rangeMax

    rangeStart = 0
    for i in range(len(subWireRanges)) :
        fullSubtractorWires = wires[rangeStart:subWireRanges[i]]
        if len(fullSubtractorWires) < 2 :
            break;
        subtractorFull = App.ActiveDocument.addObject("Part::Loft", f"{subtractorPrefix}{i}")
        bodyObj.Group = bodyObj.Group + [subtractorFull]
        subtractorFull.Ruled = False
        subtractorFull.Closed = False
        subtractorFull.Solid = True
        subtractorFull.Sections = fullSubtractorWires
        rangeStart = subWireRanges[i] - 1  #connect with the prev subtractor

        trimCyl = App.ActiveDocument.addObject("Part::Cylinder", f"{trimCylPrefix}{i}")
        bodyObj.Group = bodyObj.Group + [trimCyl]
        trimCyl.Radius = gearBar.Radius # because anything outside it won't contribute to carving
        trimCyl.Height = wOD
        plMatrix = App.Matrix()
        plMatrix.move(App.Vector(0, 0, -trimCyl.Height/2.0))
        plMatrix.rotateX(math.pi /2)
        trimCyl.Placement.Matrix = plMatrix
        
        subtractor = App.activeDocument().addObject("Part::MultiCommon", f"{trimmedSubPrefix}{i}")
        bodyObj.Group = bodyObj.Group + [subtractor]
        subtractor.Shapes = [subtractorFull, trimCyl]
        subtractors.append(subtractor)

    trimmer = App.ActiveDocument.addObject("Part::MultiFuse", trimmerToolName)
    bodyObj.Group = bodyObj.Group + [trimmer]
    trimmer.Shapes = subtractors

    wormGear = App.ActiveDocument.addObject("Part::Cut", wormGearName)
    bodyObj.Group = bodyObj.Group + [wormGear]
    wormGear.Base = gearBar
    wormGear.Tool = trimmer
    return wormGear

def toMeshAndBack(obj, bodyObj, linearDeflection = 0.05) :
    App.ActiveDocument.recompute() # otherwise the mesh will turn out empty
    mesh = App.ActiveDocument.addObject("Mesh::Feature", f"{obj.Name}_meshed");
    bodyObj.Group = bodyObj.Group + [mesh]
    mesh.Mesh = MeshPart.meshFromShape(Shape = obj.Shape, LinearDeflection = linearDeflection, AngularDeflection = 0.698131, Relative = False)
    
    asPart = App.ActiveDocument.addObject("Part::Feature", f"{obj.Name}_meshedPart")
    bodyObj.Group = bodyObj.Group + [asPart]
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Mesh.Topology, 0.01, True)
    asPart.Shape = shape
    App.ActiveDocument.removeObject(mesh.Name)
    del mesh
    
    asSolid = App.ActiveDocument.addObject("Part::Feature", f"{obj.Name}_meshedPartSolid")
    bodyObj.Group = bodyObj.Group + [asSolid]
    asSolid.Shape = Part.Solid(asPart.Shape)
    
    # do not refine it, it takes ages!!!
    #ret = App.ActiveDocument.addObject("Part::Refine", f"{obj.Name}_meshedSolidRefined");
    #bodyObj.Group = bodyObj.Group + [ret]
    #ret.Source = asSolid
    
    App.ActiveDocument.removeObject(obj.Name)
    del obj
    return asSolid


def makeThroatedWormWheel(
    bodyObj, \
    sweepAngleStep = 7.5, wheelThickness = 10, \
    module = 1.25, \
    teethCount = 36, \
    threads = 1, \
    gearOD = 25, \
    gearID = 10, \
    gearHeight = 40, \
    pressureAngleDeg = 20, \
    clearance = -1 \
) :
    wOD = (teethCount + 2)*module
    wID = (teethCount - 2.5)*module
    optimalGearHeight = gearHeight #math.sqrt(wOD*wOD - wID*wID)
    hobbingRadius = (wOD+gearID) / 2.0
    
    hobPart = wheelBody = App.activeDocument().addObject('PartDesign::Body', 'Hobs')
    hobName = f"{bodyObj.Name}_hobGear"
    if clearance < 0 :
        clearance = 0.150
    hob = makeThroatedWormGear( \
        hobPart, sweepAngleStep, \
        module, teethCount, threads, \
        gearOD, gearID, optimalGearHeight, pressureAngleDeg, \
        clearance, hobName \
    )
    if hob.ViewObject is not None :
        hob.ViewObject.Visibility = False
        
    wheelPlate = App.ActiveDocument.addObject("Part::Cylinder", f"{bodyObj.Name}_wheelRound")
    bodyObj.Group = bodyObj.Group + [wheelPlate]
    wheelPlate.Radius = wOD / 2.0
    wheelPlate.Height = wheelThickness
    plMatrix = App.Matrix()
    plMatrix.move(App.Vector(hobbingRadius, 0, -wheelThickness/2.0))
    wheelPlate.Placement.Matrix = plMatrix
    
    hobStep = 2*math.pi/threads
    wheelStep = 2*math.pi/teethCount
    
    for i in range(3) : ### this should go to range(teethCount)!!! BLODDY GEOM ERRORS AT THE SECOND STEP, tho!
        hobLink = App.ActiveDocument.addObject("App::Link", f"{bodyObj.Name}_hob{i}")
        bodyObj.Group = bodyObj.Group + [hobLink]
        hobLink.setLink(hob)
        plMatrix = App.Matrix()
        plMatrix.rotateY(i*hobStep)
        hobLink.Placement.Matrix = plMatrix
                
        hobbed = App.ActiveDocument.addObject("Part::Cut", f"{bodyObj.Name}_hobt{i}")
        bodyObj.Group = bodyObj.Group + [hobbed]
        hobbed.Base = wheelPlate
        hobbed.Tool = hobLink
        # hobbed.Refine = True
        
        #and then advance the plate
        plMatrix = App.Matrix()
        plMatrix.move(App.Vector(-hobbingRadius, 0, 0))
        plMatrix.rotateZ(wheelStep)
        plMatrix.move(App.Vector(hobbingRadius, 0, 0))
        hobbed.Placement.Matrix = plMatrix

        wheelPlate = hobbed
        # and the bloody FreeCAD smashes the geometry immediately or after a couple of hobbing!!!
        # replace it with a mesh and back to solid
        # wheelPlate = toMeshAndBack(wheelPlate, bodyObj, 0.1)
    # translate it back to origin before returning
    plMatrix = App.Matrix()
    plMatrix.move(App.Vector(-hobbingRadius, 0, 0))
    wheelPlate.Placement.Matrix = plMatrix
    return wheelPlate

if App.ActiveDocument is None:
    doc = App.newDocument("NoName")
    App.ActiveDocument = doc

module = 1.25
teethCount = 36
threadCount = 1

# gearBody = App.activeDocument().addObject('PartDesign::Body', 'Gear')
# wormGear = makeThroatedWormGear(gearBody, 1.5, module, teethCount, threadCount)
wheelBody = App.activeDocument().addObject('PartDesign::Body', 'Wheel')
makeThroatedWormWheel(wheelBody, 10, 10, module, teethCount, threadCount)
App.ActiveDocument.recompute()

# toExport = [wormGear]
# Mesh.export(toExport, f"~/del.me/freecad/wormGear-m{module}t{teethCount}th{threadCount}.stl")
