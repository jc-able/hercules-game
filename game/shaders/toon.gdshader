// Cel shading for characters and props: flat albedo (texture x colour), 3 light bands, soft rim,
// tint / hit-flash uniforms and a petrify blend to stone. Pair with outline.gdshader as next_pass.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform bool use_texture = false;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform vec4 tint : source_color = vec4(1.0);
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform float petrify : hint_range(0.0, 1.0) = 0.0;
uniform vec4 stone_color : source_color = vec4(0.66, 0.67, 0.70, 1.0);   // cool grey: reads against tan skin
uniform float shade_dark : hint_range(0.0, 1.0) = 0.42;
uniform float shade_mid : hint_range(0.0, 1.0) = 0.74;
uniform float band_1 : hint_range(0.0, 1.0) = 0.12;
uniform float band_2 : hint_range(0.0, 1.0) = 0.50;
uniform float band_soft : hint_range(0.0, 0.2) = 0.025;
uniform vec4 rim_color : source_color = vec4(1.0, 0.94, 0.82, 1.0);
uniform float rim_strength : hint_range(0.0, 1.0) = 0.22;
uniform float alpha_cut : hint_range(0.0, 1.0) = 0.0;
// Near-camera fade (bosses the camera may sit inside): fully hidden closer than near_fade_hide metres, fully drawn from
// near_fade_full on, a 4x4 ordered dither in between. 0 / 0 = off. CharacterVisual.set_near_fade() sets both.
uniform float near_fade_hide = 0.0;
uniform float near_fade_full = 0.0;
const float NF_BAYER[16] = float[](0.03125, 0.53125, 0.15625, 0.65625, 0.78125, 0.28125, 0.90625, 0.40625,
	0.21875, 0.71875, 0.09375, 0.59375, 0.96875, 0.46875, 0.84375, 0.34375);

void fragment() {
	if (near_fade_full > 0.0) {
		// VERTEX is view space here: length() = distance to the camera (shadow passes see the light's, so shadows stay)
		float nf_t = clamp((length(VERTEX) - near_fade_hide) / max(near_fade_full - near_fade_hide, 0.001), 0.0, 1.0);
		ivec2 nf_p = ivec2(FRAGCOORD.xy) % ivec2(4);
		if (nf_t < 1.0 && nf_t <= NF_BAYER[nf_p.y * 4 + nf_p.x]) {
			discard;
		}
	}
	vec4 c = albedo_color;
	if (use_texture) {
		c *= texture(albedo_tex, UV);
	}
	if (alpha_cut > 0.0 && c.a < alpha_cut) {
		discard;
	}
	c.rgb *= tint.rgb;
	float lum = dot(c.rgb, vec3(0.30, 0.59, 0.11));
	vec3 stone = stone_color.rgb * (0.72 + 0.55 * lum);
	c.rgb = mix(c.rgb, stone, petrify);
	ALBEDO = c.rgb;
	float rim = pow(clamp(1.0 - dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	EMISSION = rim_color.rgb * rim * rim_strength * (0.35 + 0.65 * lum) * (1.0 - 0.6 * petrify) + flash_color.rgb * flash;
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	if (LIGHT_IS_DIRECTIONAL) {
		// the sun: banded (shade_dark floor, mid, lit); ATTENUATION carries its shadow
		ndl *= ATTENUATION;
		float b = mix(shade_dark, shade_mid, smoothstep(band_1 - band_soft, band_1 + band_soft, ndl));
		b = mix(b, 1.0, smoothstep(band_2 - band_soft, band_2 + band_soft, ndl));
		DIFFUSE_LIGHT += LIGHT_COLOR * b / PI;
	} else {
		// omni / spot (fire, braziers): no band floor, a soft wrap scaled by ATTENUATION, so the light fades to 0 at its
		// range and its Forward+ cluster tiles never show (the banded floor used to light every pixel of those tiles)
		DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * (0.25 + 0.75 * smoothstep(0.0, 0.6, ndl)) / PI;
	}
}
