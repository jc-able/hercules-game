// Flat stylized sea: two-tone body, gentle vertex waves, drifting foam bands and shoreline foam (depth based).
shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_disabled, specular_disabled, diffuse_lambert;

uniform vec4 deep_color : source_color = vec4(0.08, 0.36, 0.55, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.22, 0.66, 0.74, 1.0);
uniform vec4 foam_color : source_color = vec4(0.95, 0.98, 1.0, 1.0);
uniform float wave_height = 0.35;
uniform float wave_scale = 0.045;
uniform float foam_band_scale = 0.06;
uniform float shore_foam = 3.0;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;

varying vec3 world_pos;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float w = sin(world_pos.x * wave_scale + TIME * 0.8) * 0.5 + sin(world_pos.z * wave_scale * 1.3 + TIME * 0.6) * 0.5;
	VERTEX.y += w * wave_height;
}

void fragment() {
	vec2 p = world_pos.xz;
	float n = noise(p * 0.02 + TIME * 0.02);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	vec3 col = mix(deep_color.rgb, shallow_color.rgb, 0.25 + 0.35 * n + 0.3 * fres);
	// drifting foam bands (stylized, hard edged)
	float band = sin((p.x + p.y * 0.6) * foam_band_scale + n * 6.0 + TIME * 0.5);
	float foam = step(0.965, band) * step(0.45, noise(p * 0.05 - TIME * 0.05));
	// shoreline foam from scene depth
	float scene_depth = texture(depth_tex, SCREEN_UV).r;
	vec4 ndc = vec4(SCREEN_UV * 2.0 - 1.0, scene_depth, 1.0);
	vec4 view = INV_PROJECTION_MATRIX * ndc;
	view.xyz /= view.w;
	float diff = clamp(VERTEX.z - view.z, 0.0, 100.0);
	float shore = 1.0 - smoothstep(0.0, shore_foam, diff);
	float rings = step(0.5, fract(diff * 0.35 - TIME * 0.4)) * (1.0 - smoothstep(0.0, shore_foam * 2.5, diff));
	foam = max(foam, max(step(0.55, shore), rings * 0.8));
	ALBEDO = mix(col, foam_color.rgb, foam);
	ALPHA = 0.97;
	ROUGHNESS = 1.0;
}
