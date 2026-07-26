#this fucker is going to handle MD importing and exporting
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
from . import mesh_op

from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.types import Operator
from bpy.utils import register_class
from bpy.props import (StringProperty, BoolProperty, CollectionProperty, )
from . import utility

class version(IntEnum):
	MD = 0
	SCR = 1
class winding(IntEnum):
	NONE = 32768
	FRONT = 0
	BACK = 1


def align_16(file):
	while file.tell() % 16 != 0:
		file.write(b"\0")
def align_4(file):
	while file.tell() % 4 != 0:
		file.write(b"\0")
class ImportMD(Operator, ImportHelper):
	"""Import Okami Model"""
	bl_idname = "import_scene.okamimdstudio_md"
	bl_label = "Import Models"
	bl_options = {'REGISTER', 'UNDO'}

	filename_ext = ".md"
	filter_glob: StringProperty(default="*.md;*.scr;*.mdb", options={'HIDDEN'}, maxlen=255)
	files: CollectionProperty(type=bpy.types.PropertyGroup)
	PS2: BoolProperty(name="PS2 MD", description="This allows the addon to import MD files from the PS2 version of OKAMI.", default=False,)
	def execute(self, context):
		layout = self.layout	 
			
		directory = self.filepath
		directory = directory.replace(os.path.basename(directory),"")
		directory = directory[:-1]
		for file_elem in self.files:
			file_path = f"{directory}/{file_elem.name}"
			import_model(file_path,self)
		return {'FINISHED'}
class ExportMD(Operator, ExportHelper):
	"""Export Okami Model"""
	bl_idname = "export_scene.okamimdstudio_md"
	bl_label = "Export"
	bl_description = "Exports the whole model, as a MD with skeleton, meshes, etc."
	bl_options = {'REGISTER', 'UNDO'}


	filename: StringProperty(name="File Name", description="Name of the exported file", default="default_model_name.md")
	PS2: BoolProperty(name="PS2 MD", description="This allows the addon to import MD files from the PS2 version of OKAMI.", default=False,)

	filename_ext = ""
	filter_glob: StringProperty(default="", options={'HIDDEN'}, maxlen=255,)
	files: CollectionProperty(type=bpy.types.PropertyGroup)

	@classmethod
	def poll(cls, context):
		active_object = context.active_object
		if active_object is None:
			return False
		
		match active_object.type:
			case "ARMATURE":
				return True
			case "MESH":
				for mod in active_object.modifiers:
					if mod.type == 'ARMATURE':
						return (
							mod.object is not None and
							mod.object.type == 'ARMATURE'
						)
				return False
	def draw(self, context):
		layout = self.layout   
			
		armature = True
		active_object = context.active_object
		match active_object.type:
			case "ARMATURE":
				armature = True
			case "MESH":
				for mod in active_object.modifiers:
					if mod.type == 'ARMATURE':
						if mod.object is not None and mod.object.type == 'ARMATURE':
							armature = False
			
		#layout.prop(self,"export_format")
		spl = layout.split()
		spl.label(text="Format")
		box = spl.box()
		if armature:
			box.label(text="MD")
		else:
			box.label(text="MDB")
		layout.prop(self,"PS2")

	def invoke(self, context, event):
		directory = os.path.dirname(self.filepath)  # preserve last used folder
		if not directory:  # if first time, use Blender's default export path
			directory = "//"

		filename = bpy.path.ensure_ext(context.active_object.name, self.filename_ext)
		self.filepath = os.path.join(directory, filename)
		return super().invoke(context, event)
	
	
	def execute(self, context):
		armature = True
		active_object = context.active_object

		skeleton = active_object
		match active_object.type:
			case "ARMATURE":
				armature = True
			case "MESH":
				for mod in active_object.modifiers:
					if mod.type == 'ARMATURE':
						if mod.object is not None and mod.object.type == 'ARMATURE':
							armature = False



		file_path = self.filepath + ".md"
		
		if armature: #export a MD file
			child_meshes = [child for child in skeleton.children if child.type == 'MESH']
			if not child_meshes:
				self.report({'INFO'}, "No child meshes found.")
				return {'CANCELLED'}
			skeleton = active_object

			for mesh in child_meshes:
				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.select_all(action='DESELECT')
				if mesh.hide_get():
					mesh.hide_set(False)  # Unhide the object
				mesh.select_set(True)
				bpy.context.view_layer.objects.active = mesh
				bpy.ops.object.mode_set(mode='EDIT')
				bpy.ops.mesh.select_all(action='SELECT')
				bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='CLIP') #for consistency
				bpy.ops.mesh.select_all(action='DESELECT')
			for bone in skeleton.pose.bones:
				name = bone.name
				if name == "root":
					name = "0"
				if utility.is_int(name) == False:
					self.report({'ERROR'}, f"The selected skeleton's bone " + name + " is not in indexed mode. Delete it or rename it as a number.")
					return {'CANCELLED'}

			export_model(file_path, self, skeleton, child_meshes, self.PS2)
			
		else: #export a MDB file
			for mod in active_object.modifiers:
				if mod.type == 'ARMATURE':
					if mod.object is not None and mod.object.type == 'ARMATURE':
						file_path = self.filepath + ".mdb"
						for bone in mod.object.pose.bones:
							name = bone.name
							if name == "root":
								name = "0"
							if utility.is_int(name) == False:
								self.report({'ERROR'}, f"The selected skeleton's bone " + name + " is not in indexed mode. Delete it or rename it as a number.")
								return {'CANCELLED'}

						with open(file_path, "wb") as file:
							export_mdb(file ,self, mod.object, active_object, self.PS2)


						break



		return {'FINISHED'}
		

