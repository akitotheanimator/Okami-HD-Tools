import bpy
import bmesh
from . import types


#helpers
def get_vert_indices(mesh_face):
	return [v.index for v in mesh_face.verts]




def get_faces_and_materials(obj, self, bm):
	materials = obj.data.materials

	if not materials:
		self.report({'ERROR'}, f"No materials assigned to {obj.name}")
		return {'CANCELLED'}

	face_groups = [] #initialize the face groups and set their size
	for i in range(len(materials)):
		face_groups.append([])

	for face in bm.faces:
		mat_index = face.material_index
		if mat_index >= len(materials):
			self.report({'ERROR'},f"Face uses invalid material index {mat_index} in {obj.name}")
			return {'CANCELLED'}
		face_groups[mat_index].append(face) #Now, add the face to the array based on the material index
	faces_with_material = [] #initialize for the next steps...

	for mat_index, material in enumerate(materials):

		try: #this now checks if the material name is valid, otherwise we aint proceeding
			material.name
		except Exception:
			self.report({'ERROR'},f'The mesh "{obj.name}" contains an invalid material.')
			return {'CANCELLED'}

		if not face_groups[mat_index]: #If the material FOR SOME REASON has NO triangles assigned to it, return an error to the user
			#"why not to remove it automatically?" Bcuz i have NO IDEA if the user will use that material later, so i can't do that on this op...
			self.report({'ERROR'},f'The material "{material.name}" is assigned in mesh "{obj.name}", 'f'but does not contain any triangle assigned.')
			return {'CANCELLED'}

		faces_with_material.append([face_groups[mat_index], material])

	return faces_with_material




def sort_mesh(self, context):
	obj = bpy.context.object


	previous_mode = bpy.context.mode
	bpy.ops.object.mode_set(mode='EDIT')
	me = obj.data
	bm = bmesh.from_edit_mesh(me)


	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='CLIP') #for consistency
	bpy.ops.mesh.select_all(action='DESELECT')



	bm.faces.ensure_lookup_table()
	start_face = min(bm.faces,key=lambda f: sum(len(e.link_faces) - 1 for e in f.edges))
	start_face.select = True


	for face in bm.faces:
		mat_index = start_face.material_index

		if mat_index > len(obj.data.materials):
			self.report({'ERROR'}, "One or more faces are using materials that doesn't exist within the model. Please reasign a valid material to the prohibited faces")
			return


	def edge_direction_in_face(face, edge):
		"""Returns +1 if edge appears as (v1,v2), -1 if as (v2,v1), 0 if not in face."""

		v1, v2 = edge

		loops = face.loops

		for i, loop in enumerate(loops):
			a = loop.vert.index
			b = loops[(i + 1) % len(loops)].vert.index

			if (a, b) == (v1, v2):
				return 1

			if (a, b) == (v2, v1):
				return -1

		return 0
	def uv_connected(face_a, face_b, uv_layer):
		def uv_edges(face):
			edges = set()
			loops = face.loops

			for i, loop in enumerate(loops):
				uv1 = tuple(loop[uv_layer].uv)
				uv2 = tuple(loops[(i + 1) % len(loops)][uv_layer].uv)

				edges.add(tuple(sorted((uv1, uv2))))

			return edges

		return not uv_edges(face_a).isdisjoint(uv_edges(face_b))

	sorted_strips = []
	remaining = set(bm.faces)

	uv_layer = bm.loops.layers.uv.active
	
	while remaining:

		seed = min(
			remaining,
			key=lambda f: sum(
				1
				for e in f.edges
				for n in e.link_faces
				if n in remaining
			)
		)

		remaining.remove(seed)

		strip = [seed]
		seed_material = seed.material_index

		# Build initial strip edge later.
		last_edge = None

		while True:

			current = strip[-1]

			candidate = None
			candidate_edge = None

			# First triangle:
			if last_edge is None:

				for edge in current.edges:

					shared_edge = (
						edge.verts[0].index,
						edge.verts[1].index,
					)

					dir_a = edge_direction_in_face(current, shared_edge)

					for n in edge.link_faces:

						if n not in remaining:
							continue

						if n.material_index != seed_material:
							continue

						if not uv_connected(current, n, uv_layer):
							continue

						dir_b = edge_direction_in_face(n, shared_edge)

						if dir_a != -dir_b:
							continue

						candidate = n
						candidate_edge = {
							edge.verts[0].index,
							edge.verts[1].index,
						}
						break

					if candidate:
						break

			# Strip already started.
			else:

				for edge in current.edges:

					edge_set = {
						edge.verts[0].index,
						edge.verts[1].index,
					}

					if edge_set != last_edge:
						continue

					shared_edge = (
						edge.verts[0].index,
						edge.verts[1].index,
					)

					dir_a = edge_direction_in_face(current, shared_edge)

					for n in edge.link_faces:

						if n not in remaining:
							continue

						if n.material_index != seed_material:
							continue

						if not uv_connected(current, n, uv_layer):
							continue

						dir_b = edge_direction_in_face(n, shared_edge)

						if dir_a != -dir_b:
							continue

						candidate = n
						break

					if candidate:
						break

			if candidate is None:
				break

			remaining.remove(candidate)
			strip.append(candidate)

			# Compute new strip edge.
			shared = {
				v.index
				for v in current.verts
				if v in candidate.verts
			}

			new_vert = next(
				v.index
				for v in candidate.verts
				if v.index not in shared
			)

			if last_edge is None:

				last_edge = shared

			else:

				last_edge = {
					new_vert,
					next(iter(last_edge)),
				}

		sorted_strips.append(strip)
						
			
	#for i in sorted_strips:
	#	print(i)
	
	triangle_strips = chains_to_triangle_strips(sorted_strips)

	#for strip in triangle_strips:
	#	print(strip)

	#strips = faces_to_triangle_strips(all_faces)
	#print(strips)

	#v0 v1 v2
	#v2 v1 v3
	#v2 v3 v4 --
	#v4 v3 v5
	#v4 v5 v6





	bpy.ops.object.mode_set(mode=previous_mode.replace("_MESH","").replace("_ARMATURE",""))
	return triangle_strips
	
