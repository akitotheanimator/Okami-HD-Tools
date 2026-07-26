#this fucker is going to handle MOT importing and exporting
import bpy
import os
import io
import math
import struct


import bmesh
import mathutils
from enum import IntEnum
from mathutils import Vector
from . import icons

from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.types import Operator
from bpy.utils import register_class
from bpy.props import (StringProperty, BoolProperty, CollectionProperty, FloatProperty )
from mathutils import Matrix
from . import utility


class keyframe_property(IntEnum):
	POSE_POSITION_X = 0
	POSE_POSITION_Y = 1
	POSE_POSITION_Z = 2
	POSE_ROTATION_X = 3
	POSE_ROTATION_Y = 4
	POSE_ROTATION_Z = 5
	POSE_SCALE_X = 6
	POSE_SCALE_Y = 7
	POSE_SCALE_Z = 8

	QUANTIZED_POSITION_X = 16
	QUANTIZED_POSITION_Y = 17
	QUANTIZED_POSITION_Z = 18
	QUANTIZED_ROTATION_X = 19
	QUANTIZED_ROTATION_Y = 20
	QUANTIZED_ROTATION_Z = 21
	QUANTIZED_SCALE_X = 22
	QUANTIZED_SCALE_Y = 23
	QUANTIZED_SCALE_Z = 24

	QUANTIZED_PRECISE_POSITION_X = 50
	QUANTIZED_PRECISE_POSITION_Y = 51
	QUANTIZED_PRECISE_POSITION_Z = 52
	QUANTIZED_PRECISE_ROTATION_X = 53
	QUANTIZED_PRECISE_ROTATION_Y = 54
	QUANTIZED_PRECISE_ROTATION_Z = 55
	QUANTIZED_PRECISE_SCALE_X = 56
	QUANTIZED_PRECISE_SCALE_Y = 57
	QUANTIZED_PRECISE_SCALE_Z = 58

	FULL_PRECISION_POSITION_X = 80
	FULL_PRECISION_POSITION_Y = 81
	FULL_PRECISION_POSITION_Z = 82
	FULL_PRECISION_ROTATION_X = 83
	FULL_PRECISION_ROTATION_Y = 84
	FULL_PRECISION_ROTATION_Z = 85
	FULL_PRECISION_SCALE_X = 86
	FULL_PRECISION_SCALE_Y = 87
	FULL_PRECISION_SCALE_Z = 88
class keyframe_property_type(IntEnum):
	POSE = 0
	QUANTIZED = 1
	QUANTIZED_PRECISE = 2
	FULL_PRECISION = 3
	UNK = 4

def get_curve_property(type):
	if type >= 0 and type <= 8:
		return keyframe_property_type.POSE
	if type >= 16 and type <= 24:
		return keyframe_property_type.QUANTIZED
	if type >= 50 and type <= 58:
		return keyframe_property_type.QUANTIZED_PRECISE
	if type >= 80 and type <= 88:
		return keyframe_property_type.FULL_PRECISION


	return keyframe_property_type.UNK
def get_transform_type(prop):
	if (prop >= keyframe_property.POSE_POSITION_X and prop <= keyframe_property.POSE_POSITION_Z) or (prop >= keyframe_property.QUANTIZED_POSITION_X and prop <= keyframe_property.QUANTIZED_POSITION_Z) or  (prop >= keyframe_property.QUANTIZED_PRECISE_POSITION_X and prop <= keyframe_property.QUANTIZED_PRECISE_POSITION_Z) or (prop >= keyframe_property.FULL_PRECISION_POSITION_X and prop <= keyframe_property.FULL_PRECISION_POSITION_Z):
		return "location"
	if (prop >= keyframe_property.POSE_ROTATION_X and prop <= keyframe_property.POSE_ROTATION_Z) or (prop >= keyframe_property.QUANTIZED_ROTATION_X and prop <= keyframe_property.QUANTIZED_ROTATION_Z) or  (prop >= keyframe_property.QUANTIZED_PRECISE_ROTATION_X and prop <= keyframe_property.QUANTIZED_PRECISE_ROTATION_Z) or (prop >= keyframe_property.FULL_PRECISION_ROTATION_X and prop <= keyframe_property.FULL_PRECISION_ROTATION_Z):
		return "rotation_euler"
	if (prop >= keyframe_property.POSE_SCALE_X and prop <= keyframe_property.POSE_SCALE_Z) or (prop >= keyframe_property.QUANTIZED_SCALE_X and prop <= keyframe_property.QUANTIZED_SCALE_Z) or  (prop >= keyframe_property.QUANTIZED_PRECISE_SCALE_X and prop <= keyframe_property.QUANTIZED_PRECISE_SCALE_Z) or (prop >= keyframe_property.FULL_PRECISION_SCALE_X and prop <= keyframe_property.FULL_PRECISION_SCALE_Z):
		return "scale"
	return "unk"
