shader_type canvas_item;

uniform sampler2D tex;
uniform sampler2D noise;
uniform float threshold = 0.5;

void fragment() {
	vec4 color = texture(noise, UV);
	if (color[0] < threshold && color[1] < threshold && color[2] < threshold)
	{
		COLOR = texture(tex, UV);
	}
}