def estimate_size(faces):
	 
	retCount = 3 #starts with three verts always
	for face in range(1,len(faces)): 
		should_separate = False

		curf = faces[face]
		v3 = get_vert_indices(curf)
		v2 = get_vert_indices(curf)
		if len(faces) > 3:
			history = []
			#v3 = get_vert_indices(curf) #V3 is already in order so it's not necessary to recompute it's value again
			v2 = get_vert_indices(faces[face-1])
			v1 = get_vert_indices(faces[face-2])
			v0 = get_vert_indices(faces[face-3])
			history.extend(v3)
			history.extend(v2)
			history.extend(v1)
			history.extend(v0)

			for idx in v3:
				if history.count(idx) > 3: #if on the past iterations the vertex index appeared more than 3 times, this means the faces have to be separated. This is easily debuggable because triangle stripping generate a "staircase" pattern that is easy to identify
					should_separate = True
					break
		
		fc0 = v3
		fc1 = get_vert_indices(faces[face-1])
		  		
		common = list(set(fc0) & set(fc1)) #now, compare the vert indices between the current iteration from the last one, and check which indexes have been mantained and which ones were removed

		if should_separate:
			retCount = retCount + 3
		else:
			if len(common) == 2:
				retCount = retCount + 1 #this means only one new vertex have to be created, because the face shares two other vertices. That's GOOD
			else:
				retCount = retCount + 3 #it was  either disconnected or not supported, which is NOT good for size...
					
	return calculate_estimation(retCount)
def estimate_size_interface(obj):
	#same stuff for estimate size, but for the interface
	for poly in obj.data.polygons:
		if len(poly.vertices) != 3:
			return -1
	face_indices = [tuple(poly.vertices) for poly in obj.data.polygons]
	retCount = 3

	for face in range(1, len(face_indices)):
		should_separate = False

		v3 = face_indices[face]

		if face >= 3:
			history = []
			history.extend(v3)
			history.extend(face_indices[face - 1])
			history.extend(face_indices[face - 2])
			history.extend(face_indices[face - 3])

			for idx in v3:
				if history.count(idx) > 3:
					should_separate = True
					break

		shared_count = len(set(v3) & set(face_indices[face - 1]))

		if should_separate:
			retCount += 3
		elif shared_count == 2:
			retCount += 1
		else:
			retCount += 3
	return calculate_estimation(retCount)
def estimate_complexity(obj, lookup):
	#print(lookup)
	mesh_size = len(obj.data.polygons)
	lookup_size = lookup
	if lookup_size >= mesh_size:
		lookup_size = mesh_size
	return round((mesh_size * pow(lookup_size,1.5)) / (2048.0)) #simple calculation based on.... uhhhhhh....the voices of my head? :3
