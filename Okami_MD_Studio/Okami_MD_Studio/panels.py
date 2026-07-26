import bpy
import webbrowser
import textwrap
import bmesh

from bpy.utils import register_class
from bpy.utils import unregister_class
from bpy.types import Panel,Operator
from mathutils import Vector
from . import __init__
from . import icons
from . import mesh_op
from . import utility
from bpy.props import StringProperty


class VIEW3D_PT_OKAMDStudioPanel(Panel):
	bl_label = "Okami MD Sudio"
	bl_idname = "VIEW3D_PT_OKMDS_P1"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Okami'

	def draw(self, context):
		layout = self.layout
		scene = context.scene 
		l1 = layout.box()

		trsp = l1.split()
		trsp.prop(scene,"okami_show_mesh_utility",text="Mesh Utility", icon='MODIFIER') 
		trsp.prop(scene,"okami_show_vertex_utility",text="Vertex Utility", icon='SURFACE_NCURVE') 
		trsp.prop(scene,"okami_show_skeleton_utility",text="Armature Utility", icon='MOD_ARMATURE') 
		l1.prop(scene,"okami_show_animation_utility",text="Animation Utility", icon='ACTION') 
		obj = bpy.context.object



		if scene.okami_show_mesh_utility:
			#l1.label(text="Mesh Utility", icon='MODIFIER')
			layout.separator()
			#vbox = l1.box()
			#vbox.separator()

			
			vbox = l1.box()
			vbox.label(text="Mesh Utility", icon='MODIFIER')
			if obj and obj.type == 'MESH':
				est_size = mesh_op.estimate_size_interface(obj)
				if est_size == -1:
					vbox.label(text="Can't compute size estimation because there's quads in this mesh.")
				else:
					metric = "Bytes"
					if est_size >= 1024:
						est_size /= 1024
						metric = "KB"
					if est_size >= 1024:
						est_size /= 1024
						metric = "MB"
					if est_size >= 1024:
						est_size /= 1024
						metric = "GB"
					est_size = round(est_size)

					vbox.label(text="Estimated output size: " + str(est_size) + " " + metric)


			vbox.separator()
			vbox.operator("okamimdstudio.unusmat", text="Remove unused materials", icon='MATERIAL')
			vbox.operator("okamimdstudio.apply_modifiers", text="Apply deform modifiers", icon='MESH_DATA')
			vbox.operator("okamimdstudio.apply_rest_pose", text="Apply rest poses", icon='ARMATURE_DATA')
			layout.separator()

		if scene.okami_show_vertex_utility:
			layout.separator()
			vult = layout.box()
			b1 = vult.box()



			b1.operator("okamimdstudio.merge", text="Merge Vert Groups", icon='WPAINT_HLT')
			b2 = b1.box()
			b2.label(text="Verts to merge:")
			#print(scene.okami_bone_names)
			if scene.okami_bone_names == "":
				b2.label(text="No Vert Group queued to merge.")
			else:
				spl = scene.okami_bone_names.split("\n")
				for bone in spl:
					b2.label(text=bone)
			
			b1.operator("okamimdstudio.resetmerge", text="Reset merge", icon='WPAINT_HLT')
			vult.separator()
			b3 = vult.box()
			b3.operator("okamimdstudio.limitverts", text="Limit verts weights to 3 bones", icon='GROUP_BONE')
			b3.operator("okamimdstudio.unusgroup", text="Delete unusued vert groups from all meshes", icon='GROUP')
		
			layout.separator()
		
		if scene.okami_show_skeleton_utility:
			layout.separator()
			skel = layout.box()
			#skel.label(text="Armature Utility", icon='MOD_ARMATURE')
			b4 = skel.box()
			b4.operator("okamimdstudio.normalize_armature", text="Normalize Armature", icon='OUTLINER_OB_ARMATURE')
			b4.operator("okamimdstudio.renindex", text="Rename skeleton bones", icon='BONE_DATA')

			skel.label(text="Bone Matching Operations")
			skel2 = skel.box()

			skel2.prop(scene,"okami_bone_match_threshold") 
			skel2.separator()
			bt4 = skel2.box()
			if scene.okami_armature_name == "":
				bt4.label(text="No Armature added for matching operations.")
			else:
				spl = scene.okami_armature_name.split("\n")
				for bone in spl:
					bt4.label(text=bone)
			
			skel2.operator("okamimdstudio.saat", text="Add selected armature to matching operations", icon='ADD')
			skel2.operator("okamimdstudio.msarmc", text="Remove armature from match operation", icon='X')
			skel2.separator()
			skel2.separator()
			skel2.operator("okamimdstudio.sbtn", text="Match Armature bones (Selected)", icon='SYNTAX_OFF')
			skel2.operator("okamimdstudio.cbm", text="Remove bone matches (Selected)", icon='X')
			skel2.separator()
			skel2.operator("okamimdstudio.apbr", text="Apply bone matches", icon='META_CUBE')
			layout.separator()
			
		if scene.okami_show_animation_utility:
			la = layout.box()
			la.label(text="Keyframe Cleanup", icon='KEYFRAME');
			boxKFC = la.box()
			
			boxKFC.label(text="Remove Location Keyframes from selected:");
			rowMS = boxKFC.row()
			rowMS.operator("pose.delete_x_location_mot", icon='ORIENTATION_GLOBAL')
			rowMS.operator("pose.delete_y_location_mot", icon='ORIENTATION_GLOBAL');
			rowMS.operator("pose.delete_z_location_mot", icon='ORIENTATION_GLOBAL');
			boxKFC.operator("pose.delete_all_location_mot", icon='ORIENTATION_GLOBAL');


			boxMS2 = boxKFC.box()
			boxMS2.label(text="Remove Rotation Keyframes from selected:");

			rowMS = boxMS2.row()
			rowMS.operator("pose.delete_x_rotation_mot", icon='ORIENTATION_GLOBAL')
			rowMS.operator("pose.delete_y_rotation_mot", icon='ORIENTATION_GLOBAL');
			rowMS.operator("pose.delete_z_rotation_mot", icon='ORIENTATION_GLOBAL');     
			boxMS2.operator("pose.delete_all_rotation_mot", icon='ORIENTATION_GLOBAL');
			
			boxMS = boxKFC.box()
			boxMS.label(text="Remove Scale Keyframes from selected:");
			rowMS = boxMS.row()
			rowMS.operator("pose.delete_x_scale_mot", icon='ORIENTATION_GLOBAL')
			rowMS.operator("pose.delete_y_scale_mot", icon='ORIENTATION_GLOBAL');
			rowMS.operator("pose.delete_z_scale_mot", icon='ORIENTATION_GLOBAL');
			boxMS.operator("pose.delete_all_scale_mot", icon='ORIENTATION_GLOBAL');
			
			la.separator()
			la.separator()
			
			la.label(text="Curve Cleanup", icon='FCURVE');
			boxMS1 = la.box()
			curve_count = 0
			if obj and obj.type == 'ARMATURE':
				if obj.animation_data:
					if obj.animation_data.action:
						curve_count = len(obj.animation_data.action.fcurves)

			boxMS1.label(text="Curve count on the animation: " + str(curve_count))
			if curve_count >= 254:
				boxMS1.label(text="Script wont be able to export the animation, reduce to 253 curves or less.",icon="X")
			boxMS1.operator("pose.cleanup_mot_selected_okami", icon='ORIENTATION_GLOBAL')
			boxMS1.operator("pose.cleanup_mot_all_okami", icon='ORIENTATION_GLOBAL')
			boxMS1.prop(scene, "okami_simplify_factor", text="Cleanup Factor")




			layout.separator()
			row = layout.row()
			row.operator("okamimdstudio.open_github",text="Open GitHub Repository ♥", icon_value=icons.get_icon("github"))



