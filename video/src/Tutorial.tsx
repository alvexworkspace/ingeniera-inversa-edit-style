import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {sans, serif} from "./fonts";
import {BLUE, DURATION, LINE, MUTED, NAVY, NAVY_CARD, S, TEXT} from "./theme";

const pad = 96;

const rise = (frame: number, fps: number, delay = 0) => {
  const s = spring({frame: frame - delay, fps, config: {damping: 18, mass: 0.7}});
  return {
    opacity: interpolate(frame - delay, [0, 10], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}),
    transform: `translateY(${interpolate(s, [0, 1], [36, 0])}px)`,
  };
};

const Chrome: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const progress = frame / (DURATION - 1);
  return (
    <AbsoluteFill style={{background: NAVY, fontFamily: sans, color: TEXT}}>
      <div
        style={{
          position: "absolute",
          width: 720,
          height: 720,
          right: -180,
          top: -220,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(46,112,240,0.28) 0%, rgba(46,112,240,0) 68%)",
          transform: `translate(${Math.sin(frame / 40) * 18}px, ${Math.cos(frame / 50) * 12}px)`,
        }}
      />
      <div style={{position: "absolute", top: 48, left: pad, fontWeight: 800, fontSize: 28, letterSpacing: -0.4}}>
        Picasso's RED
      </div>
      <AbsoluteFill style={{padding: `${pad + 36}px ${pad}px ${pad}px`}}>{children}</AbsoluteFill>
      <div style={{position: "absolute", left: pad, right: pad, bottom: 42, height: 4, background: LINE, borderRadius: 4}}>
        <div style={{width: `${progress * 100}%`, height: "100%", background: BLUE, borderRadius: 4}} />
      </div>
    </AbsoluteFill>
  );
};

const Open: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Chrome>
      <div style={{...rise(frame, fps), marginTop: 120}}>
        <div style={{fontSize: 34, fontWeight: 600, color: MUTED}}>Picasso's RED</div>
        <div style={{fontSize: 28, fontWeight: 600, color: BLUE, marginTop: 8}}>Reverse Engineer Designs</div>
      </div>
      <h1 style={{...rise(frame, fps, 8), margin: "28px 0 0", fontSize: 108, lineHeight: 0.98, letterSpacing: -3, fontWeight: 800, maxWidth: 1400}}>
        Destila un <span style={{fontFamily: serif, fontStyle: "italic", fontWeight: 800}}>estilo</span> de edición
      </h1>
      <div style={{...rise(frame, fps, 16), marginTop: 36, fontSize: 40, fontWeight: 700}}>Es gratis.</div>
    </Chrome>
  );
};

const What: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lines = [
    "Dos piezas. Un paquete.",
    "RED aprende el estilo.",
    "El oficio edita con ese estilo.",
    "Si no hay estilo, no inventa uno. Te manda a RED.",
  ];
  return (
    <Chrome>
      <div style={{marginTop: 80, display: "flex", flexDirection: "column", gap: 28}}>
        {lines.map((line, i) => (
          <div key={line} style={{...rise(frame, fps, i * 10), fontSize: i === 0 ? 72 : 48, fontWeight: 800, letterSpacing: -1.2, color: i === 0 ? TEXT : MUTED}}>
            {line}
          </div>
        ))}
      </div>
    </Chrome>
  );
};

const Pieces: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cards = [
    {title: "Picasso's RED", body: "Mide las referencias y desarma el estilo. Lo que se copia es la lógica, no la identidad de otra persona."},
    {title: "Oficio de edición", body: "Reglas, formato y un solo estilo. Si el estilo no está, esta pieza no sigue."},
  ];
  return (
    <Chrome>
      <div style={{...rise(frame, fps), fontSize: 64, fontWeight: 800, letterSpacing: -1.5}}>Las dos piezas</div>
      <div style={{display: "flex", gap: 28, marginTop: 48}}>
        {cards.map((card, i) => (
          <div key={card.title} style={{...rise(frame, fps, 8 + i * 8), flex: 1, background: NAVY_CARD, border: `1px solid ${LINE}`, borderRadius: 20, padding: 40}}>
            <div style={{fontSize: 42, fontWeight: 800, letterSpacing: -0.8}}>{card.title}</div>
            <div style={{marginTop: 18, fontSize: 32, lineHeight: 1.35, fontWeight: 600, color: MUTED}}>{card.body}</div>
          </div>
        ))}
      </div>
    </Chrome>
  );
};

const STEPS = [
  {n: "01", t: "Formato", d: "Siempre se pregunta. No se adivina. De ahí salen el tamaño y la zona segura."},
  {n: "02", t: "Lienzo", d: "Figma, Wonder, Paper, Excalidraw o el que ya uses. Sin lienzo no hay síntesis."},
  {n: "03", t: "Ingeniería inversa", d: "Se mide. Lo que no se puede calcular se dice. No se inventa un número."},
  {n: "04", t: "Estilo aprobado", d: "Lo que marcas se guarda en la carpeta de estilos del oficio."},
  {n: "05", t: "El oficio edita", d: "El siguiente video sale con ese estilo."},
];

