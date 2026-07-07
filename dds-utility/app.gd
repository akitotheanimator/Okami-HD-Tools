extends Control

@onready var sha:ShaderMaterial = $ColorRect.material
func _ready() -> void:
	var v:Viewport = get_viewport()
	v.files_dropped.connect(on_files_dropped)
	sha.set_shader_parameter("threshold", 0)
func on_files_dropped(files:PackedStringArray):
	for f:String in files:
		if f.get_extension() == "png":
			sha.set_shader_parameter("threshold", 0)
			whatever_to_dds(f, f + "_.dds")
		else:
			sha.set_shader_parameter("threshold", 0)
			dds_to_png(f, f + "_.png")
			
func dds_to_png(dds_path:String, png_path:String) -> void:
	var img:Image = Image.new()
	var err = img.load_dds_from_buffer(FileAccess.get_file_as_bytes(dds_path))
	if err != OK:
		return
	var tex := ImageTexture.create_from_image(img)
	sha.set_shader_parameter("tex", tex)
	var IMG2:Image = tex.get_image()
	IMG2.save_png(png_path)
	
	
func whatever_to_dds(png_path:String, dds_path:String) -> void:
	var img:Image = Image.load_from_file(png_path)

	if img == null:
		push_error("Failed to load image")
		return

	# Optional: generate mipmaps
	img.generate_mipmaps()

	# Compress image
	img.compress(
		Image.COMPRESS_BPTC,
		Image.COMPRESS_SOURCE_GENERIC,
		#mage.ALPHA_BLEND
	)

	# Create texture
	var tex := ImageTexture.create_from_image(img)
	sha.set_shader_parameter("tex", tex)

	var IMG2:Image = tex.get_image()
	# Save as DDS
	IMG2.save_dds(dds_path)
func _process(delta: float) -> void:
	sha.set_shader_parameter("threshold", lerpf(sha.get_shader_parameter("threshold"),1,delta*1.5))
