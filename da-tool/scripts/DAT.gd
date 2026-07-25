extends Node

@onready var LOG:Node = $"../app/log"
@onready var MANAGER:Node = $"../app/panel/panelscroll/panelcontainer"
var save_unic_dat:bool = true
var save_dat_cont:bool = true


var dat_data_array:Array = [] #this is slow but, ehh... DAT files are usually small so i don't think this will be a problem for now.

var supported_file_types:Array[PackedStringArray] = [["*.dat","Data container"], ["*.ddp","Texture Container"], ["*.bin","Unknown"], ["*.tbl","Data container"], ["*.idd","Data container"]]
var BASE_PATH:String = ""
var BASE_EXT:String = ""
var FLAG_INFO:PackedInt32Array = []

func _ready() -> void:
	var save:ConfigFile = ConfigFile.new()
	var err = save.load("user://user_config.cfg")
	if err == OK:
		save_unic_dat = save.get_value("default","save_unencrypted_dat_on_load",true)
		save_dat_cont = save.get_value("default","save_dat_contents_on_load",true)
	else:
		save.set_value("default","save_unencrypted_dat_on_load",save_unic_dat)
		save.set_value("default","save_dat_contents_on_load",save_dat_cont)
		save.save("user://user_config.cfg")
func save_config() -> void:
	var save:ConfigFile = ConfigFile.new()
	save.set_value("default","save_unencrypted_dat_on_load",save_unic_dat)
	save.set_value("default","save_dat_contents_on_load",save_dat_cont)
	save.save("user://user_config.cfg")


func get_project_path() -> String:
	return ProjectSettings.globalize_path("res://") if OS.has_feature("editor") else OS.get_executable_path().get_base_dir()
func load_data_package(PATH:String) -> void:
	LOG.ADD_LOG("Loading DAT " + PATH.get_file() + ".")
	dat_data_array.clear()
	MANAGER.clear()
	
	
	await get_tree().create_timer(0.1).timeout
	var SB:StreamPeerBuffer = StreamPeerBuffer.new()
	SB.data_array = FileAccess.get_file_as_bytes(PATH)
	

	#this portion of the code's purpose is to check if the file is either encrypted or not
	var f:FileAccess = FileAccess.open(PATH,FileAccess.READ)
	if !f:
		LOG.ADD_LOG("Couldn't open file " + PATH + ".")
		return
	SB.seek(0)
	if check_if_encrypted(SB):
		LOG.ADD_LOG("Encryption detected! Running Decryptor.")
		await get_tree().create_timer(0.1).timeout
		print("bro is encrypted")
		var BF:BlowfishECB = BlowfishECB.new()
		SB.clear()
		SB.data_array = BF.decrypt_bytes(FileAccess.get_file_as_bytes(PATH))
		#print(SB.data_array)
		BF.free()
		
		
		if save_unic_dat:
			var FILE:FileAccess = FileAccess.open(PATH.replace("." + PATH.get_extension(),"_decrypted" + "." + PATH.get_extension()),FileAccess.WRITE)
			if FILE:
				FILE.store_buffer(SB.data_array)
				LOG.ADD_LOG("Decrypted dat stored on " + FILE.get_path())
				
		
		SB.seek(0)
		if check_if_encrypted(SB): #if the file is still unreadable even after the decryption attempt, it's considered not a valid dat file.
			print("nani????")
			LOG.ADD_LOG("Couldn't open DAT " + PATH + ". It's not a valid file.")
			return
	SB.seek(0)
	load_data_package_from_memory(PATH,SB)
func check_if_encrypted(f:StreamPeerBuffer) -> bool: #false = no error, true = encrypted
	var regex:RegEx = RegEx.new() #this is going to be useful to validate strings
	regex.compile("^[A-Za-z0-9_]+$")
	var file_count:int = f.get_u32()
	if file_count * 4 > f.get_size(): #1 offset entry = 4 bytes
		return true  #the file count cannot exceed the file size, automatically assumes it's encrypted
	for i:int in range(file_count):
		var offset:int = f.get_u32()
		if offset >= f.get_size():
			return true #the offset cannot exceed the file size, automatically assumes it's encrypted
	for i:int in range(file_count):
		var file_type:String = (f.get_data(4) as PackedByteArray).get_string_from_ascii()
		if regex.search(file_type) != null: #valid character wasn't found
			return true #if the file name contains an illegal character
	
	
	
	return false
