import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
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
const PANEL = "#243656";
const INK = "#111A2E";

type Word = {t: string; start: number; end: number};
type Scene = {id: string; visual: string; key: string; start: number; end: number; words: Word[]};

const SCENES = timeline.scenes as Scene[];
const WORDS = timeline.words as Word[];

const norm = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "");

const cuando = (partes: string[], desde = 0): number | null => {
  const meta = partes.map(norm);
  const textos = WORDS.map((w) => norm(w.t));
  for (let i = 0; i <= textos.length - meta.length; i++) {
    if (WORDS[i].start < desde) continue;
    if (meta.every((p, k) => textos[i + k] === p)) return WORDS[i].start;
  }
  return null;
};

const FOCO: Record<string, {x: number; y: number; z: number}> = {
  abre: {x: 980, y: 490, z: 1.04},
  inversa: {x: 860, y: 470, z: 1.14},
  piezas: {x: 1280, y: 490, z: 1.12},
  formato: {x: 2720, y: 430, z: 1.08},
  zona: {x: 2720, y: 560, z: 1.1},
  lienzo: {x: 4560, y: 500, z: 1.05},
  mide: {x: 4560, y: 1540, z: 1.07},
  guarda: {x: 2740, y: 1520, z: 1.04},
  oficio: {x: 2740, y: 1540, z: 1.06},
  arbol: {x: 980, y: 1500, z: 1.02},
  prompt: {x: 1080, y: 1520, z: 1.02},
  cierra: {x: 2740, y: 1520, z: 1.04},
};

const ease = Easing.out(Easing.exp);

const llegada = (time: number, desde: number | null) => {
  if (desde === null || time < desde) {
    return {opacity: 0, filter: "blur(16px)", transform: "translateY(22px)"};
  }
  const p = interpolate((time - desde) * 30, [0, 11], [0, 1], {
    easing: ease,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return {opacity: p, filter: `blur(${(1 - p) * 16}px)`, transform: `translateY(${(1 - p) * 18}px)`};
};

const Grid: React.FC = () => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      backgroundImage:
        "linear-gradient(rgba(255,248,238,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(255,248,238,0.09) 1px, transparent 1px), linear-gradient(rgba(255,248,238,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,248,238,0.04) 1px, transparent 1px)",
      backgroundSize: "120px 120px, 120px 120px, 24px 24px, 24px 24px",
    }}
  />
);

const MesaClip: React.FC<{time: number}> = ({time}) => {
  const mide = cuando(["ingeniería", "inversa"]);
  const sinCara = cuando(["sin", "cara"]);
  const gratis = cuando(["Es", "gratis"]);
  const aprende = cuando(["RED", "aprende"]);
  const edita = cuando(["oficio", "edita"]);
  const noInventa = cuando(["no", "inventa"]);
  const scan = mide ? interpolate(time, [mide, mide + 2.4], [0, 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 0;
  return (
    <>
      <div style={{position: "absolute", left: 140, top: 150, width: 980, height: 640, background: PANEL, borderRadius: 28, padding: 28, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
        <div style={{display: "flex", justifyContent: "space-between", fontFamily: sans, fontWeight: 700, fontSize: 36, color: MARFIL}}>
          <span>Referencia</span>
          <span style={{color: CAMEL}}>{sinCara && time >= sinCara ? "sin cara" : "16:9"}</span>
        </div>
        <div style={{marginTop: 18, height: 500, borderRadius: 18, background: INK, position: "relative", overflow: "hidden"}}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{position: "absolute", left: 36, right: 36, top: 36 + i * 150, height: 120, borderRadius: 16, background: i === 1 ? MARFIL : "rgba(255,248,238,0.16)"}} />
          ))}
          <div style={{position: "absolute", left: 18, top: 18, width: 36, height: 36, borderLeft: `4px solid ${CAMEL}`, borderTop: `4px solid ${CAMEL}`}} />
          <div style={{position: "absolute", right: 18, top: 18, width: 36, height: 36, borderRight: `4px solid ${CAMEL}`, borderTop: `4px solid ${CAMEL}`}} />
          <div style={{position: "absolute", left: 18, bottom: 18, width: 36, height: 36, borderLeft: `4px solid ${CAMEL}`, borderBottom: `4px solid ${CAMEL}`}} />
          <div style={{position: "absolute", right: 18, bottom: 18, width: 36, height: 36, borderRight: `4px solid ${CAMEL}`, borderBottom: `4px solid ${CAMEL}`}} />
          {mide && time >= mide ? (
            <div style={{position: "absolute", top: 0, bottom: 0, left: `${scan}%`, width: 4, background: CAMEL}} />
          ) : null}
        </div>
      </div>
      <div style={{position: "absolute", left: 1180, top: 150, width: 700, display: "flex", flexDirection: "column", gap: 24}}>
        <Ficha titulo="RED" cuerpo="Aprende el estilo." on={Boolean(aprende && time >= aprende)} extra={gratis && time >= gratis ? "Gratis" : ""} />
        <Ficha titulo="Oficio" cuerpo="Edita con ese estilo." on={Boolean(edita && time >= edita)} extra={noInventa && time >= noInventa ? "No inventa uno" : ""} malo={Boolean(noInventa && time >= noInventa)} />
      </div>
    </>
  );
};