def export_model(file_path,self,armature, mesh_array, PS2):
	with open(file_path, "wb") as file:
		file.write(b"scr\0")
		file.write(struct.pack("<I", 0))
		file.write(struct.pack("<I", len(mesh_array)))
		file.write(struct.pack("<I", 0))
		offset = []
		for mesh in mesh_array:
			offset.append(file.tell())
			file.write(struct.pack("<I",0))

		align_16(file)
		data_offset = []
		for mesh in mesh_array:
			data_offset.append(file.tell())
			export_mdb(file, self,armature,mesh, PS2)

		for i in range(0,len(data_offset)):
			obj_offset = file.tell()
			file.seek(offset[i])
			file.write(struct.pack("<I", obj_offset))
			file.seek(obj_offset)
			file.write(struct.pack("<i", data_offset[i] - obj_offset))
			file.write(struct.pack("<I", 0))
			file.write(struct.pack("<f", 1))
			file.write(struct.pack("<f", 1))
			file.write(struct.pack("<f", 1))
			file.write(struct.pack("<f", 0))
			file.write(struct.pack("<f", 0))
			file.write(struct.pack("<f", 0))
			file.write(struct.pack("<f", 0))
			file.write(struct.pack("<f", 0))
			file.write(struct.pack("<f", 0))

			file.write(struct.pack("<I", 0))
			file.write(struct.pack("<I", 0))
			file.write(struct.pack("<I", 0))
			file.write(struct.pack("<I", 0))
			file.write(struct.pack("<I", 0))
			#file.write(struct.pack("<I", 0))





