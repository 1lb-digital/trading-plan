"""Render one narration MP3 per <section data-audio> in index.html.

Voice: Kokoro af_sky (Sky) at speed 1.2. Skips prompt boxes, checklists, kickers and
source lines. Run from the repo root:  /usr/bin/python3 tools/narrate.py [section-id ...]
"""
import html, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR, VOICE, SPEED = 24000, "af_sky", 1.2
GAP_LINE, GAP_HEAD = 0.35, 0.8
FFMPEG = "/opt/homebrew/bin/ffmpeg"


def strip(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("·", ",")
    return re.sub(r"\s+", " ", s).strip()


def speakable(s):
    s = re.sub(r"\b([a-z0-9-]+)\.(com|ai|io|click|app|dev|org|net|so|markets)(/[\w./?=-]*)?", r"\1 dot \2", s)
    s = s.replace("CLAUDE.md", "Claude dot M D").replace(".env", "dot env").replace("x64", "x 64").replace("ARM64", "ARM 64")
    s = s.replace("strategy.yaml", "strategy dot yaml").replace("yfinance", "Y finance").replace("yt-dlp", "Y T D L P")
    s = re.sub(r"\b([Bb])acktest", r"\1ack test", s)
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"([+-])(\d+(?:\.\d+)?)R\b", lambda m: ("plus " if m.group(1) == "+" else "minus ") + m.group(2) + " R", s)
    s = re.sub(r"\b(\d+(?:\.\d+)?)R\b", r"\1 R", s)
    s = s.replace("&", " and ").replace("/", " or ")
    return s


def lines_for(sec):
    sec = re.sub(r'<div class="prompt">.*?</pre>\s*</div>', "", sec, flags=re.S)
    sec = re.sub(r'<ul class="check".*?</ul>', "", sec, flags=re.S)
    sec = re.sub(r'<(p|div|span)[^>]*class="(kicker|src|gate-lock|gate-top|opt-tag)[^"]*"[^>]*>.*?</\1>', "", sec, flags=re.S)
    sec = re.sub(r'<button.*?</button>', "", sec, flags=re.S)
    sec = re.sub(r'<code>[^<]*--[^<]*</code>', "the command on the page", sec)
    sec = re.sub(r'<thead>.*?</thead>', "", sec, flags=re.S)
    sec = re.sub(r'\s*\((?:[^()<]|<(?!/?p\b)[^>]*>)*?<a\b[^()]*?\)', "", sec)
    out = []
    for m in re.finditer(r"<(h2|h3|h4|p|li|tr)\b[^>]*>(.*?)</\1>", sec, flags=re.S):
        tag, body = m.group(1), m.group(2)
        if tag == "tr":
            cells = [strip(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", body, flags=re.S)]
            text = ". ".join(c for c in cells if c)
        else:
            if tag == "li" and re.search(r"<(ul|ol)\b", body):
                body = re.split(r"<(?:ul|ol)\b", body)[0]
            text = strip(body)
        if text:
            if not re.search(r"[.!?:]$", text):
                text += "."
            out.append((tag in ("h2", "h3", "h4"), speakable(text)))
    return out


def main(only):
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a")
    page = open(os.path.join(ROOT, "index.html")).read()
    os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
    for m in re.finditer(r'<section id="([^"]+)" data-audio>(.*?)</section>', page, flags=re.S):
        sid, body = m.group(1), m.group(2)
        if only and sid not in only:
            continue
        parts = []
        for is_head, text in lines_for(body):
            for r in pipe(text, voice=VOICE, speed=SPEED):
                a = r.audio.numpy() if hasattr(r.audio, "numpy") else r.audio
                parts.append(np.asarray(a, dtype=np.float32))
            parts.append(np.zeros(int(SR * (GAP_HEAD if is_head else GAP_LINE)), dtype=np.float32))
        a = np.concatenate(parts)
        pk = float(np.abs(a).max())
        if pk > 0.95:
            a = a * (0.95 / pk)
        out = os.path.join(ROOT, "audio", sid + ".mp3")
        wav = out + ".part.wav"
        sf.write(wav, a, SR)
        subprocess.run([FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", wav, "-ac", "1",
                        "-b:a", "64k", out], check=True)
        os.remove(wav)
        print(f"{sid}: {len(a) / SR / 60:.1f} min")


if __name__ == "__main__":
    if "--text" in sys.argv:
        page = open(os.path.join(ROOT, "index.html")).read()
        for m in re.finditer(r'<section id="([^"]+)" data-audio>(.*?)</section>', page, flags=re.S):
            print("=== " + m.group(1))
            for h, t in lines_for(m.group(2)):
                print(("# " if h else "") + t)
    else:
        main(set(a for a in sys.argv[1:] if not a.startswith("-")))