def get_faces_that_connects(faces_mat): 

	#basically it's going to return a array of array, each array of the array is a index array, so it's [[0,1,2],[1,2,3]], etc. The way the strips are splitten is by checking the connection history, like on the size estimation function.
	#ngl im feeling lazy asf so i wont comment on this one lmao

	first = get_vert_indices(faces_mat[0])
	ret = []
	hist = [faces_mat[0]]
	cur = [first]



	

	for face in range(1,len(faces_mat)): 
		should_separate = False
		
		current_face = faces_mat[face]
		
		hist.append(current_face)
		v3 = get_vert_indices(current_face)
		if len(hist) > 3:
			history = []
			v3 = get_vert_indices(hist[len(hist)-1])
			v2 = get_vert_indices(hist[len(hist)-2])
			v1 = get_vert_indices(hist[len(hist)-3])
			v0 = get_vert_indices(hist[len(hist)-4])
			history.extend(v3)
			history.extend(v2)
			history.extend(v1)
			history.extend(v0)
			for idx in v3:
				if history.count(idx) > 3:
					should_separate = True
					break
		


		fc0 = v3
		fc1 = get_vert_indices(faces_mat[face-1])
		v3.sort()


			
		common = list(set(fc0) & set(fc1))
		common.sort()

		if should_separate:
			ret.append(cur)
			cur = [v3]
			hist = [current_face]
		else:
			
			if len(common) > 1 and len(common) != 3:
				cur.append(v3)
			else:
				ret.append(cur)
				cur = [v3]
				hist = [current_face]
	ret.append(cur)
	return ret


def staircase(tri_array): #the triangle array that needs sorting

	if len(tri_array) == 0:
		print("No enough faces")
		return
	if len(tri_array[0]) != 3:
		print("No enough vertices")
		return

	first_sequence = [tri_array[0][0], tri_array[0][1], tri_array[0][2]]

	if len(tri_array) > 1:
		def vert_index_count(c,j,curr):
			histc = []
			v1 = curr
			v2 = [tri_array[c+1][0], tri_array[c+1][1], tri_array[c+1][2]]
			v3 = [tri_array[c+2][0], tri_array[c+2][1], tri_array[c+2][2]]
			histc.extend(v1)
			histc.extend(v2)
			histc.extend(v3)

			return histc.count(v1[j])



		reference_sequence = [tri_array[1][0], tri_array[1][1], tri_array[1][2]] #second item on the array, ESSENTIAL to compute the staircase pattern.


		unique_vertices = [x for x in first_sequence if x not in reference_sequence] #computes which vertex of the first sequence doesn't repeat in the reference sequence
		repeated_vertices = [x for x in first_sequence if x in reference_sequence] #computes which vertices of the first sequence repeats in the reference sequence



		
		return_array = []
		
		if len(tri_array) == 2: #there's only two faces with three vertices in this model

			unique = [x for x in tri_array[0] if x not in tri_array[1]] #get the vertice that doesn't repeat between the first array and the second array.
			union = [x for x in tri_array[0] if x in tri_array[1]] #get the other vertices that DOES repeat
			union.sort() #then, sort them so the vertices that does repeat are in crescent order, i.e [1,0] becomes [0,1], this is essential for triangle stripping.
			
			frist_triangle = [unique[0],union[0],union[1]] #the first triangle of the list that will be returned.
			
			unique = [x for x in tri_array[1] if x not in tri_array[0]]#get the vertice that doesn't repeat between the second array and the first array.
			
			
			return_array.append(frist_triangle)
			return_array.append([union[0],union[1],unique[0]]) #the second triangle, that comes after. This should return a array as follows: [[v0,v1,v2], [v1,v2,v3]] while v is the vertex.
			return return_array
		
		
		
		if len(tri_array) > 2: #if the mesh has more than 2 triangles, it gets a bit more tricky...

			vt2 = vert_index_count(0,0,repeated_vertices) #get how many ocurrences the first repeated vertex had in the array.
			vt3 = vert_index_count(0,1,repeated_vertices) #get how many ocurrences the second repeated vertex had in the array.

			#basically, we're determining which index should go after the first vertex, which is the unique vertex. This is essential for connectivity.
			#we can't simply use a normal array sorting algorithm, because model vertices in this case can jump from index to index. i.e: [[0,1,2], [1,2,6], [2,6,14], ...] it's not sequential.


			first_triangle_sorted_indices = []
			if vt2 > vt3:
				#if vt2 is bigger than vt3, vt2 should be the last item to be put in the array.
				first_triangle_sorted_indices.append(repeated_vertices[1])
				first_triangle_sorted_indices.append(repeated_vertices[0])
			else:
				#otherwise, the opposite.
				first_triangle_sorted_indices.append(repeated_vertices[0])
				first_triangle_sorted_indices.append(repeated_vertices[1])
			#again, this is NOT a simple sorting algorithm, it's taking in consideration how the vert's indices are arranged in the future. The process of determining which vert index should come first is handled by "vert_index_count".


			frist_triangle = [unique_vertices[0], first_triangle_sorted_indices[0], first_triangle_sorted_indices[1]]
			return_array.append(frist_triangle) #first triangle of the returning array.

			
			for i in range(1,len(tri_array)): #skip the first iteration because the computing of the first face was already done.

				last_item = return_array[-1] #get the last item that was added in the computing array for the base calculation

				unique_array_ite = [x for x in tri_array[i] if x not in last_item] #compute again the unique element between two arrays. In this case, between the current array and the last array.
				
				return_array.append([last_item[1], last_item[2], unique_array_ite[0]]) #lastly, add them in order.
				#because we ordered the first triangle, the other triangles will always be in this order, which makes the rest a LOT easier. This is because the unique item is always the last item of the array, it makes the rest of the process a lot more manageable.
		return return_array
	else:
		return [first_sequence] #if the model has only 3 vertices, return the first sequence only, hard to happen but NOT impossible