def export_mdb(file,self,armature, mesh, PS2):
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode='EDIT')


	bones = []
	for i in armature.data.edit_bones:
		name = i.name
		if name == "root":
			continue
		parent = -1
		pos = i.head
		if i.parent:
			pname = i.parent.name
			if pname == "root":
				pname = "0"
			parent = int(pname) - 1
			pos = i.head - i.parent.head


		#print(i.head, "  ", name)
		bones.append([int(name), pos, parent, name])
	bones.sort(key=lambda v: v[0])

	bone_name_to_index = {}
	bone_name_to_index["root"] = 0
	for i in range(0,len(bones)):
		bone_name_to_index[str(bones[i][3])] = i+1

	bpy.context.view_layer.objects.active = mesh
	bpy.ops.object.mode_set(mode='EDIT')

	vertices = []
	bm = bmesh.new()
	bm.from_mesh(mesh.data)
	uv_layer = bm.loops.layers.uv.active

	tvert = bm.verts
	tvert.sort(key=lambda v: v.index)



	for vert in tvert:
		position = vert.co.copy()
		normal = vert.normal.copy()
		color = (0,0,0)



		weights = []

		for g in mesh.data.vertices[vert.index].groups:
			group_index = g.group
			bone_name = str(mesh.vertex_groups[group_index].name)

			#bone = bone_name_to_index.get(bone_name, -1)
			bone = bone_name_to_index.get(bone_name,-1)
			if bone == -1:
				continue

			if g.weight < 0.01:
				continue

			weights.append((bone-1, g.weight))
		if len(weights) > 3:
			self.report({'ERROR'}, f"The mesh {mesh.name} contains a vert that's present in more than 3 bone groups. That's not allowed.")
			return
		
		res = [position, normal, color, weights]
		#if res not in vertices:
		vertices.append(res)
	#now, the part that is actually fucked up, the stripification part

	materials = mesh.data.materials


	indice_build = []
	bpy.ops.object.mode_set(mode='OBJECT')
	strips_all = mesh_op.sort_mesh(self,bpy.context)


	for a in strips_all:
		face = mesh_op.find_face(bm.faces, a[0], a[1], a[2])
		if face == None:
			print("wtf, wasn't it found?? ", face)
			return
		material = materials[face.material_index]
		
		ret = [material,[]]
		if ret not in indice_build:
			indice_build.append(ret)
	for a in strips_all:
		face = mesh_op.find_face(bm.faces, a[0], a[1], a[2])
		if face == None:
			print("wtf, wasn't it found?? ", face)
			return
		material = materials[face.material_index]
		for rep in indice_build:
			if material == rep[0]:
				strip = []
				#print(a)
				for sp in range(0,len(a)):
					winding = 32768
					if sp > 1:
						winding = sp % 2
					strip.append([winding, a[sp]])
				rep[1].extend(strip)
				#for spli in a:
				#	print(spli)
				#continue




	#print(indice_build)
	


	base_offset = file.tell()
	file.write(b"mdb\0")
	bone_offset_0 = file.tell()
	file.write(struct.pack("<I",0))
	file.write(struct.pack("<H",len(armature.pose.bones)-1))
	file.write(struct.pack("<H",len(indice_build))) #each item has a material, so this is valid to identify different submeshes.
	file.write(struct.pack("<I",0));file.write(struct.pack("<I",0)) #when i try to write down a long, it simply wont work...damn man
	file.write(struct.pack("<I",0));file.write(struct.pack("<I",0))
	file.write(struct.pack("<I",0))

	mesh_data_offset = []
	for i in range(0, len(indice_build)):
		mesh_data_offset.append(file.tell())
		file.write(struct.pack("<I",0))


	align_16(file)
	bone_offset_1 = file.tell()
	file.seek(bone_offset_0)
	file.write(struct.pack("<I",bone_offset_1 - base_offset))
	file.seek(bone_offset_1)


	#print(len(bones))


	for b in bones:
		file.write(struct.pack("<f", b[1].x))
		file.write(struct.pack("<f", b[1].z))
		file.write(struct.pack("<f", -b[1].y))
		file.write(struct.pack("<i", b[2]))



	uv_lookup = {}
	for face in bm.faces:
		uvs = []
		for loop in range(0,len(face.loops)):
			vert_index = face.loops[loop].vert.index
			uv = face.loops[loop][uv_layer].uv.copy()
			uvs.append([loop, vert_index, uv])


		uvs.sort(key=lambda v: v[1])
		key = str(uvs[0][1]) + "|" +  str(uvs[1][1]) + "|" +  str(uvs[2][1])
		#print("starting... ", key)

		#uvs.sort(key=lambda v: v[0])
		uv_lookup[key] = [uvs[0][1], uvs[0][2], uvs[1][1], uvs[1][2], uvs[2][1], uvs[2][2]]




	for i in range(0, len(indice_build)):
		vcount = 0
		for strip in indice_build[i][1]:
			vcount += 1

		
		bkp = file.tell()
		file.seek(mesh_data_offset[i])
		file.write(struct.pack("<I", bkp - base_offset))
		file.seek(bkp)

		file.write(struct.pack("<I", 32)) #this is the size of the data header... in other words, this is a fixed value
		file.write(struct.pack("<I", 0)) #specifically for okami, normals dont exist
		
		uv_offset = file.tell()
		file.write(struct.pack("<I", 0))

		color_offset = file.tell()
		file.write(struct.pack("<I", 0))

		weight_offset = file.tell()
		file.write(struct.pack("<I", 0))


		file.write(struct.pack("<H", vcount))
		file.write(struct.pack("<H", int(indice_build[i][0].name.split('.')[0]))) #material index
		file.write(struct.pack("<I", 0))
		file.write(struct.pack("<I", 0))
		for strip in indice_build[i][1]:
			winding = strip[0]
			position = vertices[strip[1]][0]
			file.write(struct.pack("<f", position.x))
			file.write(struct.pack("<f", position.z))
			file.write(struct.pack("<f", -position.y))
			file.write(struct.pack("<I", winding))
		
		if 1>4:
			#normals are not stored in md files for okami... but IF they were...
			for strip in indice_build[i][1]:
				position = vertices[strip[1]][1] #normal
				file.write(struct.pack("<b", utility.map_signed_byte(position[0])))
				file.write(struct.pack("<b", utility.map_signed_byte(position[1])))
				file.write(struct.pack("<b", utility.map_signed_byte(position[2])))
				file.write(b"\0")


			#print(winding)
			#print(vertices[strip[1]][1])

		uv_fs = file.tell()
		file.seek(uv_offset)
		file.write(struct.pack("<I", uv_fs - bkp))
		file.seek(uv_fs)


		uv_index_drag = 0
		def restart_drag(start):
			for strip in range(start,len(indice_build[i][1])):
				winding = indice_build[i][1][strip][0]
				if winding != 32768:
					return strip
		restart_drag(0)
		for strip in range(0,len(indice_build[i][1])):
			#uv = vertices[strip[1]][2]
			winding = indice_build[i][1][strip][0]
			idx = indice_build[i][1][strip][1]

			#uv_final = Vector((0,0))

			if winding != 32768:
				uv_index_drag = strip
			else:
				uv_index_drag = restart_drag(strip)

			v0 = indice_build[i][1][uv_index_drag-2][1]
			v1 = indice_build[i][1][uv_index_drag-1][1]
			v2 = indice_build[i][1][uv_index_drag-0][1]
			indices_sort = [v0, v1, v2]
			indices_sort.sort()

			key = str(indices_sort[0]) + "|" +str(indices_sort[1]) + "|" +str(indices_sort[2])
			#print("retrieving... ", key)
			if key in uv_lookup:
				uvdata = uv_lookup[key]
				if uvdata[0] == idx:
					uv_final = uvdata[1]
				if uvdata[2] == idx:
					uv_final = uvdata[3]
				if uvdata[4] == idx:
					uv_final = uvdata[5]

			if 1>5:
				for face in bm.faces:
					matches = 0
					for loop in face.loops:
						vert_index = loop.vert.index
						if vert_index == v0 or vert_index == v1 or vert_index == v2:
							matches += 1
					if matches == 3:
						for loop in face.loops:
							vert_index = loop.vert.index
							if vert_index == idx:
								uv = loop[uv_layer].uv.copy()
								uv_final = uv
								break

						break
				print(uv_final)





			file.write(struct.pack("<h", round(uv_final.x * 4096)))
			file.write(struct.pack("<h", round(uv_final.y * -4096)))
		print("--------")
		align_16(file)


		color_fs = file.tell()
		file.seek(color_offset)
		file.write(struct.pack("<I", color_fs - bkp))
		file.seek(color_fs)

		for strip in indice_build[i][1]:
			file.write(struct.pack("<I", 2155905152)) #vert color unimplemented.
		align_16(file)		

		weight_fs = file.tell()
		file.seek(weight_offset)
		file.write(struct.pack("<I", weight_fs - bkp))
		file.seek(weight_fs)

		for strip in indice_build[i][1]:
			bone_mapping = vertices[strip[1]][3]
			#print(bone_mapping)

			if len(bone_mapping) == 0:
				file.write(struct.pack("<I", 0))
				file.write(struct.pack("<I", 0))
				continue


			file.write(b"\0")
			for b in bone_mapping:
				if PS2:
					if b[0] * 4 > 255:
						self.report({'ERROR'}, f"There's more than 63 bones in this model. Reduce the bone count.")
						return {'CANCELLED'}
					file.write(struct.pack("<B", int(round(b[0] * 4))))
				else:
					file.write(struct.pack("<B", b[0]))
			align_4(file)
			weights = [] #must be normalized
			if PS2:
				for b in range(0,len(bone_mapping)):
					weight = math.floor(bone_mapping[b][1] * 100)
					weights.append([b, weight])

				weights.sort(key=lambda v: v[1])
				while sum(w[1] for w in weights) < 100:
					weights[0][1] += 1



				weights.sort(key=lambda v: v[0])
				for w in weights:
					file.write(struct.pack("<B", w[1]))
				align_4(file)
			else:
				for b in range(0,len(bone_mapping)):
					weight = math.floor(bone_mapping[b][1] * 255)
					weights.append([b, weight])

				weights.sort(key=lambda v: v[1])
				while sum(w[1] for w in weights) < 255:
					weights[0][1] += 1



				weights.sort(key=lambda v: v[0])
				for w in weights:
					file.write(struct.pack("<B", w[1]))
				align_4(file)

			

				
			





		align_16(file)


