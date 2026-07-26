import bpy
from mathutils import Vector

#little helper to check if a string is indexed
def is_int(value):
	try:
		int(value)
		return True
	except ValueError:
		return False
	
def normalize_skeleton(context):
	obj = context.active_object

	old_mode = obj.mode
	obj.data.display_type = 'STICK'
	obj.data.show_bone_custom_shapes = False

	bpy.ops.object.mode_set(mode='EDIT')

	for bone in obj.data.edit_bones:
		bone.tail = bone.head + Vector((0.0, 0.0, 0.25))
		bone.roll = 0.0

	bpy.ops.object.mode_set(mode=old_mode)

def map_value(value, old_min, old_max, new_min, new_max):
	return (value - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
def map_signed_byte(value):
	return map_value(value, -128, 127, -1, 1)



def delete_curves(self,type):
	bpy.ops.ed.undo_push()
	bpy.ops.ed.undo_push()
	action = bpy.context.object.animation_data.action
	if not action:
		self.report({'ERROR'}, "No active action found.")
		return {'CANCELLED'}

	selected_bones = bpy.context.selected_pose_bones
	if not selected_bones:
		self.report({'ERROR'}, "No bones selected.")
		return {'CANCELLED'}



	typ = ""
	res = str(type)
	if type >= 0 and type < 4:
			typ = 'location'
	if type > 3 and type < 8:
			typ = 'rotation_euler'
	if type > 7:
			typ = 'scale'   
			
			
			
			
	if type == 0 or type == 4 or type == 8:
		res = ''     
	if type == 1 or type == 5 or type == 9:
			res = '0'  
	if type == 2 or type == 6 or type == 10:
			res = '1' 
	if type == 3 or type == 7 or type == 11:
			res = '2'
			
			
			

	print(typ + "     " + res + "     " + str(type))
	for fcurve in action.fcurves: 
		if fcurve.data_path.endswith(typ) and res in str(fcurve.array_index):
			bone_name = fcurve.data_path.split('"')[1]
			if bone_name in [bone.name for bone in selected_bones]:
				action.fcurves.remove(fcurve)