def get_transform_index(prop):
	curve_prop = get_curve_property(prop)
	subtr = 0
	match curve_prop:
		case keyframe_property_type.POSE:
			subtr = 0
		case keyframe_property_type.QUANTIZED:
			subtr = 16
		case keyframe_property_type.QUANTIZED_PRECISE:
			subtr = 50
		case keyframe_property_type.FULL_PRECISION:
			subtr = 80
	value = prop - subtr
	return value % 3
def path_to_index(data_path,index):
	v = -1
	if "location" in data_path:
		v = 0
	if "rotation_euler" in data_path:
		v = 3
	if "scale" in data_path:
		v = 6
	if v == -1:
		return v




	return v + index
def data_path_to_type(data_path, index, configuration):
	base_index = 0
	match configuration:
		case keyframe_property_type.POSE:
			base_index = 0
		case keyframe_property_type.QUANTIZED:
			base_index = 16
		case keyframe_property_type.QUANTIZED_PRECISE:
			base_index = 50
		case keyframe_property_type.FULL_PRECISION:
			base_index = 80
		case keyframe_property_type.UNK:
			return -1
	
	if "location" in data_path:
		base_index += index
	if "rotation_euler" in data_path:
		base_index += (index + 3)
	if "scale" in data_path:
		base_index += (index + 6)
	#print(data_path, "   ", index, "    ", configuration)


	return base_index

def from_ushort(half_precision: int) -> float:
	half_precision = int(half_precision)
	exponent = (half_precision >> 9) & ((1 << 6) - 1)
	significand = half_precision & ((1 << 9) - 1)
	sign = (half_precision >> 15) & 1
	biased_exponent = exponent - 47
	value = (sign * -2 + 1) * (2 ** biased_exponent) * (1 + significand / (2 ** 9))
	return value
def to_ushort(value: float) -> int:
	binary32 = struct.pack('f', value)
	int32 = struct.unpack('I', binary32)[0]

	sign = (int32 >> 31) & 0x1
	exponent = (int32 >> 23) & 0xFF
	mantissa = int32 & 0x7FFFFF

	exponent_value = exponent - 127 + 47
	if exponent_value < 0:
		exponent_value = 0
	elif exponent_value > 63:
		exponent_value = 63
	

	significand = mantissa >> 14
	if significand > 0x1FF:
		significand = 0x1FF
	
	binary16 = (sign << 15) | (exponent_value << 9) | significand
	return binary16


def get_curve_configuration(curve, movement_threshold, pose_threshold = 0.1):
	if len(curve) == 1:
		return keyframe_property_type.POSE

	values = [kp.co.y for kp in curve]
	if max(values) - min(values) <= pose_threshold:
		#print(max(values) - min(values))
		return keyframe_property_type.POSE
	

	y_values = [kp.co.y for kp in curve]
	
	
	min_p0 = min(y_values)
	max_p0 = max(y_values)


	quantized = True

	min_p0_quantized = from_ushort(to_ushort(min_p0))
	p0_quantized_step = from_ushort(to_ushort(max_p0 - min_p0)) / 255
	
	for i in curve:
		quant_val = round(utility.map_value(i.co.y, min_p0, max_p0,0,255))
		reconstructed_value = min_p0_quantized + (quant_val * p0_quantized_step)

		error_fact = abs(i.co.y - reconstructed_value)
		#print(error_fact)
		if error_fact > movement_threshold:
			quantized = False
			break
	if quantized:
		return keyframe_property_type.QUANTIZED
	
	
	
	quantized_precise = True
	p0_quantized_precise_step = (max_p0 - min_p0) / 65535
	for i in curve:
		quant_val = round(utility.map_value(i.co.y, min_p0, max_p0,0,65535))
		reconstructed_value = min_p0 + (quant_val * p0_quantized_precise_step)

		error_fact = abs(i.co.y - reconstructed_value)
		#print(error_fact)
		if error_fact > movement_threshold:
			quantized_precise = False
			break
	if quantized_precise:
		return keyframe_property_type.QUANTIZED_PRECISE
	


	return keyframe_property_type.FULL_PRECISION