func load_data_package_from_memory(PATH:String,f:StreamPeerBuffer) -> void:
	print("LOADING DATA PACKAGE")
	f.seek(0)
	var file_count:int = f.get_u32() - 1 #purposefully remove ROF from the file, as it will be generated again when exporting the DAT
	dat_data_array.resize(file_count)
	FLAG_INFO.resize(5)
	
	var file_sdata:Array[Array] = [] #the offets NEEDS to be sorted because some offsets can be blank. I know that because ive been on the god hand modding community for enough time
	file_sdata.resize(file_count)
	var last_offset:int = 0
	for i:int in range(file_count):
		var offset:int = f.get_u32()
		if offset != 0:
			last_offset = offset
			file_sdata[i] = [offset,""]
		else:
			file_sdata[i] = [last_offset,""]
	var RESERVE_FINAL_FILE:int = f.get_32() #this is the ROF file we will be purposefully skipping
	for i:int in range(file_count):
		var data:Array = f.get_data(4)
		file_sdata[i][1] = data[1].get_string_from_ascii()
		if file_sdata[i][1] == "":
			file_sdata[i][1] = "UNKNWON_FORMAT"
		print(file_sdata[i][1])
	
	f.get_32()
	FLAG_INFO[0] = f.get_32() #the flags...
	FLAG_INFO[1] = f.get_32()
	FLAG_INFO[2] = f.get_32()
	FLAG_INFO[3] = f.get_32()
	FLAG_INFO[4] = f.get_32() #are now OVER WOHOOOO
	
	#for i:int in range(file_sdata.size() - 1, -1, -1): #remove invalid offsets and types
	#	if file_sdata[i][0] == 0 || file_sdata[i][1] == "":
	#		file_sdata.remove_at(i)

	file_sdata.sort_custom(func(a,b) -> bool:
		return a[0] < b[0])
	file_sdata.append([RESERVE_FINAL_FILE,""])
		
	BASE_PATH = PATH.get_base_dir() + "/" + PATH.get_file().replace("." + PATH.get_extension(), "")
	BASE_EXT = PATH.get_extension()
	var basePath:String = PATH.get_base_dir() + "/" + PATH.get_file().replace("." + PATH.get_extension(),"_extracted/")

		
	for i:int in range(0,file_sdata.size()-1):
		f.seek(file_sdata[i][0]-32)
		
		var HEADER:StreamPeerBuffer = StreamPeerBuffer.new()
		HEADER.data_array = f.get_data(32)[1]
		
		
		var SPB:StreamPeerBuffer = StreamPeerBuffer.new()
		if file_sdata[i][1] != "UNKNWON_FORMAT":
			SPB.data_array = f.get_data(file_sdata[i + 1][0] - file_sdata[i][0] - 32)[1]
		else:
			SPB.data_array = f.get_data(0)[1]
		dat_data_array[i] = [file_sdata[i][1],HEADER.data_array,SPB.data_array]
			
			
		#print(file_sdata[i])
	LOG.ADD_LOG("Finished loading DAT " + PATH.get_file() + ".")
	if save_dat_cont:
		export_all()
		LOG.ADD_LOG("DAT contents extracted to path " + basePath + ".")
	MANAGER.refresh()

func export_all():
	var all:PackedInt32Array = []
	all.resize(dat_data_array.size())
	for i:int in range(0,dat_data_array.size()):
		all[i] = i
	export(all)
	
	