const Flow: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const intro = 20;
  const each = Math.floor((S.flow - intro) / STEPS.length);
  const active = Math.min(STEPS.length - 1, Math.max(0, Math.floor((frame - intro) / each)));
  return (
    <Chrome>
      <div style={{...rise(frame, fps), fontSize: 28, fontWeight: 700, color: BLUE}}>El flujo completo</div>
      <div style={{marginTop: 28, display: "flex", flexDirection: "column", gap: 14}}>
        {STEPS.map((step, i) => {
          const on = i === active;
          return (
            <div
              key={step.n}
              style={{
                display: "flex",
                gap: 28,
                alignItems: "center",
                padding: "18px 28px",
                borderRadius: 16,
                background: on ? "rgba(46,112,240,0.16)" : "transparent",
                border: `1px solid ${on ? BLUE : "transparent"}`,
                opacity: frame < intro ? 0.35 : i <= active ? 1 : 0.35,
              }}
            >
              <div style={{fontSize: 40, fontWeight: 800, color: BLUE, width: 84}}>{step.n}</div>
              <div>
                <div style={{fontSize: 40, fontWeight: 800, letterSpacing: -0.6}}>{step.t}</div>
                {on ? <div style={{marginTop: 6, fontSize: 30, fontWeight: 600, color: MUTED, maxWidth: 1400}}>{step.d}</div> : null}
              </div>
            </div>
          );
        })}
      </div>
    </Chrome>
  );
};

const FORMATS = [
  ["Reel hablado", "1080 × 1920"],
  ["Sin cara", "Voz, stock o imagen"],
  ["Motion", "Una frase, una escena"],
  ["Tutorial", "Pantalla limpia"],
  ["Anuncio", "Se mide la plataforma"],
  ["Video largo", "Clase o YouTube"],
];

const Formats: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Chrome>
      <div style={{...rise(frame, fps), fontSize: 64, fontWeight: 800, letterSpacing: -1.4}}>Seis formatos</div>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 22, marginTop: 40}}>
        {FORMATS.map(([title, body], i) => (
          <div key={title} style={{...rise(frame, fps, 6 + i * 4), background: NAVY_CARD, border: `1px solid ${LINE}`, borderRadius: 18, padding: "32px 28px"}}>
            <div style={{fontSize: 36, fontWeight: 800}}>{title}</div>
            <div style={{marginTop: 10, fontSize: 26, fontWeight: 600, color: MUTED}}>{body}</div>
          </div>
        ))}
      </div>
    </Chrome>
  );
};

const LINES = [
  "Copia dos carpetas a .claude/skills/",
  "picassos-red",
  "oficio-de-edicion",
  "pip install -r requirements.txt",
  "Hacen falta ffmpeg y ffprobe",
];

const Install: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Chrome>
      <div style={{...rise(frame, fps), fontSize: 64, fontWeight: 800, letterSpacing: -1.4}}>Instalación</div>
      <div style={{marginTop: 36, background: "#0A1A3A", border: `1px solid ${LINE}`, borderRadius: 18, padding: "36px 40px", display: "flex", flexDirection: "column", gap: 18}}>
        {LINES.map((line, i) => (
          <div key={line} style={{...rise(frame, fps, 8 + i * 6), fontFamily: i === 0 || i === 4 ? sans : "ui-monospace, monospace", fontSize: i === 0 || i === 4 ? 36 : 34, fontWeight: 650, color: i === 1 || i === 2 ? BLUE : TEXT}}>
            {line}
          </div>
        ))}
      </div>
    </Chrome>
  );
};

const Prompt: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lines = [
    "Pégalo en tu IA",
    "Clona el repositorio",
    "Copia las dos carpetas de skills",
    "Arranca RED con un video de referencia",
    "El formato se pregunta. El lienzo es obligatorio.",
  ];
  return (
    <Chrome>
      <div style={{...rise(frame, fps), fontSize: 64, fontWeight: 800, letterSpacing: -1.4}}>El prompt para tu IA</div>
      <div style={{marginTop: 40, display: "flex", flexDirection: "column", gap: 22}}>
        {lines.map((line, i) => (
          <div key={line} style={{...rise(frame, fps, 6 + i * 5), fontSize: i === 0 ? 48 : 40, fontWeight: 700, color: i === 0 ? TEXT : MUTED}}>
            {line}
          </div>
        ))}
      </div>
    </Chrome>
  );
};

const End: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Chrome>
      <div style={{marginTop: 90, ...rise(frame, fps)}}>
        <div style={{fontSize: 72, fontWeight: 800, letterSpacing: -1.6}}>Primero se entiende.</div>
        <div style={{fontSize: 72, fontWeight: 800, letterSpacing: -1.6}}>Después se edita.</div>
      </div>
      <div style={{...rise(frame, fps, 12), marginTop: 40, fontSize: 32, fontWeight: 600, color: MUTED, maxWidth: 1200}}>
        El método se inspira en Joseph y en su video sobre el estilo de edición de Arthur Brooks.
      </div>
      <div style={{...rise(frame, fps, 18), marginTop: 28, fontSize: 30, fontWeight: 700, color: BLUE}}>
        github.com/alvexworkspace/ingeniera-inversa-edit-style
      </div>
    </Chrome>
  );
};

export const Tutorial: React.FC = () => {
  let from = 0;
  const blocks: Array<[number, React.FC]> = [
    [S.open, Open],
    [S.what, What],
    [S.pieces, Pieces],
    [S.flow, Flow],
    [S.formats, Formats],
    [S.install, Install],
    [S.prompt, Prompt],
    [S.end, End],
  ];
  return (
    <AbsoluteFill style={{background: NAVY}}>
      {blocks.map(([dur, Comp], i) => {
        const start = from;
        from += dur;
        return (
          <Sequence key={i} from={start} durationInFrames={dur}>
            <Comp />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