def reset_armature_pose(armature):
	for bone in armature.pose.bones:
		bone.location = (0.0, 0.0, 0.0)
		bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
		bone.rotation_euler = (0.0, 0.0, 0.0)
		bone.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
		bone.scale = (1.0, 1.0, 1.0)
class ImportMOT(Operator, ImportHelper):
	"""Import Okami Animation"""
	bl_idname = "import_scene.okami_mot"
	bl_label = "Import Animations"
	bl_options = {'REGISTER', 'UNDO'}

	filename_ext = ".mot"
	filter_glob: StringProperty(default="*.mot", options={'HIDDEN'}, maxlen=255)
	files: CollectionProperty(type=bpy.types.PropertyGroup)
	def execute(self, context):
		layout = self.layout
		armature = bpy.context.view_layer.objects.active
		if not armature:
			self.report({'ERROR'}, f"No armature selected. Please select a armature before importing a animation.")
			return {'CANCELLED'}
		if armature.type != "ARMATURE":
			self.report({'ERROR'}, f"Object selected isn't a armature.")
			return {'CANCELLED'}
		bpy.context.scene.render.fps = 30 #all anims are set in 30 fps
		bpy.context.scene.frame_current = 0
		bpy.context.scene.frame_start = 0


		bpy.ops.object.mode_set(mode='POSE')

		for pose_bone in armature.pose.bones:
			pose_bone.rotation_mode = 'XYZ'

		if armature.animation_data is None:
			armature.animation_data_create()

		
		directory = self.filepath
		directory = directory.replace(os.path.basename(directory),"")
		directory = directory[:-1]
		bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
		for file_elem in self.files:
			file_path = f"{directory}/{file_elem.name}"
			import_animation(file_path, self, armature)
		return {'FINISHED'}
class ExportMOT(Operator, ExportHelper):
	"""Export Okami Animation"""
	bl_idname = "export_scene.okami_mot"
	bl_label = "Export Animation"
	bl_options = {'REGISTER', 'UNDO'}

	filename_ext = ".mot"
	filter_glob: StringProperty(default="*.mot", options={'HIDDEN'}, maxlen=255,)
	files: CollectionProperty(type=bpy.types.PropertyGroup)
	
	determine_dynamicaly: BoolProperty(name="Set property types dynaically", description="This allows the addon to decide automatically the property type of each fcurve.", default=True,)
	precision_only: BoolProperty(name = "Precision only", description = "If this setting is activated, the whole file will be exported with full precision, ideal for cutscenes.", default = False,)
	loops: BoolProperty(name = "Animation loops", description = "this will only show up if you dont have blen2mot installed. Bascially this sets if the animation is going to be looped or not", default = True,)
	
	movement_threshold: FloatProperty(name = "Movement Threshold", description = "This threshold determines what curve type to use. If the error of the quantized curve is greater than this threshold, the precision is increased in exchange of some storage space.", default = 0.02,)
	
	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None
		
	def draw(self, context):
		layout = self.layout   
			
		#layout.label(text="Allowed curve properties:")
		lt1 = layout.box()
		layout.separator()
		lt1.prop(self,"movement_threshold")
		layout.prop(self,"loops")
		   
	def execute(self, context):
		bpy.context.scene.tool_settings.use_keyframe_insert_auto = False 
		anim_loops = self.loops
		armature = bpy.context.view_layer.objects.active
		if not armature:
			self.report({'ERROR'}, f"No armature selected. Please select a armature before exporting a animation.")
			return {'CANCELLED'}
		if armature.type != "ARMATURE":
			self.report({'ERROR'}, f"Object selected isn't a armature.")
			return {'CANCELLED'}
		if armature.animation_data is None:
			self.report({'ERROR'}, f"Object selected has no animation data.")
			return {'CANCELLED'}
		if armature.animation_data.action is None:
			self.report({'ERROR'}, f"Object selected has no animation.")
			return {'CANCELLED'}


		directory = self.filepath
		directory = directory.replace(os.path.basename(directory),"")
		directory = directory[:-1]
		file_path = f"{directory}/{self.files[0].name}"
		bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
		export_animation(file_path, self, armature, anim_loops, self.movement_threshold, self.precision_only)
		bpy.context.scene.frame_current = 0
		return {'FINISHED'} 