class OKAMIMDSTUDIO_OT_OpenGithub(Operator):
	bl_idname = "okamimdstudio.open_github"
	bl_label = "Open Github"

	def execute(self, context):
		webbrowser.open("https://github.com/akitotheanimator/Okami-HD-Tools")
		return {'FINISHED'}


class OKAMIMDSTUDIO_OT_ApplyRest(Operator):
	bl_idname = "okamimdstudio.apply_rest_pose"
	bl_label = "Apply Skeleton Rest Pose"
	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None and (active_object.type == "ARMATURE" or active_object.type == "MESH")
	def execute(self, context):
		selected_object = bpy.context.selected_objects[0]
		bpy.ops.object.mode_set(mode='OBJECT')

		
		if selected_object.type == "ARMATURE":
			child_meshes = [child for child in selected_object.children if child.type == 'MESH']
			for obj in child_meshes:
				deform_modifiers = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']

				if deform_modifiers:
					for mod in deform_modifiers:
						if mod.type == "ARMATURE":
							if mod.object is not None:
								bpy.context.view_layer.objects.active = obj
								bpy.ops.object.modifier_apply(modifier=mod.name)
							else:
								obj.modifiers.remove(mod)
			bpy.context.view_layer.objects.active = selected_object
			bpy.ops.object.mode_set(mode='POSE')
			bpy.ops.pose.armature_apply(selected=False)
			bpy.ops.object.mode_set(mode='OBJECT')
			for obj in child_meshes:
				mod = obj.modifiers.new(name="Armature", type='ARMATURE')
				mod.object = selected_object


		else:
			deform_modifiers = [mod for mod in selected_object.modifiers if mod.type == 'ARMATURE']
			armature = None

			if deform_modifiers:
				for mod in deform_modifiers:
					if mod.type == "ARMATURE":
						if mod.object is not None:
							armature = mod.object

			if armature is None:
				self.report({'ERROR'}, f"Selected mesh doesn't have a valid armature modifier.")
				return {'CANCELLED'}

			child_meshes = [child for child in armature.children if child.type == 'MESH']
			for obj in child_meshes:
				deform_modifiers = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']

				if deform_modifiers:
					for mod in deform_modifiers:
						if mod.type == "ARMATURE":
							if mod.object is not None:
								bpy.context.view_layer.objects.active = obj
								bpy.ops.object.modifier_apply(modifier=mod.name)
							else:
								obj.modifiers.remove(mod)

			bpy.context.view_layer.objects.active = armature
			bpy.ops.object.mode_set(mode='POSE')
			bpy.ops.pose.armature_apply(selected=False)
			bpy.ops.object.mode_set(mode='OBJECT')
			for obj in child_meshes:
				mod = obj.modifiers.new(name="Armature", type='ARMATURE')
				mod.object = armature



		return {'FINISHED'} 
	
	