const Ficha: React.FC<{titulo: string; cuerpo: string; on: boolean; extra?: string; malo?: boolean}> = ({titulo, cuerpo, on, extra, malo}) => (
  <div style={{background: on ? MARFIL : PANEL, color: on ? NAVY : MARFIL, borderRadius: 28, padding: "32px 36px", minHeight: 250, boxShadow: "0 18px 40px rgba(0,0,0,0.22)"}}>
    <div style={{fontFamily: sans, fontWeight: 800, fontSize: 72, letterSpacing: -1}}>{titulo}</div>
    <div style={{marginTop: 12, fontFamily: sans, fontWeight: 600, fontSize: 36}}>{cuerpo}</div>
    {extra ? (
      <div style={{marginTop: 18, display: "inline-block", background: malo ? TEJA : SALVIA, color: NAVY, borderRadius: 999, padding: "8px 18px", fontFamily: sans, fontWeight: 800, fontSize: 28}}>
        {extra}
      </div>
    ) : null}
  </div>
);

const MesaChat: React.FC<{time: number}> = ({time}) => {
  const chips = [
    ["Reel", ["reel"]],
    ["YouTube", ["YouTube"]],
    ["Sin cara", ["sin", "cara"]],
    ["Motion", ["motion"]],
    ["Tutorial", ["tutorial"]],
    ["Anuncio", ["anuncio"]],
    ["Clase", ["clase"]],
  ] as const;
  const zona = cuando(["zona", "segura"]);
  const tamano = cuando(["el", "tamaño"]);
  const muestraZona = tamano !== null && time >= tamano;
  return (
    <div style={{position: "absolute", left: 1960, top: 140, width: 1520, height: muestraZona ? 820 : 520, background: PANEL, borderRadius: 28, padding: 32, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
      <div style={{fontFamily: sans, fontWeight: 800, fontSize: 36, color: CAMEL}}>Conversación</div>
      <Burbuja propia texto="Quiero editar este video." />
      <Burbuja texto="¿Qué formato?" />
      <div style={{display: "flex", flexWrap: "wrap", gap: 14, marginTop: 22}}>
        {chips.map(([label, partes]) => {
          const at = cuando([...partes], 17);
          const on = at !== null && time >= at;
          return (
            <div key={label} style={{fontFamily: sans, fontWeight: 800, fontSize: 40, padding: "14px 22px", borderRadius: 16, background: on ? MARFIL : INK, color: on ? NAVY : MARFIL, outline: on ? `3px solid ${CAMEL}` : "none"}}>
              {label}
            </div>
          );
        })}
      </div>
      {muestraZona ? (
        <div style={{...llegada(time, tamano), display: "flex", gap: 28, marginTop: 28, alignItems: "flex-end"}}>
          <MarcoVertical />
          <MarcoHorizontal on={Boolean(zona && time >= zona)} />
        </div>
      ) : null}
    </div>
  );
};

const Burbuja: React.FC<{texto: string; propia?: boolean}> = ({texto, propia}) => (
  <div style={{marginTop: 16, marginLeft: propia ? 280 : 0, marginRight: propia ? 0 : 280, background: propia ? MARFIL : INK, color: propia ? NAVY : MARFIL, borderRadius: 20, padding: "16px 22px", fontFamily: sans, fontWeight: 700, fontSize: 36}}>
    {texto}
  </div>
);

const MarcoVertical: React.FC = () => (
  <div style={{width: 150, height: 266, borderRadius: 16, border: `3px solid ${MARFIL}`, position: "relative"}}>
    <div style={{position: "absolute", left: 0, right: 0, top: 0, height: 48, background: TEJA, opacity: 0.9}} />
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 54, background: TEJA, opacity: 0.9}} />
    <div style={{position: "absolute", bottom: -40, left: 0, fontFamily: sans, fontWeight: 800, fontSize: 28, color: MARFIL}}>9:16</div>
  </div>
);

