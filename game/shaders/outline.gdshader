// Inverted-hull ink outline (use as next_pass of the toon material). `width` is in metres; CharacterVisual
// sets it from the character's height so an 8 m boss and a 1.9 m hero both get a sensible line.
// px_width > 0 (real models and their props): the line is about px_width pixels wide at 720 p at any distance,
// clamped to [min_width, width] metres, so a 1.9 m hero seen from 4 m and a 14 m hydra seen from 25 m read alike.
shader_type spatial;
render_mode unshaded, cull_front, depth_draw_opaque, shadows_disabled;

uniform vec4 outline_color : source_color = vec4(0.07, 0.05, 0.05, 1.0);
uniform float width = 0.012;
uniform float px_width = 0.0;
uniform float min_width = 0.0;
uniform float petrify : hint_range(0.0, 1.0) = 0.0;
// Near-camera fade, same rule and names as toon.gdshader (0 / 0 = off).
uniform float near_fade_hide = 0.0;
uniform float near_fade_full = 0.0;
const float NF_BAYER[16] = float[](0.03125, 0.53125, 0.15625, 0.65625, 0.78125, 0.28125, 0.90625, 0.40625,
	0.21875, 0.71875, 0.09375, 0.59375, 0.96875, 0.46875, 0.84375, 0.34375);

void vertex() {
	float w = width;
	if (px_width > 0.0) {
		float d = max(-(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z, 0.05);
		float world_per_px = 2.0 * d / (PROJECTION_MATRIX[1][1] * 720.0);
		w = clamp(px_width * world_per_px, min_width, width);
	}
	VERTEX += normalize(NORMAL) * w;
}

void fragment() {
	if (near_fade_full > 0.0) {
		float nf_t = clamp((length(VERTEX) - near_fade_hide) / max(near_fade_full - near_fade_hide, 0.001), 0.0, 1.0);
		ivec2 nf_p = ivec2(FRAGCOORD.xy) % ivec2(4);
		if (nf_t < 1.0 && nf_t <= NF_BAYER[nf_p.y * 4 + nf_p.x]) {
			discard;
		}
	}
	ALBEDO = mix(outline_color.rgb, vec3(0.20, 0.19, 0.18), petrify);
}