def import_model(file_path,self):
		
		if bpy.context.view_layer.objects.active:
			bpy.ops.object.mode_set(mode='OBJECT')
		with open(file_path, "rb") as file:
			filemagic = file.read(4)
			is_scr = filemagic == b"scr\0"
			
			if is_scr == False and filemagic != b"mdb\0":
				self.report({'ERROR'}, f"The imported file is not a valid model file.")
				return {'CANCELLED'}

			if is_scr:
				md_version = struct.unpack("<I", file.read(4))[0]
				if md_version == version.MD:
					bpy.ops.object.armature_add(enter_editmode = True, location=(0, 0, 0))
					main_armature = bpy.context.object
					bpy.context.view_layer.objects.active = main_armature
					main_armature.name = os.path.basename(file_path)

					
					root = main_armature.data.edit_bones[0]
					root.name = "root"
					root.head = Vector((0, 0, 0))
					root.tail = Vector((0, 0, 0.25))
					root.roll = 0
					bpy.ops.object.mode_set(mode='OBJECT')


				#version 0 = MD
				#version 1 = SCR
				#version 3 and so on is for GOD HAND, but since this addon is focused on OKAMI, i will strip GOD HAND's compatibility
				#basically is telling if the file is quantized or nah
				
				mesh_count = struct.unpack("<I", file.read(4))[0]
				file.seek(16)

				offset = []
				for i in range(0,mesh_count):
					data_offset = struct.unpack("<I", file.read(4))[0]
					offset.append(data_offset)
				offset.append(-1)

				for i in range(0,len(offset)-1):
					
					mdb_offset1 = 0
					if offset[i+1] != -1:
						file.seek(offset[i+1])
						mdb_offset1 = offset[i+1] + struct.unpack("<i", file.read(4))[0]
					else:
						mdb_offset1 = offset[0]

					file.seek(offset[i])
					mdb_offset0 = offset[i] + struct.unpack("<i", file.read(4))[0]

					file.seek(mdb_offset0)

					stream = io.BytesIO(file.read(mdb_offset1 - mdb_offset0))
					file.seek(offset[i]+4)






					

					match md_version:
						case version.MD:
							unk1 = struct.unpack("<I", file.read(4))[0]
							main_armature.scale.x = struct.unpack("<f", file.read(4))[0]
							main_armature.scale.y = struct.unpack("<f", file.read(4))[0]
							main_armature.scale.z = struct.unpack("<f", file.read(4))[0]

							main_armature.rotation_euler[0] = struct.unpack("<f", file.read(4))[0]
							main_armature.rotation_euler[1] = struct.unpack("<f", file.read(4))[0]
							main_armature.rotation_euler[2] = struct.unpack("<f", file.read(4))[0]

							main_armature.location.x = struct.unpack("<f", file.read(4))[0]
							main_armature.location.z = -struct.unpack("<f", file.read(4))[0]
							main_armature.location.y = struct.unpack("<f", file.read(4))[0]
							unk2 = file.read(20) #it's possible MD contains flags which still needs research
							import_mdb(main_armature, stream, self, md_version, str(i), self.PS2)
						case version.SCR:
							bpy.ops.object.armature_add(enter_editmode = True, location=(0, 0, 0))
							armature = bpy.context.object
							bpy.context.view_layer.objects.active = armature
							armature.name = str(i) + "." + os.path.basename(file_path)

							
							root = armature.data.edit_bones[0]
							root.name = "root"
							root.head = Vector((0, 0, 0))
							root.tail = Vector((0, 0, 0.25))
							root.roll = 0
							bpy.ops.object.mode_set(mode='OBJECT')


							unk1 = file.read(18)
							armature.location.x = struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.location.z = -struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.location.y = struct.unpack("<h", file.read(2))[0] / 4096.0

							armature.rotation_euler[0] = struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.rotation_euler[1] = struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.rotation_euler[2] = struct.unpack("<h", file.read(2))[0] / 4096.0

							armature.scale.x = struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.scale.y = struct.unpack("<h", file.read(2))[0] / 4096.0
							armature.scale.z = struct.unpack("<h", file.read(2))[0] / 4096.0

							unk2 = file.read(12) #it's possible MD contains flags which still needs research
							import_mdb(armature, stream, self, md_version, str(i), self.PS2)
			else:
				bpy.ops.object.armature_add(enter_editmode = True, location=(0, 0, 0))
				main_armature = bpy.context.object
				bpy.context.view_layer.objects.active = main_armature
				main_armature.name = os.path.basename(file_path)

				
				root = main_armature.data.edit_bones[0]
				root.name = "root"
				root.head = Vector((0, 0, 0))
				root.tail = Vector((0, 0, 0.25))
				root.roll = 0
				bpy.ops.object.mode_set(mode='OBJECT')

				file.seek(0,2)
				end = file.tell()
				file.seek(0)
				stream = io.BytesIO(file.read(end))
				import_mdb(main_armature, stream, self, version.MD)