def import_animation(file_path,self,armature):
	
	with open(file_path, "rb") as file:
		filemagic = file.read(4)
		if filemagic != b"mtb3":
			self.report({'ERROR'}, f"The imported file is not a valid animation file.")
			return {'CANCELLED'}
		animation = bpy.data.actions.new(name=str(os.path.basename(file_path)))
		armature.animation_data.action = animation
		bpy.data.actions[animation.name].use_fake_user = True
		
		
		frame_count = struct.unpack("<H", file.read(2))[0]

		bpy.context.scene.frame_end = frame_count-1

		property_count = struct.unpack("<B", file.read(1))[0] #the last property is a terminator
		animation_loop = struct.unpack("<B", file.read(1))[0] == 1
		for i in range(0, property_count-1):
			bone_index = (struct.unpack("<b", file.read(1))[0]) + 1
			bone_name = str(bone_index) if bone_index > 0 else "root"
			if bone_name in armature.pose.bones:
				pose_bone = armature.pose.bones[bone_name]
			else:
				print("Couldn't find bone " + bone_name +" at: " + str(file.tell()))
				file.read(7)
				continue


			property = struct.unpack("<B", file.read(1))[0]
			transform_type = get_transform_type(property)
			transform_index = get_transform_index(property)
			curve_property = get_curve_property(property)




			if transform_type == "unk":
				print("Unknown property " + str(property) + " at: " + str(file.tell()))
				file.read(6)
				continue
			
			if bone_name in armature.animation_data.action.groups:
				group = armature.animation_data.action.groups[bone_name]
			else:
				group = armature.animation_data.action.groups.new(name=bone_name)
					
			reset_armature_pose(armature)
			
			if transform_type == "location":
				if bone_name != "root":
					pose_bone.matrix = pose_bone.parent.matrix
			

			keyframe_count = struct.unpack("<H", file.read(2))[0]

			#print(transform_type, "   ",  property, "   ", keyframe_count)

			if curve_property == keyframe_property_type.POSE:
				value = struct.unpack("<f", file.read(4))[0]
				match property:
					case keyframe_property.POSE_POSITION_X:
						pose_bone.location.x += value
					case keyframe_property.POSE_POSITION_Y:
						pose_bone.location.y += value
					case keyframe_property.POSE_POSITION_Z:
						pose_bone.location.z += value

					case keyframe_property.POSE_ROTATION_X:
						pose_bone.rotation_euler[0] = value
					case keyframe_property.POSE_ROTATION_Y:
						pose_bone.rotation_euler[1] = value
					case keyframe_property.POSE_ROTATION_Z:
						pose_bone.rotation_euler[2] = value

					case keyframe_property.POSE_SCALE_X:
						pose_bone.scale.x = value
					case keyframe_property.POSE_SCALE_Y:
						pose_bone.scale.y = value
					case keyframe_property.POSE_SCALE_Z:
						pose_bone.scale.z = value

				pose_bone.keyframe_insert(data_path=transform_type, index=transform_index, frame=0)
				fcurve = animation.fcurves.find(f'pose.bones["{bone_name}"].{transform_type}', index=transform_index)
				if fcurve.group != group:
					fcurve.group = group

			else:
				keyframes = []
				offset = struct.unpack("<I", file.read(4))[0]
				back = file.tell()
				file.seek(offset)
				time_relative = 0
				if curve_property == keyframe_property_type.QUANTIZED:
					P_MIN = from_ushort(struct.unpack("<H", file.read(2))[0])
					P_MAX = from_ushort(struct.unpack("<H", file.read(2))[0])
					M0_MIN = from_ushort(struct.unpack("<H", file.read(2))[0])
					M0_MAX = from_ushort(struct.unpack("<H", file.read(2))[0])
					M1_MIN = from_ushort(struct.unpack("<H", file.read(2))[0])
					M1_MAX = from_ushort(struct.unpack("<H", file.read(2))[0])
				if curve_property == keyframe_property_type.QUANTIZED_PRECISE:
					P_MIN = struct.unpack("<f", file.read(4))[0]
					P_MAX = struct.unpack("<f", file.read(4))[0]
					M0_MIN = struct.unpack("<f", file.read(4))[0]
					M0_MAX = struct.unpack("<f", file.read(4))[0]
					M1_MIN = struct.unpack("<f", file.read(4))[0]
					M1_MAX = struct.unpack("<f", file.read(4))[0]
				for c in range(0,keyframe_count):
					match curve_property:
						case keyframe_property_type.FULL_PRECISION:
							time = struct.unpack("<H", file.read(2))[0]
							file.read(2)
							P0 = struct.unpack("<f", file.read(4))[0]
							M0 = struct.unpack("<f", file.read(4))[0]
							M1 = struct.unpack("<f", file.read(4))[0]

							if transform_type == "location":
								P0 = pose_bone.location[transform_index] + P0
							keyframes.append([time,P0,M0,M1])
						case keyframe_property_type.QUANTIZED:
							time_relative += struct.unpack("<B", file.read(1))[0]
							P0 = struct.unpack("<B", file.read(1))[0]
							M0 = struct.unpack("<B", file.read(1))[0]
							M1 = struct.unpack("<B", file.read(1))[0]

							PVAL = P_MIN + P_MAX * P0
							M0VAL = M0_MIN + M0_MAX * M0
							M1VAL = M1_MIN + M1_MAX * M1

							if transform_type == "location":
								PVAL = pose_bone.location[transform_index] + PVAL
							
							keyframes.append([time_relative,PVAL,M0VAL,M1VAL])
						case keyframe_property_type.QUANTIZED_PRECISE:
							time = struct.unpack("<H", file.read(2))[0]
							P0 = struct.unpack("<H", file.read(2))[0]
							M0 = struct.unpack("<H", file.read(2))[0]
							M1 = struct.unpack("<H", file.read(2))[0]

							PVAL = P_MIN + P_MAX * P0
							M0VAL = M0_MIN + M0_MAX * M0
							M1VAL = M1_MIN + M1_MAX * M1

							if transform_type == "location":
								PVAL = pose_bone.location[transform_index] + PVAL
							
							keyframes.append([time,PVAL,M0VAL,M1VAL])
					

				for kf in keyframes:
					TIME = kf[0]
					p0 = kf[1]
					match transform_type:
						case "location":
							pose_bone.location = Vector((p0,p0,p0))
						case "rotation_euler":
							pose_bone.rotation_euler = Vector((p0,p0,p0))
						case "scale":
							pose_bone.scale = Vector((p0,p0,p0))	
					pose_bone.keyframe_insert(data_path=transform_type, index=transform_index, frame=TIME)  
					
				for kf in range(0,len(keyframes)-1):
					p0 = keyframes[kf][1]
					p1 = keyframes[kf + 1][1]
					
					m0 = keyframes[kf][3]
					m1 = keyframes[kf+1][2]

					fcurve = animation.fcurves.find(f'pose.bones["{bone_name}"].{transform_type}', index=transform_index)
					if fcurve.group != group:
						fcurve.group = group
						
					fcurve.keyframe_points[kf].handle_right_type = 'FREE'
					fcurve.keyframe_points[kf].handle_right.y = p0 + (m0 / 3.0)
					
					
					fcurve.keyframe_points[kf+1].handle_left_type = 'FREE'
					fcurve.keyframe_points[kf+1].handle_left.y = p1 - (m1 / 3.0)
				file.seek(back)

			pose_bone.location = (0.0, 0.0, 0.0)
			pose_bone.rotation_euler = (0.0, 0.0, 0.0)
			pose_bone.scale = (1.0, 1.0, 1.0)


