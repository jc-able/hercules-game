# HERCULES boss fights — prompts (v2, behind-the-back boss fights)

Each fight is its own 15 s clip, made in two steps:

1. **Opening frame** — Nano Banana Pro, 16:9, 2K. References: Hercules sheet + that boss's sheet.
2. **Fight clip** — Seedance 2.5, mode `omni_reference`, 15 s, 16:9, sound on. The opening frame goes in as `start_image`; the same two sheets go in as `image_references`.

The opening frame is what locks the camera behind Hercules and the boss's size. The video prompt then tells Seedance to keep that camera for the whole clip.

---

## Step 1 — opening frame (image prompt)

A gameplay screenshot from an original cel-shaded 3D third-person action RPG boss fight. No HUD, no text.

Use the two reference sheets: image 1 is Hercules (use his BACK view), image 2 is [BOSS]. Match their colors, clothing and anatomy exactly, rendered as toon-shaded 3D game models with crisp outlines and hard-edged shadows.

Camera: a third-person chase camera close behind Hercules, at his head height, tilted slightly upward. Hercules stands in the lower center of the frame with his back to us, full body visible, about one third of the frame height: curly brown hair, sleeveless red tunic, belt, sandals, a short steel sword with a silver-grey blade in his right hand and a round bronze shield on his left arm, knees bent in a combat stance.

In front of him, facing him and the camera, towers [BOSS + SCALE + POSE].

Setting: [ARENA]. Wide-angle lens, deep perspective, strong sense of scale.

**Boss lines**

- **Cyclops** — the Four-Armed Cyclops: a giant five times Hercules's height, so tall his bald one-eyed head nearly touches the top edge of the frame. Hercules reaches only to his knee. The Cyclops raises a huge dark wooden club with his upper two arms, his lower two arms spread wide. *Arena:* a sunlit seaside quarry, a flat ring of packed earth, broken marble columns around the rim, the blue sea and sky beyond.
- **Medusa** — Medusa: a giant whose upright body rises four times Hercules's height, her head of green snake hair nearly touching the top edge of the frame. Hercules reaches only to the first thick coil of her single long green serpent tail, which trails far behind her across the floor. She wears gold armor, her arms spread, her eyes beginning to glow. *Arena:* a circular pale marble courtyard under daylight, ringed with petrified stone warrior statues standing around the rim.
- **Hydra** — the Lernaean Hydra: a colossal beast as big as a temple with nine heads on long necks, four legs and a long tail, black, violet and crimson. Each head is as large as Hercules and he reaches only to its ankle. Its nine heads fan out across the top of the frame, the center head rearing back with fire glowing in its throat. *Arena:* a broad black basalt shelf with glowing cracks, a sea of lava glowing beyond the rim, a dark orange volcanic sky.

---

## Step 2 — fight clip (video prompt)

### Shared block (opens every fight prompt)

Gameplay footage of a boss fight from HERCULES, an original cel-shaded 3D third-person action RPG. Animate from the first frame and keep its art style, lighting and character scale.

Reference images: the Hercules character sheet and the [BOSS] character sheet. Keep both characters on-model. Do not show the sheets. Hercules has a sword in his right hand and a round shield on his left arm. [BOSS ANATOMY LINE]

CAMERA: a third-person chase camera, exactly as in the first frame, for the entire clip: close behind Hercules's back at his head height, tilted slightly up at the boss. Hercules always stays in the lower center of the frame with his back to us, about one third of the frame height. The camera is attached to him like a game camera following the player: it never rises above him, never pulls far away, never shows his face or his side, and never cuts. One continuous take.

SCALE: [BOSS] stays a towering giant for the entire clip, [N] times Hercules's height, [its/his/her] head near the top of the frame. [SCALE LINE]

MOVEMENT: Hercules is locked on to [BOSS]. He strafes sideways in a circle around it, always facing it, and the camera orbits with Hercules, so [BOSS] stays in the center of the frame, turning to track him, while [BACKGROUND] slides sideways behind. Its attacks are slow and heavy with long clear windups.

[TIMED BEATS]

Sound: tense orchestral boss music, [FIGHT SOUNDS]. No dialogue. No HUD, no on-screen text, no slow motion.

### Cyclops — beats

- Anatomy: The Cyclops has one eye and four arms. Scale: five times Hercules's height; Hercules reaches only to his knee. Background: the quarry columns and the sea.

0:00-0:04 Hercules strafes left, circling the Cyclops. The Cyclops winds up and sweeps his giant club low across the ground. Hercules dodge-rolls sideways under the sweep and springs back to his feet.
0:04-0:09 He keeps circling. The Cyclops lifts the club high overhead with his upper two arms and its shadow falls across Hercules. At the last moment Hercules dodge-rolls sideways. The club smashes into the earth beside him, cracking the ground in a burst of dust, and sticks.
0:09-0:13 While the Cyclops strains to pull the club free, his forearm is down at ground level. Hercules runs in and slashes the forearm twice with his sword, the blade clearly visible. The Cyclops roars.
0:13-0:15 The Cyclops wrenches the club free. Hercules backs away and starts circling again.

Sounds: heavy impacts, roars, footsteps and sword hits.

### Medusa — beats

- Anatomy: Medusa has green snake hair, gold armor and one single long green serpent tail. Scale: her upright body four times Hercules's height; Hercules reaches only to the first coil of her tail. Background: the courtyard walls and the petrified warrior statues.

0:00-0:05 Hercules strafes right, circling Medusa. Her eyes light up and a narrow fan of pale light appears on the marble floor around his feet, marking where her gaze will strike. Hercules dodge-rolls sideways out of the fan just as a bright gaze beam fires from her eyes through the spot where he stood.
0:05-0:10 He springs up and keeps circling. Her eyes light up again and the fan of light sweeps onto him. Hercules plants his feet and raises his polished shield. The gaze beam hits the shield and reflects straight back into her face. She shrieks, recoils and lowers her head all the way down to the floor in front of him.
0:10-0:13 Hercules runs in and cuts the exposed side of her neck with his sword, the blade clearly visible.
0:13-0:15 Medusa rears back up to her full height, snakes hissing. Hercules backs away and starts circling again.

Sounds: hissing snakes, the hum and crack of the gaze beam, a shield ring, a sword hit.

### Hydra — beats

- Anatomy: The Hydra has nine heads on long necks, four legs and a long tail, black, violet and crimson. Scale: colossal, as big as a temple, its nine heads fanned across the top of the frame; each head is as large as Hercules and he reaches only to its ankle. Background: the lava sea and the rock walls.

0:00-0:05 The center head rears back and inhales, fire glowing in its throat. Hercules sprints sideways in a circle toward the Hydra's shoulder as the head sweeps a long stream of fire across the basalt just behind him, leaving a glowing scorched arc. All nine heads stay readable above the flames.
0:05-0:09 The flames stop and the smoking center head drops low to the ground in front of him. Hercules runs in and slashes the soft underside of its jaw with his sword, the blade clearly visible. The Hydra roars.
0:09-0:13 The Hydra lifts its near foreleg high above him. Hercules dodge-rolls sideways just before the giant foot stomps down beside him, cracking the basalt in a ring of dust.
0:13-0:15 Hercules springs up, backs away and starts circling again as the heads rear up.

Sounds: a deep inhale, roaring fire, a sword hit, a ground-shaking stomp.