def calculate_estimation(vert_count):
	return (vert_count * 16) + (vert_count * 4) + (vert_count * 4) + (vert_count * 8)
	#retCount * 16 is how many bytes a vertex definition occupy within the memory.
	#retCount * 4 is how many bytes a vertex UV occupy within the memory.
	#retCount * 4 is how many bytes a vertex color occupy within the memory.
	#retCount * 8 is how many bytes a vertex weight occupy within the memory.


#stuff for winding calculation

def face_chain_to_strip(chain):
	if not chain:
		return []

	if len(chain) == 1:
		return [v.index for v in chain[0].verts]

	# ----- Build first triangle -----

	f0 = chain[0]
	f1 = chain[1]

	shared = [v.index for v in f0.verts if v in f1.verts]

	if len(shared) != 2:
		return None

	unique = next(v.index for v in f0.verts if v.index not in shared)

	loops = [v.index for v in f0.verts]

	strip = None

	# Try both orientations.
	for i in range(3):
		a = loops[i]
		b = loops[(i + 1) % 3]

		if {a, b} != set(shared):
			continue

		for candidate in (
			[unique, a, b],
			[unique, b, a],
		):

			test = candidate[:]

			ok = True

			for face in chain[1:]:
				verts = {v.index for v in face.verts}

				last_edge = {test[-2], test[-1]}

				if not last_edge.issubset(verts):
					ok = False
					break

				new_vert = next((v for v in verts if v not in last_edge), None)

				if new_vert is None:
					ok = False
					break

				test.append(new_vert)

			if ok:
				strip = test
				break

		if strip:
			break

	return strip

def chains_to_triangle_strips(sorted_strips):
	strips = []

	for chain in sorted_strips:
		strip = face_chain_to_strip(chain)

		if strip is None:
			print("Couldn't stripify chain:")
			print([f.index for f in chain])
			continue

		# Validate every generated triangle.
		for i in range(2, len(strip)):
			if i & 1:
				tri = {strip[i-1], strip[i-2], strip[i]}
			else:
				tri = {strip[i-2], strip[i-1], strip[i]}

			face = None
			for f in chain:
				if {v.index for v in f.verts} == tri:
					face = f
					break

			if face is None:
				print("INVALID STRIP!")
				print(strip)
				return []

		strips.append(strip)

	return strips

def find_face(bm_faces, v0, v1, v2):
	for faces in bm_faces:
		matches = 0
		if faces.verts[0].index == v0 or faces.verts[0].index == v1 or faces.verts[0].index == v2:
			matches += 1
		if faces.verts[1].index == v0 or faces.verts[1].index == v1 or faces.verts[1].index == v2:
			matches += 1
		if faces.verts[2].index == v0 or faces.verts[2].index == v1 or faces.verts[2].index == v2:
			matches += 1
		if matches == 3:
			return faces
	return None