def export_animation(file_path,self,armature,loops, movement_threshold, precision_only):
	action = armature.animation_data.action
	animation_frame_count = 0
	curves = []
	

	for curve in action.fcurves:
		for fc in curve.keyframe_points:
			if fc.co.x > animation_frame_count:
				animation_frame_count = round(fc.co.x)
		if "pose.bones" in curve.data_path:
			original_bone_name = curve.data_path.split("\"")[1]
			bone_name = curve.data_path.split("\"")[1]
			if "rotation_quaternion" in curve.data_path:
				#print("Data path " + curve.data_path + " contains quaternion rotation. quaternion rotation isn't supported. Make sure your bones are set to XYZ euler instead of Quaternion.")
				continue
			if bone_name == "root":
				bone_name = "0"
			if utility.is_int(bone_name) == False:
				#print("Curve " + curve.data_path + " have a bone that isn't in index mode. This curve was skipped.")
				continue

			bone_idx = int(bone_name)
			c_index = path_to_index(curve.data_path,curve.array_index)
			if c_index == -1:
				print("Data path " + curve.data_path + " contains a unknown transform. The curve was skipped.")
				continue
			property = curve.data_path.split(']')[1].replace(".","")
			sort_order = c_index + (bone_idx * 10)
			#print(curve.data_path, "    ", property, "    ",c_index, "     ", sort_order)
			curves.append([sort_order, bone_idx, original_bone_name, curve, property])
			
			
		else:
			print(curve.data_path +" was skipped due to being incompatible with skeletal animation.")
	
	reset_armature_pose(armature)
	property_count = len(curves)
	curves.sort(key=lambda x: x[0])

	if property_count >= 254:
		self.report({'ERROR'}, f"The animation contains 254 curves or more, delete some curves before exporting.")
		return {'CANCELLED'}


		
	offsets = []
	write_curves = []
	with open(file_path, "wb") as file:
		file.write(b"mtb3")
		file.write(struct.pack("<H",animation_frame_count + 1))
		file.write(struct.pack("<B",property_count + 1))
		file.write(struct.pack("<B", 1 if loops else 0))
		for i in range(0, property_count):
			if precision_only:
				property_config = keyframe_property_type.FULL_PRECISION
			else:
				property_config = get_curve_configuration(curves[i][3].keyframe_points, movement_threshold, 0.1 if "rotation_euler" not in curves[i][3].data_path else 0.01)

			print(
				curves[i][3].data_path,
				curves[i][3].array_index,
				len(curves[i][3].keyframe_points),
				property_config
			)
			
			property_type = data_path_to_type(curves[i][4], curves[i][3].array_index, property_config)
			if property_type == -1:
				print("curve could not be processed. His property could not be determined.")
				continue

			file.write(struct.pack("<b", curves[i][1]-1))
			file.write(struct.pack("<B", property_type)) #type


			if property_config != keyframe_property_type.POSE:
				file.write(struct.pack("<H", len(curves[i][3].keyframe_points)))
			else:
				file.write(struct.pack("<H", 1))


			value_offset = 0.0
			if property_config == keyframe_property_type.POSE:
				if curves[i][4] == "location":
					if curves[i][2] != "root":
						curve_index = curves[i][3].array_index
						bone = armature.pose.bones[curves[i][2]]
						bone.matrix = bone.parent.matrix
						value_offset = bone.location[curve_index]

				file.write(struct.pack("<f", curves[i][3].keyframe_points[0].co.y - value_offset))
			else:
				offsets.append(file.tell())
				file.write(struct.pack("<I", 0))
				time = []
				p0 = []
				m0 = []
				m1 = []

				if curves[i][4] == "location":
					if curves[i][2] != "root":
						curve_index = curves[i][3].array_index
						bone = armature.pose.bones[curves[i][2]]
						bone.matrix = bone.parent.matrix

						value_offset = bone.location[curve_index]
				for curve in curves[i][3].keyframe_points:


					
					HL = curve.handle_left.y - value_offset
					HR = curve.handle_right.y - value_offset
					P0 = curve.co.y - value_offset
					M0 = 3 * (P0 - HL)
					M1 = 3 * (HR - P0)

					p0.append(P0)
					m0.append(M0)
					m1.append(M1)
					time.append(round(curve.co.x))



				write_curves.append([property_config, p0,m0,m1, time])
				
		file.write(struct.pack("<I", 4294967167)) #terminator property
		file.write(struct.pack("<I", 0))

		for i in range(0,len(offsets)):
			backup_offset = file.tell()
			file.seek(offsets[i])
			file.write(struct.pack("<I", backup_offset))
			file.seek(backup_offset)


			min_p0 = min(write_curves[i][1])
			max_p0 = max(write_curves[i][1])
			min_m0 = min(write_curves[i][2])
			max_m0 = max(write_curves[i][2])
			min_m1 = min(write_curves[i][3])
			max_m1 = max(write_curves[i][3])
			match write_curves[i][0]:
				case keyframe_property_type.QUANTIZED:


					file.write((to_ushort(min_p0)).to_bytes(2,"little"))
					file.write((to_ushort((max_p0 - min_p0) / 255)).to_bytes(2,"little"))
					file.write((to_ushort(min_m0)).to_bytes(2,"little"))
					file.write((to_ushort((max_m0 - min_m0)  / 255)).to_bytes(2,"little"))
					file.write((to_ushort(min_m1)).to_bytes(2,"little"))
					file.write((to_ushort((max_m1 - min_m1)  / 255)).to_bytes(2,"little"))

					t = 0
					for data in range(0, len(write_curves[i][1])):
						#round(utility.map_value(i.co.y, min_p0, max_p0,0,255))
						file.write(struct.pack("<B", write_curves[i][4][data] - t))
						if min_p0 == max_p0:
							file.write(struct.pack('<B',1))
						else:
							file.write(struct.pack('<B',round(utility.map_value(write_curves[i][1][data], min_p0, max_p0,0,255))))
						if min_m0 == max_m0:
							file.write(struct.pack('<B',1))
						else:
							file.write(struct.pack('<B',round(utility.map_value(write_curves[i][2][data], min_m0, max_m0,0,255))))
						if min_m1 == max_m1:
							file.write(struct.pack('<B',1))
						else:
							file.write(struct.pack('<B',round(utility.map_value(write_curves[i][3][data], min_m1, max_m1,0,255))))


						t = write_curves[i][4][data]
				case keyframe_property_type.QUANTIZED_PRECISE:

					file.write(struct.pack("<f", min_p0))
					file.write(struct.pack("<f", (max_p0 - min_p0) / 65535))
					file.write(struct.pack("<f", min_m0))
					file.write(struct.pack("<f", (max_m0 - min_m0) / 65535))
					file.write(struct.pack("<f", min_m1))
					file.write(struct.pack("<f", (max_m1 - min_m1) / 65535))

					for data in range(0, len(write_curves[i][1])):
						file.write(struct.pack("<H", write_curves[i][4][data]))
						if min_p0 == max_p0:
							file.write(struct.pack('<H',1))
						else:
							file.write(struct.pack('<H',round(utility.map_value(write_curves[i][1][data], min_p0, max_p0,0,65535))))
						if min_m0 == max_m0:
							file.write(struct.pack('<H',1))
						else:
							file.write(struct.pack('<H',round(utility.map_value(write_curves[i][2][data], min_m0, max_m0,0,65535))))
						if min_m1 == max_m1:
							file.write(struct.pack('<H',1))
						else:
							file.write(struct.pack('<H',round(utility.map_value(write_curves[i][3][data], min_m1, max_m1,0,65535))))
				case keyframe_property_type.FULL_PRECISION:
					for data in range(0, len(write_curves[i][1])):
						file.write(struct.pack("<H", write_curves[i][4][data]))
						file.write(struct.pack("<H", 65535))

						file.write(struct.pack("<f", write_curves[i][1][data]))
						file.write(struct.pack("<f", write_curves[i][2][data]))
						file.write(struct.pack("<f", write_curves[i][3][data]))
				




def menu_func_import(self, context):
	self.layout.operator(ImportMOT.bl_idname,text="Import OKAMI Animation (.mot)",icon_value=icons.get_icon("okami"))
def menu_func_export(self, context):
	self.layout.operator(ExportMOT.bl_idname,text="Export OKAMI Animation (.mot)",icon_value=icons.get_icon("okami"))
classes = [ImportMOT,ExportMOT]



def register():
	for cls in classes:
		register_class(cls)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
def unregister():
	for cls in classes:
		unregister_class(cls)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)