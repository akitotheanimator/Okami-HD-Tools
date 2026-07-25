extends ColorRect


func _ready() -> void:
	var v:Viewport = get_viewport()
	v.files_dropped.connect(on_files_dropped)
func on_files_dropped(files:PackedStringArray):
	for f:String in files:
		var allow:bool = false
		var s:String = "*." + f.get_extension()
		for i:Array in DAT.supported_file_types:
			if i[0].to_lower() == s.to_lower() || s.to_lower() == "*.dbp":
				allow = true
				break
		if allow:
			if s != "*.dbp":
				DAT.load_data_package(f) #this should ouput the DAT assets.
			else: 
				var F:FileAccess = FileAccess.open(f,FileAccess.READ)
				if !F:
					DAT.LOG.ADD_LOG("Couldn't open file " + f + ".")
					return
				#reassemble dbp back into a encrypted DAT file.
				DAT.FLAG_INFO.resize(5)
				
				DAT.MANAGER.clear()
				#print(f.get_base_dir())
				var all_files:PackedStringArray = get_all_files(f.get_base_dir())
				var sort_array:Array = []
				sort_array.resize(all_files.size())
				for i:int in range(0, all_files.size()):
					var number:int = int(all_files[i].get_file().split('_')[1].split('.')[0])
					sort_array[i] = [all_files[i],number]
				sort_array.sort_custom(func(a,b) -> bool:
					return a[1] < b[1])
				
				var ALL_PATHS:PackedStringArray = []
				for i:int in range(0, sort_array.size()):
					if FileAccess.file_exists(sort_array[i][0]) && FileAccess.file_exists(sort_array[i][0] + ".i"):
						ALL_PATHS.append(sort_array[i][0])
						ALL_PATHS.append(sort_array[i][0] + ".i")
					
				DAT.dat_data_array.clear()
				DAT.dat_data_array.resize(roundi(ALL_PATHS.size()/2))
				for i:int in range(0, ALL_PATHS.size(),2):
					var index:int = roundi(i / 2)
					#print(ALL_PATHS[i])
					DAT.dat_data_array[index] = [ALL_PATHS[i].get_file().split('_')[0], FileAccess.get_file_as_bytes(ALL_PATHS[i+1]), FileAccess.get_file_as_bytes(ALL_PATHS[i])]
				F.seek(F.get_8() + 1)
				DAT.FLAG_INFO[0] = F.get_32()
				DAT.FLAG_INFO[1] = F.get_32()
				DAT.FLAG_INFO[2] = F.get_32()
				DAT.FLAG_INFO[3] = F.get_32()
				DAT.FLAG_INFO[4] = F.get_32()
				DAT.MANAGER.refresh()
				DAT.LOG.ADD_LOG("Package constructor loaded from path " + f + ".")
		else:
			if DAT.save_unic_dat:
				var SB:StreamPeerBuffer = StreamPeerBuffer.new()
				SB.data_array = FileAccess.get_file_as_bytes(f)
				if SB.data_array.size() % BlowfishECB.BLOCK_SIZE != 0:
					DAT.LOG.ADD_LOG("The given file cannot be decrypted. Block size does not match. Result: " + str(SB.data_array.size() % BlowfishECB.BLOCK_SIZE))
					return

				#this portion of the code's purpose is to check if the file is either encrypted or not
				var f2:FileAccess = FileAccess.open(f,FileAccess.READ)
				if !f2:
					DAT.LOG.ADD_LOG("Couldn't open file " + f + ".")
					return
				SB.seek(0)
				DAT.LOG.ADD_LOG("An attempt to decrypt the file will be made. However, if the file wasn't encrypted, the decryptor will only scramble your file's data. Make sure it is encrypted before running it through this program.")
				DAT.LOG.ADD_LOG("Trying file decryption...")
				await get_tree().create_timer(0.1).timeout
				var BF:BlowfishECB = BlowfishECB.new()
				SB.clear()
				SB.data_array = BF.decrypt_bytes(FileAccess.get_file_as_bytes(f))
				BF.free()
					
					
				if DAT.save_unic_dat:
					var FILE:FileAccess = FileAccess.open(f.replace("." + f.get_extension(),"_decrypted" + "." + f.get_extension()),FileAccess.WRITE)
					if FILE:
						FILE.store_buffer(SB.data_array)
						DAT.LOG.ADD_LOG("Decrypted file stored on " + FILE.get_path() +".")
#chatgpt helped me on this one lmao 🥀
func get_all_files(path:String, files:Array = []) -> PackedStringArray:
	var dir := DirAccess.open(path)
	
	if dir == null:
		push_error("Cannot open directory: " + path)
		return files
	dir.list_dir_begin()
	while true:
		var file_name := dir.get_next()
		if file_name == "":
			break
		# Skip hidden/system entries
		if file_name.begins_with("."):
			continue
		var full_path := path.path_join(file_name)
		if dir.current_is_dir():
			get_all_files(full_path, files)
		else:
			if "#IGNORE" not in full_path && full_path.get_extension() != "i":
				var vt:PackedStringArray = full_path.get_file().split('_') #check if the file type is correct
				if vt.size() == 2:
					var vt2:PackedStringArray = vt[1].split('.')
					if vt2.size() == 2:
						if vt2[0].is_valid_int():
							
							files.append(full_path)
	dir.list_dir_end()
	return files
