// Voice tab: text-to-speech (Kokoro) adds an audio clip to the gallery; speech-to-
// text (Whisper) transcribes an uploaded audio file. Both run locally on Metal.

import { useRef, useState } from "react";
import { synthesizeSpeech, transcribeAudio } from "../api";
import type { GalleryItem } from "../types";

export default function VoicePanel({ onGenerated }: { onGenerated: (item: GalleryItem) => void }) {
  const [text, setText] = useState("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const [ttsError, setTtsError] = useState<string | null>(null);

  const [sttBusy, setSttBusy] = useState(false);
  const [sttError, setSttError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const onSpeak = async () => {
    const t = text.trim();
    if (!t || ttsBusy) return;
    setTtsBusy(true);
    setTtsError(null);
    try {
      const result = await synthesizeSpeech(t);
      onGenerated({ kind: "audio", url: result.url, label: t.slice(0, 80), seconds: result.seconds });
    } catch (e) {
      setTtsError(e instanceof Error ? e.message : String(e));
    } finally {
      setTtsBusy(false);
    }
  };

  const onTranscribe = async (file: File) => {
    setSttBusy(true);
    setSttError(null);
    setTranscript(null);
    try {
      const result = await transcribeAudio(file);
      setTranscript(result.text);
    } catch (e) {
      setSttError(e instanceof Error ? e.message : String(e));
    } finally {
      setSttBusy(false);
      if (fileRef.current) fileRef.current.value = ""; // allow re-selecting the same file
    }
  };

  return (
    <section className="panel">
      <h2>Text to speech</h2>
      <textarea
        className="goal"
        rows={3}
        placeholder="Type something to read aloud…"
        value={text}
        disabled={ttsBusy}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="row">
        <button onClick={() => void onSpeak()} disabled={ttsBusy || !text.trim()}>
          {ttsBusy ? "Synthesizing…" : "Speak"}
        </button>
        <span className="hint">Kokoro · local · Metal</span>
      </div>
      {ttsError && <p className="error">{ttsError}</p>}

      <h3 id="stt-label">Speech to text</h3>
      <input
        type="file"
        accept="audio/*"
        aria-labelledby="stt-label"
        ref={fileRef}
        disabled={sttBusy}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void onTranscribe(file);
        }}
      />
      {sttBusy && <p className="muted">Transcribing…</p>}
      {sttError && <p className="error">{sttError}</p>}
      {transcript !== null && <blockquote className="transcript">{transcript || "(no speech detected)"}</blockquote>}
    </section>
  );
}