const MarcoHorizontal: React.FC<{on: boolean}> = ({on}) => (
  <div style={{width: 420, height: 236, borderRadius: 16, border: `3px solid ${on ? CAMEL : MARFIL}`, position: "relative", background: INK}}>
    <div style={{position: "absolute", inset: 28, border: `2px dashed ${CAMEL}`}} />
    <div style={{position: "absolute", left: 40, top: 40, fontFamily: sans, fontWeight: 800, fontSize: 36, color: MARFIL}}>1920×1080</div>
    <div style={{position: "absolute", bottom: -40, left: 0, fontFamily: sans, fontWeight: 800, fontSize: 28, color: MARFIL}}>Zona segura</div>
  </div>
);

const MesaLienzo: React.FC<{time: number}> = ({time}) => {
  const herramientas = ["Figma", "Wonder", "Paper", "Excalidraw"];
  const marcas = cuando(["marcas"]);
  const real = cuando(["tamaño", "real"]);
  const grupos = ["Gancho", "Desarrollo", "Cierre"];
  return (
    <div style={{position: "absolute", left: 3760, top: 110, width: 1640, height: 820, background: "#E7E1D6", borderRadius: 28, padding: 28, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
      <div style={{display: "flex", gap: 16, alignItems: "center"}}>
        <div style={{fontFamily: sans, fontWeight: 800, fontSize: 40, color: NAVY}}>Lienzo</div>
        {herramientas.map((h) => {
          const at = cuando([h]);
          const on = at !== null && time >= at;
          return (
            <div key={h} style={{fontFamily: sans, fontWeight: 700, fontSize: 32, color: on ? NAVY : "#8A8478", background: on ? MARFIL : "transparent", borderRadius: 12, padding: "6px 12px"}}>
              {h}
            </div>
          );
        })}
      </div>
      <div style={{display: "flex", gap: 22, marginTop: 22}}>
        {grupos.map((g, gi) => (
          <div key={g} style={{flex: 1, background: "rgba(27,42,74,0.06)", borderRadius: 20, padding: 16, minHeight: 640}}>
            <div style={{fontFamily: sans, fontWeight: 800, fontSize: 32, color: NAVY}}>{g}</div>
            {[0, 1].map((n) => {
              const marcado = gi === 1 && n === 0 && marcas !== null && time >= marcas;
              return (
                <div key={n} style={{marginTop: 14, height: 210, borderRadius: 16, background: MARFIL, border: marcado ? `4px solid ${CAMEL}` : "4px solid transparent", position: "relative"}}>
                  <div style={{position: "absolute", left: 16, right: 16, top: 24, height: 16, borderRadius: 8, background: NAVY, opacity: 0.2}} />
                  <div style={{position: "absolute", left: 16, right: 70, top: 54, height: 16, borderRadius: 8, background: NAVY, opacity: 0.12}} />
                  {marcado ? (
                    <div style={{position: "absolute", right: 12, top: 12, background: CAMEL, color: NAVY, fontFamily: sans, fontWeight: 800, fontSize: 28, borderRadius: 10, padding: "6px 10px"}}>
                      me gusta
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      {real && time >= real ? (
        <div style={{...llegada(time, real), position: "absolute", right: 48, bottom: 36, background: NAVY, color: MARFIL, borderRadius: 14, padding: "10px 16px", fontFamily: sans, fontWeight: 800, fontSize: 32}}>
          16:9 en tamaño real
        </div>
      ) : null}
    </div>
  );
};

const MesaMedidor: React.FC<{time: number}> = ({time}) => {
  const items = [
    {nombre: "Cortes", palabra: ["cortes"], valor: "12", ancho: 78},
    {nombre: "Color", palabra: ["color"], valor: "navy", ancho: 64},
    {nombre: "Texto", palabra: ["texto"], valor: "38%", ancho: 38},
    {nombre: "Ritmo", palabra: ["ritmo"], valor: "medio", ancho: 52},
  ];
  const dice = cuando(["lo", "dice"]);
  return (
    <div style={{position: "absolute", left: 3760, top: 1160, width: 1640, height: 760, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22}}>
      {items.map((item) => {
        const at = cuando(item.palabra, 37);
        const p = at && time >= at ? interpolate((time - at) * 30, [0, 16], [0, 1], {easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 0;
        return (
          <div key={item.nombre} style={{background: MARFIL, color: NAVY, borderRadius: 24, padding: "28px 32px"}}>
            <div style={{fontFamily: sans, fontWeight: 700, fontSize: 32, color: "#5C5749"}}>{item.nombre}</div>
            <div style={{fontFamily: sans, fontWeight: 800, fontSize: 84, letterSpacing: -2}}>{item.valor}</div>
            <div style={{height: 18, borderRadius: 9, background: "rgba(27,42,74,0.12)", overflow: "hidden"}}>
              <div style={{width: `${item.ancho * p}%`, height: "100%", background: NAVY}} />
            </div>
          </div>
        );
      })}
      {dice && time >= dice ? (
        <div style={{...llegada(time, dice), position: "absolute", left: 36, bottom: 28, background: TEJA, color: NAVY, fontFamily: sans, fontWeight: 800, fontSize: 32, borderRadius: 12, padding: "8px 14px"}}>
          Si no se puede medir, se dice
        </div>
      ) : null}
    </div>
  );
};

const MesaLinea: React.FC<{time: number}> = ({time}) => {
  const guarda = cuando(["se", "guarda"]);
  const reglas = cuando(["las", "reglas"], 46);
  const formato = cuando(["el", "formato"], 47);
  const estilo = cuando(["ese", "estilo"]);
  const arma = cuando(["arma", "la"]);
  const clips = [
    {nombre: "Reglas", at: reglas, color: PANEL},
    {nombre: "Formato", at: formato, color: "#31507A"},
    {nombre: "Estilo", at: estilo, color: CAMEL},
    {nombre: "Corte", at: arma, color: SALVIA},
  ];
  const play = arma && time >= arma ? interpolate(time, [arma, arma + 1.2], [0, 92], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 0;
  return (
    <div style={{position: "absolute", left: 1960, top: 1140, width: 1560, height: 780, background: PANEL, borderRadius: 28, padding: 28, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
      <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
        <div style={{fontFamily: sans, fontWeight: 800, fontSize: 40, color: MARFIL}}>estilos/</div>
        {guarda && time >= guarda ? (
          <div style={{...llegada(time, guarda), background: MARFIL, color: NAVY, borderRadius: 12, padding: "8px 14px", fontFamily: sans, fontWeight: 800, fontSize: 32}}>
            estilo.md
          </div>
        ) : null}
      </div>
      <div style={{marginTop: 36, position: "relative", height: 560, background: INK, borderRadius: 18, overflow: "hidden"}}>
        {clips.map((c, i) => (
          <div key={c.nombre} style={{position: "absolute", left: 24, right: 24, top: 30 + i * 130, height: 100}}>
            <div style={{position: "absolute", left: 0, right: 0, top: 48, height: 2, background: "rgba(255,248,238,0.15)"}} />
            <div style={{...(c.at && time >= c.at ? llegada(time, c.at) : {opacity: 0.28}), position: "absolute", left: 80 + i * 40, width: 340, height: 84, borderRadius: 14, background: c.at && time >= c.at ? c.color : "transparent", border: `3px solid ${c.color === PANEL ? MARFIL : c.color}`, color: c.color === CAMEL || c.color === SALVIA ? NAVY : MARFIL, display: "flex", alignItems: "center", paddingLeft: 18, fontFamily: sans, fontWeight: 800, fontSize: 32}}>
              {c.nombre}
            </div>
          </div>
        ))}
        <div style={{position: "absolute", top: 0, bottom: 0, left: `${8 + play * 0.84}%`, width: 3, background: CAMEL}} />
      </div>
    </div>
  );
};

const MesaArbol: React.FC<{time: number}> = ({time}) => {
  const filas = [
    {texto: ".claude/", at: cuando(["punto", "claude"]), nivel: 0},
    {texto: "skills/", at: cuando(["skills"]), nivel: 1},
    {texto: "picassos-red/", at: cuando(["picassos"]), nivel: 2},
    {texto: "oficio-de-edicion/", at: cuando(["oficio", "de", "edición"], 52), nivel: 2},
  ];
  const prompt = cuando(["el", "prompt"]);
  const clona = cuando(["clonas"]);
  const arranca = cuando(["arrancas"]);
  const lineas = [
    {t: "Clona el repo.", at: clona},
    {t: "Copia las carpetas.", at: prompt},
    {t: "Arranca con un video mío.", at: arranca},
  ];
  return (
    <>
      <div style={{position: "absolute", left: 140, top: 1160, width: 760, height: 700, background: PANEL, borderRadius: 28, padding: 32, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
        <div style={{fontFamily: sans, fontWeight: 800, fontSize: 36, color: CAMEL}}>Carpetas</div>
        {filas.map((f) => (
          <div key={f.texto} style={{...llegada(time, f.at), marginTop: 18, marginLeft: f.nivel * 36, fontFamily: sans, fontWeight: 800, fontSize: 40, color: MARFIL}}>
            {f.texto}
          </div>
        ))}
      </div>
      <div style={{position: "absolute", left: 960, top: 1160, width: 860, height: 700, background: MARFIL, borderRadius: 28, padding: 32, boxShadow: "0 24px 60px rgba(0,0,0,0.28)"}}>
        <div style={{fontFamily: sans, fontWeight: 800, fontSize: 36, color: CAMEL}}>Prompt</div>
        {lineas.map((l) => {
          const on = l.at !== null && time >= l.at;
          return (
            <div key={l.t} style={{marginTop: 28, fontFamily: sans, fontWeight: 800, fontSize: 44, color: on ? NAVY : "rgba(27,42,74,0.35)"}}>
              {l.t}
            </div>
          );
        })}
      </div>
    </>
  );
};

const Subtitulo: React.FC<{time: number}> = ({time}) => {
  const scene = [...SCENES].reverse().find((s) => s.start <= time) || SCENES[0];
  const dichos = scene.words.filter((w) => w.start <= time + 0.03);
  const cola: Word[] = [];
  for (const w of dichos) {
    cola.push(w);
    while (cola.map((x) => x.t).join(" ").length > 42 && cola.length > 1) cola.shift();
  }
  if (!cola.length) return null;
  return (
    <div style={{position: "absolute", left: 160, right: 160, bottom: 22, display: "flex", justifyContent: "center", alignItems: "flex-end", gap: 10, flexWrap: "wrap"}}>
      {cola.map((w, i) => {
        const es = norm(w.t) === norm(scene.key) || (norm(scene.key).length > 3 && norm(w.t).includes(norm(scene.key)));
        const estilo = llegada(time, w.start);
        if (es) {
          return (
            <span key={`${w.start}-${i}`} style={{...estilo, background: MARFIL, color: NAVY, fontFamily: clave, fontStyle: "italic", fontSize: 48, lineHeight: 1, padding: "4px 12px 8px"}}>
              {w.t}
            </span>
          );
        }
        return (
          <span key={`${w.start}-${i}`} style={{...estilo, color: "#FFFFFF", fontFamily: sans, fontWeight: 650, fontSize: 40, filter: "none", transform: "none", opacity: 1}}>
            {w.t}
          </span>
        );
      })}
    </div>
  );
};

export const Tutorial: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const time = frame / fps;
  let indice = 0;
  SCENES.forEach((s, i) => {
    if (s.start <= time) indice = i;
  });
  const actual = FOCO[SCENES[indice].id];
  const previo = FOCO[SCENES[Math.max(0, indice - 1)].id];
  const u = interpolate(time, [SCENES[indice].start, SCENES[indice].start + 0.42], [0, 1], {
    easing: ease,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x = previo.x + (actual.x - previo.x) * u + Math.sin(time * 0.8) * 8;
  const y = previo.y + (actual.y - previo.y) * u;
  const z = previo.z + (actual.z - previo.z) * u;
  return (
    <AbsoluteFill style={{background: NAVY, overflow: "hidden"}}>
      <Audio src={staticFile("voz.mp3")} />
      <div style={{width: 5600, height: 2400, transform: `translate(${960 - x * z}px, ${540 - y * z}px) scale(${z})`, transformOrigin: "0 0"}}>
        <Grid />
        <svg width={5600} height={2400} style={{position: "absolute", inset: 0}}>
          <path d="M860 490 C 1800 470, 2100 470, 2720 490 S 4000 500, 4560 500 S 4560 1540, 4560 1540 S 3400 1520, 2720 1520 S 1400 1480, 860 1480" fill="none" stroke={CAMEL} strokeWidth={4} opacity={0.55} />
        </svg>
        <MesaClip time={time} />
        <MesaChat time={time} />
        <MesaLienzo time={time} />
        <MesaMedidor time={time} />
        <MesaLinea time={time} />
        <MesaArbol time={time} />
      </div>
      <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 118, background: NAVY}}>
        <Subtitulo time={time} />
        <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 6, background: "rgba(255,248,238,0.16)"}}>
          <div style={{width: `${(frame / durationInFrames) * 100}%`, height: "100%", background: CAMEL}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