class OKAMIMDSTUDIO_OT_ApplyMods(Operator):
	bl_idname = "okamimdstudio.apply_modifiers"
	bl_label = "Apply Mesh Modifiers"
	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None and (active_object.type == "ARMATURE" or active_object.type == "MESH")
	def execute(self, context):
		
		selected_object = bpy.context.selected_objects[0]
		bpy.ops.object.mode_set(mode='OBJECT')

		
		if selected_object.type == "ARMATURE":
			child_meshes = [child for child in selected_object.children if child.type == 'MESH']
			for obj in child_meshes:
				deform_modifiers = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']

				if deform_modifiers:
					for mod in deform_modifiers:
						if mod.type == "ARMATURE":
							if mod.object is not None:
								bpy.context.view_layer.objects.active = obj
								bpy.ops.object.modifier_apply(modifier=mod.name)
							else:
								obj.modifiers.remove(mod)
		else:
			deform_modifiers = [mod for mod in selected_object.modifiers if mod.type == 'ARMATURE']

			if deform_modifiers:
				for mod in deform_modifiers:
					if mod.type == "ARMATURE":
						if mod.object is not None:
							bpy.context.view_layer.objects.active = selected_object
							bpy.ops.object.modifier_apply(modifier=mod.name)
						else:
							obj.modifiers.remove(mod)
		return {'FINISHED'} 

