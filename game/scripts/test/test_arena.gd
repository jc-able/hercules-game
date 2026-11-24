extends ArenaBase
## Scene id "test": the core regression arena — a flat sand disc and the dummy boss. Keep it working.

func _init() -> void:
	arena_id = &"test"
	radius = Tuning.DUMMY["arena_radius"]
	victory_scene = &"title"


func build_environment() -> void:
	EnvKit.sky(self)
	EnvKit.sun(self, Vector3(-48, -30, 0))
	EnvKit.floor_disc(self, radius, Color(0.87, 0.76, 0.55))
	EnvKit.sea(self, 3000.0, -3.0)
	for i in 10:
		var a := TAU * float(i) / 10.0 + 0.2
		var h := 5.0 + 2.0 * float(i % 3)
		var pos := Vector3(sin(a) * (radius + 1.5), 0, cos(a) * (radius + 1.5))
		if i % 3 == 0:
			EnvKit.prop(self, "column_broken", pos, rad_to_deg(a))
		else:
			EnvKit.prop(self, "column", pos, rad_to_deg(a), h / 6.0)


func spawn_boss() -> BossBase:
	var b := DummyBoss.new()
	b.name = "DummyBoss"
	b.position = Vector3(0, 0.05, -4.0)     # returned unparented: ArenaBase sets arena + player, then adds it
	return b
