import bpy
from bpy.utils import register_class
from bpy.utils import unregister_class
from . import panels
from . import icons
from . import types
from . import md
from . import mot
from . import curve_simplify


bl_info = {
	"name": "Okami MD Studio",
	"author": "Akito3D",
	"version" : (1, 0, 0),
	"blender" : (4, 3, 0),
	"location": "View3D / Okami",
	"description": "Okami MD Studio",
	"wiki_url": "",
	"category": "Models"}





def register():
	types.register()
	icons.register()
	panels.register()
	md.register()
	mot.register()
	curve_simplify.register()

	
def unregister():
	types.unregister()
	icons.unregister()
	panels.unregister()
	md.unregister()
	mot.unregister()
	curve_simplify.unregister()


if __name__ == "__main__":
	register()