class OKAMIMDSTUDIO_OT_UnusMat(Operator):
	bl_label = ""
	bl_idname = "okamimdstudio.unusmat"
	bl_description = "Removes all unused materials from the selected mesh (UNUSED meaning the material has NO VERTICES assigned on it or INVALID materials)"
	
	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None and active_object.type == "MESH"
	
	def execute(self, context):
		obj = context.active_object
		materials = obj.data.materials

		used_indices = {
			face.material_index
			for face in obj.data.polygons
		}

		for i in range(len(materials)-1,-1,-1):
			if materials[i] is None or i not in used_indices:
				obj.data.materials.pop(index=i)
		

		return {'FINISHED'}		
class OKAMIMDSTUDIO_OT_Merge(Operator):
	bl_idname = "okamimdstudio.merge"
	bl_label = "Utility"
	bl_description = "Creates a vert group merging operation"
	def execute(self, context):
		bpy.ops.ed.undo_push()
		obj = bpy.context.object
		if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
			scene = context.scene
			if scene.okami_bone_names == "":
				selected_bones = bpy.context.selected_pose_bones
				if selected_bones:
					active_bone = selected_bones
					for bone in selected_bones:
						scene.okami_bone_names = scene.okami_bone_names + bone.name + "\n"
					scene.okami_bone_names = scene.okami_bone_names[:-1]
			else:
				selected_bones = bpy.context.selected_pose_bones
				if selected_bones:
					active_bone = selected_bones[0]
					spl = scene.okami_bone_names.split("\n")
					for vg in spl:
						if active_bone.name != vg:
							child_meshes = [child for child in obj.children if child.type == 'MESH']
							for objc in child_meshes:
								group_a = objc.vertex_groups.get(vg)
								group_b = objc.vertex_groups.get(active_bone.name)   
								if group_a:
									group_data = {}
									for vertex in objc.data.vertices:
										for group_element in vertex.groups:
											if group_element.group == group_a.index:
												group_data[vertex.index] = group_element.weight
									print(f"Vertex Group: {group_a.name}")
									if group_b:
										for vert_index, weight in group_data.items():
											group_b.add([vert_index], weight, type='ADD')
										objc.vertex_groups.remove(group_a)
									else:
										vertex_group = objc.vertex_groups.new(name=str(active_bone.name))
										for vert_index, weight in group_data.items():
											vertex_group.add([vert_index], weight, type='REPLACE')
										objc.vertex_groups.remove(group_a)
					bpy.context.view_layer.objects.active = obj
					bpy.ops.object.mode_set(mode='EDIT')
					edit_bones = obj.data.edit_bones
					 
					spl = scene.okami_bone_names.split("\n")
					for vg in spl:
						bone_to_delete = edit_bones.get(vg)
						if bone_to_delete:
							edit_bones.remove(bone_to_delete)
						 
					 
					bpy.ops.object.mode_set(mode='POSE')
					  
					scene.okami_bone_names = ""
					bpy.ops.ed.undo_push()
				else:
					self.report({'ERROR'}, f"You're trying to merge the same bone.")
					return {'CANCELLED'}	  
		
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_ResetMerge(Operator):
	bl_idname = "okamimdstudio.resetmerge"
	bl_label = "Utility"
	bl_description = "Resets the group you want to merge"
	def execute(self, context):
		context.scene.okami_bone_names = ""
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_Limit(Operator):
	bl_idname = "okamimdstudio.limitverts"
	bl_label = "Utility"
	bl_description = "Limits all vert groups of a selected mesh to only allow 3 bones per vert"

	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None and bpy.context.mode == "OBJECT" and active_object.type == "MESH"
	def execute(self, context):
		bpy.ops.object.vertex_group_limit_total(limit=3)
		return {'FINISHED'}    
