// Ground warning decal: circle (mode 0), cone/arc (mode 1) or ring (mode 2) on a flat quad (UV 0..1 = -R..R).
// The fill grows with `progress` (0..1) over the warning time; a bright edge keeps it readable on sand and basalt.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform int mode = 0;
uniform vec4 color : source_color = vec4(0.95, 0.12, 0.08, 1.0);
uniform vec4 edge_color : source_color = vec4(1.0, 0.92, 0.75, 1.0);
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float half_angle = 0.5;   // radians (cone)
uniform float inner = 0.0;        // 0..1 inner radius fraction (ring)
uniform float edge = 0.025;       // edge width as a fraction of the radius
uniform float strike = 0.0;       // 1 at impact: flash

void fragment() {
	vec2 p = UV * 2.0 - 1.0;      // x right, y forward (+Z of the node)
	p.y = -p.y;
	float r = length(p);
	float inside = step(r, 1.0);
	float edge_m = smoothstep(1.0 - edge * 2.0, 1.0 - edge, r) * inside;
	float fill_r = progress;
	float a_ok = 1.0;
	float r0 = 0.0;
	if (mode == 1) {
		float ang = abs(atan(p.x, -p.y));
		a_ok = step(ang, half_angle);
		float side = smoothstep(half_angle - edge * 1.5 / max(r, 0.05), half_angle, ang) * a_ok * inside;
		edge_m = max(edge_m * a_ok, side);
	} else if (mode == 2) {
		r0 = inner;
		inside *= step(inner, r);
		float in_edge = (1.0 - smoothstep(inner, inner + edge, r)) * inside;
		edge_m = max(edge_m, in_edge);
		fill_r = mix(inner, 1.0, progress);
	}
	float body = inside * a_ok;
	float fill = body * step(r, fill_r) * step(r0, r);
	float a = body * 0.22 + fill * 0.38 + edge_m * 0.85 + strike * body * 0.5;
	vec3 c = mix(color.rgb, edge_color.rgb, max(edge_m * 0.7, strike));
	ALBEDO = c;
	ALPHA = clamp(a * color.a, 0.0, 1.0);
}