def import_mdb(armature, stream,self, type, name = "mesh",PS2=False):
	filemagic = stream.read(4)
	if filemagic != b"mdb\0":
		self.report({'ERROR'}, f"The imported file is not a valid mdb file.")
		return
	skeleton_bones_offset = struct.unpack("<I",stream.read(4))[0]
	bone_count = struct.unpack("<H",stream.read(2))[0]
	mesh_count = struct.unpack("<H",stream.read(2))[0]
	mesh_offsets = []
	stream.seek(32)
	for _ in range(0, mesh_count):
		mesh_offsets.append(struct.unpack("<I",stream.read(4))[0])

	stream.seek(skeleton_bones_offset)
	bpy.ops.object.mode_set(mode='EDIT')

	for i in range(0,bone_count):
		x = struct.unpack("<f",stream.read(4))[0]
		y = struct.unpack("<f",stream.read(4))[0]
		z = struct.unpack("<f",stream.read(4))[0]
		#print(file.tell())
		parent = struct.unpack("<i",stream.read(4))[0] + 1
		if armature.data.edit_bones.get(str(i+1)) != None:
			continue


		bone = armature.data.edit_bones.new(str(i+1))
		bone.head = Vector((x, -z, y))
		bone.use_connect = False
		bone.parent = armature.data.edit_bones[parent]
		bone.head += armature.data.edit_bones[parent].head
		bone.tail = bone.head + Vector((0, 0, 0.25))
	

	for bone in armature.pose.bones:
		bone.rotation_mode = 'XYZ'


	
	bpy.ops.object.mode_set(mode='OBJECT')
	mesh = bpy.data.meshes.new(name)
	mesh_object = bpy.data.objects.new(name, mesh)
	bpy.context.collection.objects.link(mesh_object)
	mesh_object.parent = armature
	armature_modifier = mesh_object.modifiers.new(name="Armature", type='ARMATURE')
	armature_modifier.object = armature
	bm = bmesh.new()

	uvs = []
	normals = []
	colors = []
	weights = []
	for mesh_offset in mesh_offsets:
		stream.seek(mesh_offset)
		vertices_offset = struct.unpack("<I",stream.read(4))[0]
		normals_offset = struct.unpack("<I",stream.read(4))[0]
		uvs_offset = struct.unpack("<I",stream.read(4))[0]
		vertex_color_offset = struct.unpack("<I",stream.read(4))[0]
		weights_offset = struct.unpack("<I",stream.read(4))[0]
		vert_count = struct.unpack("<H",stream.read(2))[0]
		texture_index = struct.unpack("<H",stream.read(2))[0]


		mat = bpy.data.materials.get(str(texture_index))
		if not mat:
			mat = bpy.data.materials.new(name=str(texture_index))
		mesh_object.data.materials.append(mat)
		material_index = mesh_object.data.materials.find(mat.name)
		


		if vertices_offset != 0:
			stream.seek(mesh_offset + vertices_offset)

			for i in range(0,vert_count):
				if type == version.MD:
					x = struct.unpack("<f",stream.read(4))[0]
					y = struct.unpack("<f",stream.read(4))[0]
					z = struct.unpack("<f",stream.read(4))[0]
					winding_order = struct.unpack("<I",stream.read(4))[0]
				else:
					x = (struct.unpack("<h",stream.read(2))[0] / 100)
					y = (struct.unpack("<h",stream.read(2))[0] / 100)
					z = (struct.unpack("<h",stream.read(2))[0] / 100)
					winding_order = struct.unpack("<H",stream.read(2))[0]
				bm.verts.new(Vector((x, -z, y)))	
				bm.verts.ensure_lookup_table()
				match winding_order:
					case winding.FRONT:
						f = bm.faces.new([bm.verts[len(bm.verts)-3],bm.verts[len(bm.verts)-2],bm.verts[len(bm.verts)-1]])
						f.material_index = material_index
					case winding.BACK:
						f = bm.faces.new([bm.verts[len(bm.verts)-2],bm.verts[len(bm.verts)-3],bm.verts[len(bm.verts)-1]])
						f.material_index = material_index
		if normals_offset != 0:
			stream.seek(mesh_offset + normals_offset)
			for i in range(0,vert_count):
				if type == version.MD:
					x = (utility.map_signed_byte(struct.unpack("<b", stream.read(1))[0]) * -1)
					y = (utility.map_signed_byte(struct.unpack("<b", stream.read(1))[0]) * -1)
					z = (utility.map_signed_byte(struct.unpack("<b", stream.read(1))[0]) * -1)
					struct.unpack("<b", stream.read(1))[0] #unused
				
					le = math.sqrt(x*x + y*y + z*z)

					x = x / le
					y = y / le
					z = z / le
				else:
					x = 0
					y = 0
					z = 0
				normals.append(Vector(x*-1,z,y*-1))
		if uvs_offset != 0:
			stream.seek(mesh_offset + uvs_offset)
			
			for i in range(0,vert_count):
				x = (struct.unpack("<h",stream.read(2))[0] / 4096.0)
				y = ((struct.unpack("<h",stream.read(2))[0] / 4096.0) * -1)
				uvs.append([x,y])
		if vertex_color_offset != 0:
			stream.seek(mesh_offset + vertex_color_offset)
			for i in range(0,vert_count):
				r = struct.unpack("<B",stream.read(1))[0] / 128
				g = struct.unpack("<B",stream.read(1))[0] / 128
				b = struct.unpack("<B",stream.read(1))[0] / 128
				a = struct.unpack("<B",stream.read(1))[0] / 128
				colors.append([r, g, b, a])
		if weights_offset != 0:
			stream.seek(mesh_offset + weights_offset)
			for i in range(0,vert_count):
				#print(stream.tell(), "  ", i, "  ", vert_count)
				stream.read(1)
				if PS2 == False:
					bone_0 = str(struct.unpack("<B",stream.read(1))[0] + 1)
					bone_1 = str(struct.unpack("<B",stream.read(1))[0] + 1)
					bone_2 = str(struct.unpack("<B",stream.read(1))[0] + 1)
				else:
					bone_0 = str(round(struct.unpack("<B",stream.read(1))[0] / 4) + 1)
					bone_1 = str(round(struct.unpack("<B",stream.read(1))[0] / 4) + 1)
					bone_2 = str(round(struct.unpack("<B",stream.read(1))[0] / 4) + 1)

				if PS2 == False:
					weight_0 = struct.unpack("<B",stream.read(1))[0] / 255.0
					weight_1 = struct.unpack("<B",stream.read(1))[0] / 255.0
					weight_2 = struct.unpack("<B",stream.read(1))[0] / 255.0
				else:
					weight_0 = struct.unpack("<B",stream.read(1))[0] / 100.0
					weight_1 = struct.unpack("<B",stream.read(1))[0] / 100.0
					weight_2 = struct.unpack("<B",stream.read(1))[0] / 100.0
				stream.read(1)
				weights.append((bone_0,bone_1,bone_2,weight_0,weight_1,weight_2))


	bm.to_mesh(mesh)
	mesh.update()
	if len(normals) != 0:
		mesh.normals_split_custom_set_from_vertices(normals)
	uv_layer = mesh.uv_layers.new(name="UVMap")
	for poly in mesh.polygons:
		for loop_idx in poly.loop_indices:
			vi = mesh.loops[loop_idx].vertex_index
			uv_layer.data[loop_idx].uv = uvs[vi]

	color_layer = mesh.color_attributes.new(name="COLOR", type="FLOAT_COLOR", domain="POINT")
	for i in range(0,len(bm.verts)):
		color_layer.data[i].color = (colors[i][0], colors[i][1], colors[i][2], colors[i][3])
	for i in range(0,len(weights)):
		b0n = weights[i][0]
		b1n = weights[i][1]
		b2n = weights[i][2]
		b0infl = weights[i][3]
		b1infl = weights[i][4]
		b2infl = weights[i][5]


		if b0n in mesh_object.vertex_groups:
			bone0_group = mesh_object.vertex_groups[b0n]
		else:
			bone0_group = mesh_object.vertex_groups.new(name=b0n)
		


		if b1n in mesh_object.vertex_groups:
			bone1_group = mesh_object.vertex_groups[b1n]
		else:
			bone1_group = mesh_object.vertex_groups.new(name=b1n)



		if b2n in mesh_object.vertex_groups:
			bone2_group = mesh_object.vertex_groups[b2n]
		else:
			bone2_group = mesh_object.vertex_groups.new(name=b2n)

			
		bone0_group.add([i], b0infl, 'ADD')
		bone1_group.add([i], b1infl, 'ADD')
		bone2_group.add([i], b2infl, 'ADD')

	mesh.update()
	bm.free()
	bpy.context.view_layer.objects.active = armature
	bpy.context.object.show_in_front = True
	bpy.context.object.data.display_type = 'STICK'



def menu_func_import(self, context):
	self.layout.operator(ImportMD.bl_idname,text="Import OKAMI Model (.md / .scr / .mdb)",icon_value=icons.get_icon("okami"))
def menu_func_export(self, context):
	self.layout.operator(ExportMD.bl_idname,text="Export OKAMI Model (.md / .mdb)",icon_value=icons.get_icon("okami"))
classes = [ImportMD, ExportMD]



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