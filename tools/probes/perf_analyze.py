import json, sys, statistics as st

for path in sys.argv[1:]:
    d = json.load(open(path))
    fr = d["frames"]
    # skip the first 3 s of wall time (window open, first scene build)
    body = [f for f in fr if f[1] > 3000]
    ms = [f[2] for f in body]
    if not ms:
        print(path, "no frames"); continue
    srt = sorted(ms)
    p = lambda q: srt[min(len(srt) - 1, int(q * len(srt)))]
    over16 = sum(1 for m in ms if m > 16.7)
    over33 = sum(1 for m in ms if m > 33.4)
    worst = sorted(body, key=lambda f: -f[2])[:8]
    dc = [f[3] for f in body]; pr = [f[4] for f in body]; ob = [f[5] for f in body]
    phys = [f[6] for f in body]; proc = [f[7] for f in body]
    print("==", path.split("/")[-1], d.get("variant",""), "window", d["window"], "refresh", d["refresh"], "vsync", d["vsync"], d["adapter"])
    print("  frames %d  avg %.2f ms (%.0f fps)  median %.2f  p99 %.2f  p99.9 %.2f  worst %.1f ms  >16.7ms: %d  >33ms: %d"
          % (len(ms), st.mean(ms), 1000 / st.mean(ms), st.median(ms), p(0.99), p(0.999), srt[-1], over16, over33))
    print("  draw calls avg %.0f max %d | primitives avg %.0f max %d | objects avg %.0f max %d"
          % (st.mean(dc), max(dc), st.mean(pr), max(pr), st.mean(ob), max(ob)))
    print("  process avg %.2f max %.1f ms | physics avg %.2f max %.1f ms | vram %.0f MB static %.0f MB"
          % (st.mean(proc), max(proc), st.mean(phys), max(phys), d["video_mem"] / 1e6, d["static_mem"] / 1e6))
    if len(body[0])>8:
        gc=[f[8] for f in body]; gg=[f[9] for f in body]; sg=sorted(gg)
        print("  render cpu avg %.2f max %.1f ms | GPU avg %.2f p99 %.2f max %.1f ms" % (st.mean(gc), max(gc), st.mean(gg), sg[int(0.99*len(sg))], max(gg)))
    print("  worst frames (game t, wall s, ms):", ", ".join("t=%.2f/%.1fs %.0fms" % (f[0], f[1] / 1000, f[2]) for f in worst))