class OKAMIMDSTUDIO_OT_UnusGroup(Operator):
	bl_idname = "okamimdstudio.unusgroup"
	bl_label = "Utility"
	bl_description = "Removes all groups which the bones doesn't exists\nSelect an armature, and then, execute this button"
	@classmethod
	def poll(cls, context):
		active_object = context.active_object  
		return active_object is not None and bpy.context.mode == "OBJECT" and active_object.type == "ARMATURE"
	def execute(self, context):
		scene = bpy.context.scene
		
		obj = context.active_object
		bone_names = {bone.name for bone in obj.data.bones}
		
		
		
		child_meshes = [child for child in obj.children if child.type == 'MESH']
		for cm in child_meshes:
			unused_groups = [vg for vg in cm.vertex_groups if vg.name not in bone_names]
			for vg in unused_groups:
				cm.vertex_groups.remove(vg)
		return {'FINISHED'}    
class OKAMIMDSTUDIO_OT_NormalizeArmature(Operator):
	bl_idname = "okamimdstudio.normalize_armature"
	bl_label = "Utility"
	bl_description = ("Normalizes the selected armature so the copy transform constraint is the same for every armature.")

	@classmethod
	def poll(cls, context):
		active_object = context.active_object
		return active_object is not None and active_object.type == "ARMATURE"

	def execute(self, context):
		obj = context.active_object
		utility.normalize_skeleton(context)
		self.report({'INFO'}, f"Normalized {len(obj.data.edit_bones)} bones")
		return {'FINISHED'} 
