// Painted-looking gradient sky with soft cloud bands and a sun disc.
shader_type sky;

uniform vec3 top_color : source_color = vec3(0.24, 0.48, 0.82);
uniform vec3 horizon_color : source_color = vec3(0.86, 0.90, 0.92);
uniform vec3 bottom_color : source_color = vec3(0.30, 0.52, 0.66);
uniform vec3 cloud_color : source_color = vec3(1.0, 0.97, 0.92);
uniform vec3 cloud_shade : source_color = vec3(0.78, 0.80, 0.88);
uniform float cloud_amount : hint_range(0.0, 1.0) = 0.5;
uniform vec3 sun_color : source_color = vec3(1.0, 0.92, 0.70);
uniform float sun_size = 0.035;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }

void sky() {
	vec3 d = EYEDIR;
	float h = d.y;
	vec3 col = h > 0.0 ? mix(horizon_color, top_color, pow(clamp(h, 0.0, 1.0), 0.6)) : mix(horizon_color, bottom_color, clamp(-h * 3.0, 0.0, 1.0));
	if (h > 0.0) {
		vec2 uv = d.xz / (h + 0.18);
		float c = fbm(uv * vec2(0.9, 2.6) + vec2(TIME * 0.004, 0.0));
		float band = smoothstep(0.62 - cloud_amount * 0.3, 0.70 - cloud_amount * 0.3, c);
		float shade = smoothstep(0.55, 0.85, fbm(uv * vec2(0.9, 2.6) + vec2(0.07, 0.11)));
		vec3 cc = mix(cloud_shade, cloud_color, shade);
		col = mix(col, cc, band * smoothstep(0.0, 0.12, h));
	}
	if (LIGHT0_ENABLED) {
		float s = dot(d, LIGHT0_DIRECTION);
		col = mix(col, sun_color, smoothstep(1.0 - sun_size * 0.02, 1.0 - sun_size * 0.015, s));
		col += sun_color * pow(max(s, 0.0), 64.0) * 0.25;
	}
	COLOR = col;
}