var TEMP_PATH:String = ""
func export(selected:PackedInt32Array):
	print("EXPORTING DATA PACKAGE")
	var basepath:String = BASE_PATH + "_extracted/"
	TEMP_PATH = basepath
	if dat_data_array.size() != 0:
		for i:int in selected:
			#print(dat_data_array[i][0])
			var part_path:String = basepath + dat_data_array[i][0] + "/"
			var clpath:String = part_path + dat_data_array[i][0] + "_" + str(i)
			var fpath:String = clpath + "." + dat_data_array[i][0].to_lower()
			var hpath:String = fpath + ".i"
			DirAccess.make_dir_recursive_absolute(part_path)
			#print(fpath, "    ", hpath)
			var F:FileAccess = FileAccess.open(hpath,FileAccess.WRITE)
			if F:
				F.store_buffer(dat_data_array[i][1])
			F.close()
			F = FileAccess.open(fpath,FileAccess.WRITE)
			if F:
				F.store_buffer(dat_data_array[i][2])
			F.close()
	var f:FileAccess = FileAccess.open(basepath + "Body.dbp",FileAccess.WRITE)
	if f:
		f.store_8(BASE_EXT.length())
		f.store_buffer(BASE_EXT.to_ascii_buffer())
		f.store_32(FLAG_INFO[0])
		f.store_32(FLAG_INFO[1])
		f.store_32(FLAG_INFO[2])
		f.store_32(FLAG_INFO[3])
		f.store_32(FLAG_INFO[4])
func replace_content(index:int, file:String) -> void:
	dat_data_array[index][2] = FileAccess.get_file_as_bytes(file)
	
func save_file(path:String,encrypted:bool) -> void:
	print("SAVING DATA PACKAGE")
	var f:StreamPeerBuffer = StreamPeerBuffer.new()
	if f:
		var align_4:Callable = func():
			while f.get_position() % 4 != 0:
				f.put_8(0)
		var align_8:Callable = func():
			while f.get_position() % 8 != 0:
				f.put_8(0)
		var align_32:Callable = func():
			while f.get_position() % 32 != 0:
				f.put_8(0)
		var ARRAY:PackedInt32Array = []
		
		
		f.put_32(dat_data_array.size()+1)
		for i:Array in dat_data_array:
			f.put_32(0)
			
		var ROF_OFFSET:int = f.get_position()
		f.put_32(0)
		
		#print(dat_data_array)
		for i:Array in dat_data_array:
			#print(i[0])
			print(i[0])
			if i[0] == "UNKNWON_FORMAT":
				f.put_32(0)
			else:
				f.put_data(i[0].to_ascii_buffer())
			align_4.call()
		f.put_32(4607826)
		
		
		
		
		#align_32.call()
		f.put_32(FLAG_INFO[0]) #oh no.... FLAGS!!!!!
		f.put_32(FLAG_INFO[1]) #oh no.... FLAGS!!!!!
		f.put_32(FLAG_INFO[2]) #oh no.... FLAGS!!!!!
		f.put_32(FLAG_INFO[3]) #oh no.... FLAGS!!!!!
		f.put_32(FLAG_INFO[4]) #oh no.... FLAGS!!!!!
		#align_8.call()
		
		for i:Array in dat_data_array:
			f.put_data(i[1])
			ARRAY.append(f.get_position())
			f.put_data(i[2])
		
		#align_32.call()
		
		#write ROF
		f.put_u64(0)
		f.put_u64(8029484318139502418)
		f.put_u64(29542)
		f.put_u64(0)
		var ROF_OFFSET_AF:int = f.get_position()
		f.put_u64(3762286100157977938)
		for i:int in range(0,dat_data_array.size()):
			f.put_64(ARRAY[i])
		f.put_64(ROF_OFFSET_AF)
		align_32.call()
		
		f.seek(ROF_OFFSET)
		f.put_32(ROF_OFFSET_AF)
		
		
		
		
		for i:int in range(0,dat_data_array.size()):
			f.seek(4 + (i * 4))
			f.put_32(ARRAY[i])
			pass
		
		
		
	if !encrypted:
		var F:FileAccess = FileAccess.open(path,FileAccess.WRITE)
		if F:
			F.store_buffer(f.data_array)
	else:
		var DATA:StreamPeerBuffer = StreamPeerBuffer.new()
		var BF:BlowfishECB = BlowfishECB.new()
		DATA.data_array = BF.encrypt_bytes(f.data_array)
		
		var F:FileAccess = FileAccess.open(path,FileAccess.WRITE)
		if F:
			F.store_buffer(DATA.data_array)
	
