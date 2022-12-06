# FreeCAD-wormdrive

FreeCAD 0.20+ scripted objects Python dealing with the design of worm drives (both gear and wheel). At high tesselation (angular resolution) make take some good minutes for `FreeCAD.ActiveDocument.recompute()` to finish generating the gear and/or wheel.

**Warning**: Work-in-progress

## Throated worm drives
 
The worm gear looks like

![throated 1thread](./images/throated-gear-1thread.png)

**The worm-wheel function fails to produce anything. after a second "hobbing" step the result is full of geom errors. With FreeCAD v0.20.1, Revision 29410, on a Windows 10 Home, Lenovo laptop AMD Ryzen 5 3500U with Radeon Vega Mobile Gfx 2.10 GHz, 16GB RAM**