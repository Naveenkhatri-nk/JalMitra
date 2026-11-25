"""
voice.py - Browser voice for JalMitra (no AI model, no server-side audio).

  * Speech to text: the browser's Web Speech API (SpeechRecognition), in a
    small custom Streamlit component (voice_component/index.html). The text
    is shown in an editable box before it is sent. Start/Stop buttons.
  * Text to speech: the browser's speechSynthesis, with Play, Pause/Resume
    and Stop buttons.

In Chrome and Edge the recognition itself is done by the browser vendor's
speech service, so listening needs an internet connection; everything else
in JalMitra works offline. Text chat always stays available.

Tested-ness: see language.VOICE. Nothing here has been tested with a real
microphone yet; the app labels every voice language as browser-dependent and
the ones without their own locale or voices as experimental.
"""

import html
import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import language as L

_COMPONENT_DIR = Path(__file__).resolve().parent / "voice_component"
_mic = components.declare_component("jalmitra_mic", path=str(_COMPONENT_DIR))

LABELS = {
    "en": {"start": "Start", "stop": "Stop", "listening": "Listening...", "unsupported":
           "Speech recognition is not available in this browser (use Chrome or Edge). Please type your question.",
           "denied": "Microphone permission was denied.", "nospeech": "No speech was heard.",
           "network": "The browser speech service could not be reached.",
           "nolang": "This browser does not support this speech language.", "nomic": "No microphone was found.",
           "done": "Done. Check the text below, edit it if needed, then press Ask.",
           "play": "Play", "pause": "Pause", "resume": "Resume", "stopspeak": "Stop",
           "novoice": "No voice for this language is installed in this browser; it may stay silent or use another voice."},
    "hi": {"start": "बोलना शुरू", "stop": "रोकें", "listening": "सुन रहा है...",
           "unsupported": "इस ब्राउज़र में आवाज़ पहचान उपलब्ध नहीं है (Chrome या Edge इस्तेमाल करें)। कृपया सवाल टाइप करें।",
           "denied": "माइक्रोफ़ोन की अनुमति नहीं मिली।", "nospeech": "कोई आवाज़ नहीं सुनाई दी।",
           "network": "ब्राउज़र की आवाज़ सेवा से संपर्क नहीं हुआ।", "nolang": "यह ब्राउज़र इस भाषा की आवाज़ पहचान नहीं करता।", "nomic": "कोई माइक्रोफ़ोन नहीं मिला।",
           "done": "हो गया। नीचे लिखा टेक्स्ट जाँचें, ज़रूरत हो तो बदलें, फिर पूछें दबाएँ।",
           "play": "सुनें", "pause": "रोकें", "resume": "फिर चलाएँ", "stopspeak": "बंद करें",
           "novoice": "इस ब्राउज़र में इस भाषा की आवाज़ नहीं है; यह चुप रह सकता है या दूसरी आवाज़ में पढ़ सकता है।"},
}


def _labels(lang):
    base = dict(LABELS["en"])
    base.update(LABELS.get("hi" if lang in ("hi", "raj", "hinglish") else lang, {}))
    return base


def voice_info(lang):
    v = L.VOICE.get(lang, L.VOICE["en"])
    return v["stt"], v["tts"], v["level"]


def speech_input(lang, key="jalmitra_mic"):
    """Show Start/Stop mic buttons. Returns {"text", "id", "locale"} once speech is recognised, else None."""
    stt, _, _ = voice_info(lang)
    return _mic(locale=stt, labels=_labels(lang), key=key, default=None)


def speakable(text):
    """Answer text without Markdown symbols, for reading aloud."""
    text = re.sub(r"[*_`#>|]", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def speak_controls(text, lang, key=0):
    """Play / Pause-Resume / Stop buttons that read the answer with the browser voice."""
    _, tts, _ = voice_info(lang)
    lab = _labels(lang)
    payload = json.dumps({"text": speakable(text), "lang": tts, "novoice": lab["novoice"],
                          "pause": lab["pause"], "resume": lab["resume"]}).replace("</", "<\\/")
    page = f"""
<div style="font-family:sans-serif;font-size:14px">
 <button id="p">▶ {html.escape(lab['play'])}</button>
 <button id="h">⏸ {html.escape(lab['pause'])}</button>
 <button id="s">⏹ {html.escape(lab['stopspeak'])}</button>
 <span id="m" style="color:#666;margin-left:6px"></span>
</div>
<script>
const d = {payload};
const synth = window.speechSynthesis;
const m = document.getElementById("m");
function pickVoice() {{
  const vs = synth ? synth.getVoices() : [];
  return vs.find(v => v.lang === d.lang) || vs.find(v => v.lang && v.lang.slice(0,2) === d.lang.slice(0,2));
}}
document.getElementById("p").onclick = () => {{
  if (!synth) {{ m.textContent = "speechSynthesis not available"; return; }}
  synth.cancel();
  const u = new SpeechSynthesisUtterance(d.text);
  u.lang = d.lang;
  const v = pickVoice();
  if (v) u.voice = v; else m.textContent = d.novoice + " (" + d.lang + ")";
  synth.speak(u);
}};
document.getElementById("h").onclick = (e) => {{
  if (!synth) return;
  if (synth.paused) {{ synth.resume(); e.target.textContent = "⏸ " + d.pause; }}
  else if (synth.speaking) {{ synth.pause(); e.target.textContent = "▶ " + d.resume; }}
}};
document.getElementById("s").onclick = () => {{ if (synth) synth.cancel(); }};
</script>"""
    if hasattr(st, "iframe"):
        st.iframe(page, height=48)            # Streamlit 1.5x+ (components.html is deprecated)
    else:
        components.html(page, height=48)