class OKAMIMDSTUDIO_OT_SetArmatureAsTarget(Operator):
	bl_idname = "okamimdstudio.saat"
	bl_label = "Utility"
	bl_description = "Add the currently selected armature to the matching operation armature. This will be the armature your mod will be targetting to."

	def execute(self, context):
		context.scene.okami_armature_name = context.selected_objects[0].name
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_SetBoneToName(Operator):
	bl_idname = "okamimdstudio.sbtn"
	bl_label = "Utility"
	bl_description = "Match the selected bones by distance and add Copy Transform constraints for remapping"
	@classmethod
	def poll(cls, context):
		active_object = context.active_object 
		if context.scene.okami_armature_name == "":
			return False
		arm = bpy.data.objects.get(context.scene.okami_armature_name)
		if arm == None or arm == active_object:
			return False
		return active_object is not None
	def execute(self, context):
		bpy.ops.object.mode_set(mode='POSE')
		scene = context.scene
		if scene.okami_armature_name == "":
			scene.okami_armature_name = context.selected_objects[0].name
			return {'FINISHED'}

		
		arm_a = context.selected_objects[0]
		arm_b = bpy.data.objects.get(scene.okami_armature_name)

		if not arm_a or not arm_b:
			self.report({'ERROR'}, "Invalid armatures")
			return {'CANCELLED'}
		
		selected_bones = context.selected_pose_bones
		if not selected_bones:
			self.report({'ERROR'}, "No bones selected.")
			return {'CANCELLED'}
		used_bones = set()

		for pb in arm_a.pose.bones:
			for c in pb.constraints:
				if (
					c.type == 'COPY_TRANSFORMS' and
					c.target == arm_b and
					c.subtarget
				):
					used_bones.add(c.subtarget)
		
		for bone_a in selected_bones:

			bone_a_head_world = arm_a.matrix_world @ bone_a.head

			closest_bone = None
			closest_distance = float('inf')

			for bone_b in arm_b.pose.bones:

				if bone_b.name in used_bones:
					continue

				bone_b_head_world = arm_b.matrix_world @ bone_b.head

				distance = (
					bone_a_head_world -
					bone_b_head_world
				).length

				if (
					distance < closest_distance and
					distance <= context.scene.okami_bone_match_threshold
				):
					closest_distance = distance
					closest_bone = bone_b

			if closest_bone is None:
				self.report({'WARNING'},f"No match found for bone '{bone_a.name}'")
				continue

			used_bones.add(closest_bone.name)

			# Remove previous Copy Transform constraints if desired
			for c in bone_a.constraints:
				if c.type == 'COPY_TRANSFORMS':
					bone_a.constraints.remove(c)

			con = bone_a.constraints.new('COPY_TRANSFORMS')
			con.target = arm_b
			con.subtarget = closest_bone.name

			print(
				f"{bone_a.name} -> "
				f"{closest_bone.name} "
				f"({closest_distance:.4f})"
			)

		
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_ClearBoneMatching(Operator):
	bl_idname = "okamimdstudio.cbm"
	bl_label = "Utility"
	bl_description = "Remove bones that are already matched with copy constraints"
	@classmethod
	def poll(cls, context):
		active_object = context.active_object 
		if context.scene.okami_armature_name == "":
			return False
		arm = bpy.data.objects.get(context.scene.okami_armature_name)
		if arm == None or arm == active_object:
			return False
		return active_object is not None
	def execute(self, context):
		bpy.ops.object.mode_set(mode='POSE')
		selected_bones = bpy.context.selected_pose_bones

		if not selected_bones:
			print("No bones selected")
		else:
			for bone in selected_bones:

				# Iterate backwards because we're removing items
				for constraint in reversed(bone.constraints):
					if constraint.type == 'COPY_TRANSFORMS':
						bone.constraints.remove(constraint)

			print("Copy Transform constraints removed.")
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_ClearArmatureName(Operator):
	bl_idname = "okamimdstudio.msarmc"
	bl_label = "Utility"
	bl_description = "Removes the target armature from the matching operation"
	def execute(self, context):
		context.scene.okami_armature_name = ""
		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_ApplyBoneRemap(Operator):
	bl_idname = "okamimdstudio.apbr"
	bl_label = "Apply Bone Remap"
	bl_description = ("Renames bones according to their Copy Transform constraints and renames matching vertex groups, making the currently selected armature compatible for exporting. (CANT REDO AFTER RUNNING THIS OPERATION)"
	)

	@classmethod
	def poll(cls, context):
		active_object = context.active_object 
		if context.scene.okami_armature_name == "":
			return False
		arm = bpy.data.objects.get(context.scene.okami_armature_name)
		if arm == None or arm == active_object:
			return False
		return (
			context.active_object and context.active_object.type == 'ARMATURE'
		)

	def execute(self, context):


		remapped_bones = set()
		scene = context.scene

		arm_a = context.active_object
		old_mode = arm_a.mode
		arm_b = bpy.data.objects.get(scene.okami_armature_name)

		

		arm_a.hide_set(False)
		arm_b.hide_set(False)

		arm_a.hide_viewport = False
		arm_b.hide_viewport = False


		bpy.ops.object.mode_set(mode='POSE')



		if arm_b is None:
			self.report({'ERROR'}, "Target armature not found")
			return {'CANCELLED'}

		used_targets = {}
		for bone in range(0,len(arm_a.pose.bones)):
			arm_a.pose.bones[bone].name = str(bone * 120)



		for bone in arm_a.pose.bones:

			for constraint in bone.constraints:

				if (constraint.type == 'COPY_TRANSFORMS' and constraint.target == arm_b and constraint.subtarget):

					target_name = constraint.subtarget

					if target_name in used_targets:
						self.report({'ERROR'},f"Duplicate target '{target_name}' used by "f"'{used_targets[target_name]}' and "f"'{bone.name}'")
						return {'CANCELLED'}

					used_targets[target_name] = bone.name


		bone_name_count = 1
		for bone in arm_b.pose.bones:
			if utility.is_int(bone.name):
				index = int(bone.name)
				if index > bone_name_count:
					bone_name_count = index
		bone_name_count += 1
		rename_list = set()
		for bone in arm_a.pose.bones:
			if len(bone.constraints) == 0:
				rename_list.add(bone)
				continue
			for constraint in list(bone.constraints):
				if (constraint.type == 'COPY_TRANSFORMS' and constraint.target == arm_b and constraint.subtarget):

					old_name = bone.name
					new_name = constraint.subtarget

					bone.name = new_name
					remapped_bones.add(new_name)
					bone.constraints.remove(constraint)

					print(f"{old_name} -> {new_name}")
		for bone in rename_list:
			print(bone.name + "    ...")
			bone.name = str(bone_name_count)
			bone_name_count += 1



		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.context.view_layer.objects.active = arm_b
		bpy.ops.object.mode_set(mode='EDIT')

		armature_b_parents = {}
		for bone_name in remapped_bones:
			source_bone = arm_b.data.edit_bones.get(bone_name)
			parent = source_bone.parent
			if parent != None:
				armature_b_parents[bone_name] = parent.name

		bpy.ops.object.mode_set(mode='OBJECT')

		bpy.context.view_layer.objects.active = arm_a
		bpy.ops.object.mode_set(mode='EDIT')
		edit_bones_a = arm_a.data.edit_bones

		for bone_name in remapped_bones:
			eb = edit_bones_a.get(bone_name)
			if eb:
				eb.parent = None
		for bone_name in remapped_bones:
			if bone_name not in armature_b_parents:
				continue
			source_bone = edit_bones_a.get(bone_name)
			source_parent = edit_bones_a.get(armature_b_parents[bone_name])
			
			if source_bone is None:
				continue

			source_bone.parent = source_parent

		self.report({'INFO'}, "Bone remapping applied")
		utility.normalize_skeleton(context)

		#bpy.ops.object.mode_set(mode='POSE')
		#arm_a.pose.bones[0].name = "root"
		#bpy.ops.object.mode_set(mode=old_mode)



		return {'FINISHED'}
