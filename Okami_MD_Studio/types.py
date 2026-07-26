import bpy

from bpy.utils import register_class
from bpy.utils import unregister_class
from bpy.types import Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, CollectionProperty,EnumProperty,IntProperty
from . import __init__
from . import icons



def register():

	bpy.types.Scene.okami_bone_names = StringProperty( #used for vert group merge
		name="",
		description="",
		default=""
	)
	bpy.types.Scene.okami_armature_name = StringProperty(
		name="",
		description="",
		default=""
	)
	
	bpy.types.Scene.okami_bone_match_threshold = FloatProperty(
		name="Match Threshold",
		description="how close a bone A needs to be from bone B in order to be detected (expanding this might make bone detection innacurate).",
		default=0.1,
		min=0
	)
	
	bpy.types.Scene.okami_show_mesh_utility = BoolProperty(
		name="",
		description="",
		default=True,
	)
	bpy.types.Scene.okami_show_vertex_utility = BoolProperty(
		name="",
		description="",
		default=True,
	)
	bpy.types.Scene.okami_show_skeleton_utility = BoolProperty(
		name="",
		description="",
		default=True,
	)
	bpy.types.Scene.okami_show_animation_utility = BoolProperty(
		name="",
		description="",
		default=True,
	)
	
	bpy.types.Scene.okami_simplify_factor = FloatProperty(
		name="Simplify Factor",
		description="The factor of curve cleanup you want in the animation",
		default=0.01
	)

def unregister():
	del bpy.types.Scene.okami_bone_names
	del bpy.types.Scene.okami_armature_name
	del bpy.types.Scene.okami_bone_match_threshold
	del bpy.types.Scene.okami_show_mesh_utility
	del bpy.types.Scene.okami_show_vertex_utility
	del bpy.types.Scene.okami_show_skeleton_utility
	del bpy.types.Scene.okami_simplify_factor

