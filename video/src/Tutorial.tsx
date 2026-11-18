import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {clave, sans} from "./fonts";
import timeline from "./timeline.json";

const NAVY = "#1B2A4A";
const MARFIL = "#FFF8EE";
const CAMEL = "#C19A6B";
const TEJA = "#E5877E";
const SALVIA = "#86CFA5";

type Word = {t: string; start: number; end: number};
type Scene = {
  id: string;
  say: string;
  key: string;
  visual: string;
  start: number;
  end: number;
  words: Word[];
};

const SCENES = timeline.scenes as Scene[];

const norm = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "");

const Grid: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundImage:
        "linear-gradient(rgba(255,248,238,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(255,248,238,0.09) 1px, transparent 1px), linear-gradient(rgba(255,248,238,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,248,238,0.04) 1px, transparent 1px)",
      backgroundSize: "120px 120px, 120px 120px, 24px 24px, 24px 24px",
    }}
  />
);

const Palabra: React.FC<{text: string; on: boolean; local: number}> = ({text, on, local}) => {
  const p = interpolate(local, [0, 11], [0, 1], {
    easing: Easing.out(Easing.exp),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  if (on) {
    return (
      <div
        style={{
          display: "inline-block",
          background: MARFIL,
          color: NAVY,
          fontFamily: clave,
          fontStyle: "italic",
          fontWeight: 400,
          fontSize: text.length > 10 ? 72 : 108,
          lineHeight: 0.95,
          padding: "8px 28px 16px",
          opacity: p,
          filter: `blur(${(1 - p) * 16}px)`,
          transform: `translateY(${(1 - p) * 28}px)`,
          clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
        }}
      >
        {text}
      </div>
    );
  }
  return (
    <div
      style={{
        fontFamily: sans,
        fontWeight: 800,
        fontSize: 72,
        letterSpacing: -2,
        color: MARFIL,
        opacity: p,
        filter: `blur(${(1 - p) * 10}px)`,
        transform: `translateY(${(1 - p) * 22}px)`,
      }}
    >
      {text}
    </div>
  );
};

const Sub: React.FC<{scene: Scene; time: number}> = ({scene, time}) => {
  const dichos = scene.words.filter((w) => w.start <= time + 0.02);
  const linea = dichos.map((w) => w.t).join(" ");
  if (!linea) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: 120,
        right: 120,
        bottom: 78,
        textAlign: "center",
        fontFamily: sans,
        fontWeight: 600,
        fontSize: 40,
        color: "#FFFFFF",
        lineHeight: 1.15,
      }}
    >
      {linea}
    </div>
  );
};

const Ficha: React.FC<{title: string; body: string; on: boolean}> = ({title, body, on}) => (
  <div
    style={{
      flex: 1,
      background: on ? MARFIL : "#243656",
      color: on ? NAVY : MARFIL,
      borderRadius: 28,
      padding: "36px 32px",
      minHeight: 280,
    }}
  >
    <div style={{fontFamily: clave, fontStyle: "italic", fontSize: 64, lineHeight: 1}}>{title}</div>
    <div style={{marginTop: 18, fontFamily: sans, fontWeight: 600, fontSize: 32, lineHeight: 1.25}}>{body}</div>
  </div>
);