class OKAMIMDSTUDIO_OT_Rename(Operator):
	bl_idname = "okamimdstudio.renindex"
	bl_label = "Reindex"
	bl_description = ("Renames bones automatically, while it produces a useable skeleton for export, it doesn't produce a useable skeleton for model replacing. Unless you edit all the animations from the original skeleton, do NOT use this feature unless you know what you're doing."
	)

	@classmethod
	def poll(cls, context):
		active_object = context.active_object 
		return (
			context.active_object and context.active_object.type == 'ARMATURE'
		)

	def execute(self, context):
		obj = context.active_object
		bpy.ops.object.mode_set(mode='POSE')
		for bone in range(1,len(obj.pose.bones)):
			obj.pose.bones[bone].name = str(bone)
		obj.pose.bones[0].name = "root"
		return {'FINISHED'}

class DAOperator(Operator):
	bl_idname = "pose.delete_all_location_mot"
	bl_label = "XYZ"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,0)
		return {'FINISHED'} 
class DXOperator(Operator):
	bl_idname = "pose.delete_x_location_mot"
	bl_label = "X"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,1)
		return {'FINISHED'}            
class DYOperator(Operator):
	bl_idname = "pose.delete_y_location_mot"
	bl_label = "Y"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,2)
		return {'FINISHED'}  
class DZOperator(Operator):
	bl_idname = "pose.delete_z_location_mot"
	bl_label = "Z"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,3)
		return {'FINISHED'}  
class DRAOperator(Operator):
	bl_idname = "pose.delete_all_rotation_mot"
	bl_label = "XYZ"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,4)
		return {'FINISHED'}  
class DRXOperator(Operator):
	bl_idname = "pose.delete_x_rotation_mot"
	bl_label = "X"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,5)
		return {'FINISHED'}               
class DRYOperator(Operator):
	bl_idname = "pose.delete_y_rotation_mot"
	bl_label = "Y"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,6)
		return {'FINISHED'}     
class DRZOperator(Operator):
	bl_idname = "pose.delete_z_rotation_mot"
	bl_label = "Z"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,7)
		return {'FINISHED'}   
class DSAOperator(Operator):
	bl_idname = "pose.delete_all_scale_mot"
	bl_label = "XYZ"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,8)
		return {'FINISHED'}  
class DSXOperator(Operator):
	bl_idname = "pose.delete_x_scale_mot"
	bl_label = "X"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,9)
		return {'FINISHED'}  
class DSYOperator(Operator):
	bl_idname = "pose.delete_y_scale_mot"
	bl_label = "Y"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,10)
		return {'FINISHED'}   
