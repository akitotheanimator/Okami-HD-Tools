import bpy.utils.previews
import os

custom_icons = None


def get_icon(icon):
    return custom_icons[icon].icon_id
def register():
	global custom_icons

	custom_icons = bpy.utils.previews.new()

	icons_dir = os.path.join(os.path.dirname(__file__), "icons")

	custom_icons.load("github", os.path.join(icons_dir, "github.png"), 'IMAGE')
	custom_icons.load("okami", os.path.join(icons_dir, "okami.png"), 'IMAGE')
	
def unregister():
	global custom_icons

	bpy.utils.previews.remove(custom_icons)
	custom_icons = None