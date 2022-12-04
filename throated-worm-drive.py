import FreeCAD as App
import Part
import PartDesign
import math

# Gui.activeView().setActiveObject('pdbody', bodyObj)
# Gui.Selection.clearSelection()
# Gui.Selection.addSelection(bodyObj)
# Gui.ActiveDocument.ActiveView.setAxisCross(True)

def makeWorkGear( \
    bodyObj, \
    sweepAngleStep = 7.5, \
    module = 1.25, \
    teethCount = 36, \
    threads = 1, \
    gearOD = 25, \
    gearID = 10, \
    gearHeight = 40, \
    pressureAngleDeg = 20, \
    clearance = 0.0 \
) :

    import InvoluteGearFeature as gf

    numSteps = math.floor(360/sweepAngleStep)

    wirePrefix = f"{bodyObj.Name}w"
    barName  = f"{bodyObj.Name}_barStock"
    trimCylPrefix = f"{bodyObj.Name}tc"
    subtractorPrefix = f"{bodyObj.Name}fs"
    trimmedSubPrefix = f"{bodyObj.Name}Ts"
    trimmerToolName = f"{bodyObj.Name}_tool"
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
        if clearance > 0 :
            owheel = App.ActiveDocument.addObject("Part::Offset2D",f"{wirePrefix}{i}")
            bodyObj.Group = bodyObj.Group + [owheel]
            owheel.Value = - clearSelection / 2.0
            owheel.Source = wwheel
            wwheel = owheel
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

if App.ActiveDocument is None:
    doc = App.newDocument("NoName")
    App.ActiveDocument = doc

module = 1.25
teethCount = 36
threadCount = 4

gearBody = App.activeDocument().addObject('PartDesign::Body', 'Gear')
wormGear = makeWorkGear(gearBody, 1.5, module, teethCount, threadCount)
App.ActiveDocument.recompute()

import Mesh
toExport = [wormGear]
Mesh.export(toExport, f"c:/del.me/freecad/wormGear-m{module}t{teethCount}th{threadCount}.stl")