const Mock: React.FC<{scene: Scene; time: number}> = ({scene, time}) => {
  const local = time - scene.start;
  if (scene.visual === "two") {
    const red = scene.id !== "edita";
    return (
      <div style={{display: "flex", gap: 28, width: 1500, marginTop: 24}}>
        <Ficha title="RED" body="Aprende el estilo." on={red} />
        <Ficha title="Oficio" body="Edita con ese estilo." on={!red} />
      </div>
    );
  }
  if (scene.visual === "formats" || scene.visual === "ask") {
    const opciones = ["Reel", "YouTube", "Sin cara", "Motion", "Tutorial", "Anuncio", "Clase"];
    return (
      <div style={{display: "flex", flexWrap: "wrap", gap: 16, width: 1500, justifyContent: "center"}}>
        {opciones.map((op, i) => (
          <div
            key={op}
            style={{
              fontFamily: sans,
              fontWeight: 800,
              fontSize: 40,
              padding: "18px 28px",
              borderRadius: 18,
              background: i === Math.min(opciones.length - 1, Math.floor(local * 2)) ? MARFIL : "#243656",
              color: i === Math.min(opciones.length - 1, Math.floor(local * 2)) ? NAVY : MARFIL,
            }}
          >
            {op}
          </div>
        ))}
      </div>
    );
  }
  if (scene.visual === "safe") {
    return (
      <div style={{display: "flex", gap: 48, alignItems: "center"}}>
        <div style={{width: 280, height: 498, border: `3px solid ${MARFIL}`, borderRadius: 24, position: "relative"}}>
          <div style={{position: "absolute", left: 0, right: 0, top: 0, height: 70, background: TEJA, opacity: 0.85}} />
          <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 78, background: TEJA, opacity: 0.85}} />
          <div style={{position: "absolute", inset: "90px 24px auto", color: MARFIL, fontFamily: sans, fontWeight: 700, fontSize: 28}}>
            9:16
          </div>
        </div>
        <div style={{width: 640, height: 360, border: `3px solid ${MARFIL}`, borderRadius: 24, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: sans, fontWeight: 800, fontSize: 42, color: MARFIL}}>
          16:9
        </div>
      </div>
    );
  }
  if (scene.visual === "canvas") {
    const grupos = ["Gancho", "Subtítulo", "Cara"];
    return (
      <div style={{display: "flex", gap: 22}}>
        {grupos.map((g) => (
          <div key={g} style={{width: 360, background: "#243656", borderRadius: 24, padding: 22}}>
            <div style={{fontFamily: sans, fontWeight: 800, fontSize: 32, color: CAMEL}}>{g}</div>
            <div style={{marginTop: 16, height: 150, borderRadius: 16, background: MARFIL}} />
            <div style={{marginTop: 12, height: 90, borderRadius: 16, background: "rgba(255,248,238,0.35)"}} />
          </div>
        ))}
      </div>
    );
  }
  if (scene.visual === "measure") {
    const nums = [
      ["12", "cortes / min"],
      ["#1B2A4A", "color"],
      ["38%", "texto"],
    ];
    return (
      <div style={{display: "flex", gap: 28}}>
        {nums.map(([n, l]) => (
          <div key={l} style={{width: 380, background: MARFIL, color: NAVY, borderRadius: 24, padding: "28px 24px"}}>
            <div style={{fontFamily: sans, fontWeight: 800, fontSize: 72, letterSpacing: -2}}>{n}</div>
            <div style={{fontFamily: sans, fontWeight: 600, fontSize: 32}}>{l}</div>
          </div>
        ))}
      </div>
    );
  }
  if (scene.visual === "save" || scene.visual === "install") {
    return (
      <div style={{background: "#243656", borderRadius: 24, padding: "36px 40px", width: 1280}}>
        <div style={{fontFamily: sans, fontWeight: 700, fontSize: 40, color: SALVIA}}>.claude/skills/</div>
        <div style={{marginTop: 16, fontFamily: sans, fontWeight: 800, fontSize: 48}}>picassos-red</div>
        <div style={{marginTop: 8, fontFamily: sans, fontWeight: 800, fontSize: 48}}>oficio-de-edicion</div>
      </div>
    );
  }
  if (scene.visual === "layers") {
    const capas = ["Reglas", "Formato", "Estilo"];
    return (
      <div style={{display: "flex", flexDirection: "column", gap: 16, width: 900}}>
        {capas.map((c, i) => (
          <div key={c} style={{background: i === 2 ? MARFIL : "#243656", color: i === 2 ? NAVY : MARFIL, borderRadius: 20, padding: "22px 32px", fontFamily: sans, fontWeight: 800, fontSize: 48}}>
            {c}
          </div>
        ))}
      </div>
    );
  }
  if (scene.visual === "chat") {
    return (
      <div style={{width: 1280, background: "#243656", borderRadius: 28, padding: 36}}>
        <div style={{fontFamily: sans, fontWeight: 700, fontSize: 28, color: CAMEL}}>Prompt</div>
        <div style={{marginTop: 18, fontFamily: sans, fontWeight: 650, fontSize: 40, lineHeight: 1.25, color: MARFIL}}>
          Clona el repo. Copia las dos carpetas. Arranca con un video mío.
        </div>
      </div>
    );
  }
  return null;
};

const Frase: React.FC<{scene: Scene; time: number; fps: number}> = ({scene, time, fps}) => {
  const dichos = scene.words.filter((w) => w.start <= time + 0.04);
  return (
    <div style={{display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "center", gap: "10px 18px", maxWidth: 1680}}>
      {dichos.map((w, i) => {
        const on = norm(w.t).length > 2 && (norm(scene.key).includes(norm(w.t)) || norm(w.t).includes(norm(scene.key).split(" ")[0]));
        const local = Math.max(0, (time - w.start) * fps);
        if (on) return <Palabra key={`${w.t}-${i}`} text={w.t} on local={local} />;
        const p = interpolate(local, [0, 8], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
        return (
          <span key={`${w.t}-${i}`} style={{fontFamily: sans, fontWeight: 800, fontSize: 64, letterSpacing: -1, color: MARFIL, opacity: p, filter: `blur(${(1 - p) * 8}px)`}}>
            {w.t}
          </span>
        );
      })}
    </div>
  );
};

const Escena: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = scene.start + frame / fps;
  const muestraMock = !["word", "hero", "close"].includes(scene.visual);
  return (
    <AbsoluteFill>
      <Grid />
      <div style={{position: "absolute", top: 64, left: 72, right: 72, bottom: 150, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 36}}>
        {muestraMock ? <Mock scene={scene} time={time} /> : null}
        <Frase scene={scene} time={time} fps={fps} />
      </div>
    </AbsoluteFill>
  );
};

export const Tutorial: React.FC = () => {
  const {fps} = useVideoConfig();
  const total = Math.ceil(timeline.duration * fps);
  return (
    <AbsoluteFill style={{background: NAVY, fontFamily: sans}}>
      <Audio src={staticFile("voz.mp3")} />
      {SCENES.map((scene) => {
        const from = Math.round(scene.start * fps);
        const dur = Math.max(1, Math.round((scene.end - scene.start) * fps));
        return (
          <Sequence key={scene.id} from={from} durationInFrames={dur}>
            <Escena scene={scene} />
          </Sequence>
        );
      })}
      <div style={{position: "absolute", left: 80, right: 80, bottom: 36, height: 4, background: "rgba(255,248,238,0.15)"}}>
        <Bar total={total} />
      </div>
    </AbsoluteFill>
  );
};

const Bar: React.FC<{total: number}> = ({total}) => {
  const frame = useCurrentFrame();
  return <div style={{width: `${(frame / total) * 100}%`, height: "100%", background: CAMEL}} />;
};