class DSZOperator(Operator):
	bl_idname = "pose.delete_z_scale_mot"
	bl_label = "Z"
	bl_options = {'REGISTER', 'UNDO'}
	def execute(self, context):
		utility.delete_curves(self,11)
		return {'FINISHED'} 
class CleanupOperatorSelected(Operator):
	bl_idname = "pose.cleanup_mot_selected_okami"
	bl_label = "Cleanup Curves (Selected Curves)"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = ("Simplifies only the selected curves of the animation as much as it can without altering how it looks. The higher the cleanup factor, the more it will clean. But, the more imprecise it will be.")
	def execute(self, context):
		bpy.ops.ed.undo_push()
	

		bpy.ops.graph.simplify_okami(error=context.scene.okami_simplify_factor, only_selected=False, mode='DISTANCE')

		return {'FINISHED'}  
class CleanupOperatorAll(Operator):
	bl_idname = "pose.cleanup_mot_all_okami"
	bl_label = "Cleanup Curves (All Curves)"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = ("Simplifies all curves of the animation as much as it can without altering how it looks. The higher the cleanup factor, the more it will clean. But, the more imprecise it will be.")
	def execute(self, context):
		bpy.ops.ed.undo_push()
	

		bpy.ops.graph.simplify_okami(error=context.scene.okami_simplify_factor, only_selected=False, mode='DISTANCE')

		return {'FINISHED'}  
class OBJECT_OT_Select_Strip(Operator):
	bl_idname = "okamimdstudio.selstrip"
	bl_label = ""
	bl_description = "Selects the desired strip in edit mode"
	
	
	strip: bpy.props.StringProperty()
	
	@classmethod
	def poll(cls, context):
		active_object = context.active_object   
		return active_object is not None
	def execute(self, context):
		obj = bpy.context.edit_object
		mesh = bmesh.from_edit_mesh(obj.data)
		mesh.faces.ensure_lookup_table()
		mesh.verts.ensure_lookup_table()
		spl = self.strip.split('|')
		for a in range(0,len(spl)-1):
			indexes = spl[a].split(' ')
			v0 = int(indexes[0])
			v1 = int(indexes[1])
			v2 = int(indexes[2])
			for face in mesh.faces:
				tr0 = face.verts[0].index
				tr1 = face.verts[1].index
				tr2 = face.verts[2].index
				trl = [tr0, tr1, tr2]
				if v0 in trl and v1 in trl and v2 in trl:
					face.select = True
					break
		bmesh.update_edit_mesh(obj.data)
		return {'FINISHED'}  

classes = (
	VIEW3D_PT_OKAMDStudioPanel,
	OKAMIMDSTUDIO_OT_OpenGithub,
	OKAMIMDSTUDIO_OT_ApplyRest,
	OKAMIMDSTUDIO_OT_ApplyMods,
	OKAMIMDSTUDIO_OT_UnusMat,
	OKAMIMDSTUDIO_OT_Merge,
	OKAMIMDSTUDIO_OT_ResetMerge,
	OKAMIMDSTUDIO_OT_Limit,
	OKAMIMDSTUDIO_OT_UnusGroup,
	OKAMIMDSTUDIO_OT_NormalizeArmature,
	OKAMIMDSTUDIO_OT_SetArmatureAsTarget,
	OKAMIMDSTUDIO_OT_SetBoneToName,
	OKAMIMDSTUDIO_OT_ApplyBoneRemap,
	OKAMIMDSTUDIO_OT_ClearBoneMatching,
	OKAMIMDSTUDIO_OT_ClearArmatureName,
	OKAMIMDSTUDIO_OT_Rename,
	DAOperator, DXOperator, DYOperator, DZOperator, DRAOperator, DRXOperator, DRYOperator, DRZOperator, DSAOperator, DSXOperator, DSYOperator, DSZOperator,
	CleanupOperatorSelected, CleanupOperatorAll,

	OBJECT_OT_Select_Strip

	)

def register():
	for cls in classes:
		register_class(cls)
		
	
def unregister():
	for cls in classes:
		unregister_class(cls)
