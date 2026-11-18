/* Una entrada por video. Cambiar la URL es editar solo este objeto.
   ratio es opcional. Si no está, manda --reel-ratio en styles.css (9 / 16).
   url vacía = tarjeta pendiente, sin enlace inventado. */
const VIDEOS = {
  "alex-1": {
    url: "https://www.instagram.com/p/DflIjHrkgKJ/",
    ratio: "9 / 16",
  },
  "alex-2": {
    url: "https://www.instagram.com/p/De2Jqyvtd4H/",
    ratio: "9 / 16",
  },
  /* TODO: falta la URL. No inventar un link de un tercero. */
  "faceless-1": { url: "", ratio: "9 / 16" },
  /* TODO: falta la URL. No inventar un link de un tercero. */
  "faceless-2": { url: "", ratio: "9 / 16" },
  /* TODO: falta la URL. No inventar un link de un tercero. */
  "faceless-3": { url: "", ratio: "9 / 16" },
};

const PROMPT = `Quiero usar el paquete gratis Picasso's RED y Oficio de edición para destilar un estilo de video.

1. Clona o descarga este repositorio.
https://github.com/alvexworkspace/ingeniera-inversa-edit-style

2. Copia estas dos carpetas dentro de .claude/skills/ del proyecto donde vamos a trabajar.
.claude/skills/picassos-red
.claude/skills/oficio-de-edicion

3. Si vamos a medir videos, instala las dependencias con pip install -r requirements.txt. Hacen falta ffmpeg y ffprobe en el sistema.

4. Arranca Picasso's RED con este video de referencia.
[PEGA AQUÍ EL LINK O LA RUTA DEL VIDEO]

Antes de reunir más referencias, pregunta el formato. No lo adivines.
El lienzo es obligatorio. Pregúntame cuál uso. Puede ser Figma, Wonder, Paper, Excalidraw u otro.
Si hay un conector, úsalo. Si no, exporta las imágenes y una guía para armarlo a mano.
Sin lienzo no sintetices.
Cuando yo apruebe el estilo, guárdalo en .claude/skills/oficio-de-edicion/estilos/ usando la plantilla.`;

function kindOf(url) {
  const u = url.toLowerCase();
  if (u.includes("instagram.com/")) return "instagram";
  if (u.includes("youtube.com/") || u.includes("youtu.be/")) return "youtube";
  if (/\.(mp4|webm|mov)(\?|$)/.test(u)) return "file";
  return "link";
}

function youtubeId(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname === "youtu.be") return parsed.pathname.slice(1);
    if (parsed.searchParams.get("v")) return parsed.searchParams.get("v");
    const parts = parsed.pathname.split("/").filter(Boolean);
    const embed = parts.indexOf("embed");
    if (embed >= 0 && parts[embed + 1]) return parts[embed + 1];
    const shorts = parts.indexOf("shorts");
    if (shorts >= 0 && parts[shorts + 1]) return parts[shorts + 1];
  } catch (err) {
    return "";
  }
  return "";
}

let instagramScript = null;

function loadInstagram() {
  if (window.instgrm && window.instgrm.Embeds) return Promise.resolve();
  if (instagramScript) return instagramScript;
  instagramScript = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://www.instagram.com/embed.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("instagram"));
    document.body.appendChild(script);
  });
  return instagramScript;
}

function showFallback(reel) {
  reel.classList.add("is-fallback");
  reel.classList.remove("is-live");
}

function showLive(reel) {
  reel.classList.add("is-live");
  reel.classList.remove("is-fallback");
}

function watchInstagram(reel, stage) {
  const started = Date.now();
  const tick = () => {
    const frame = stage.querySelector("iframe");
    if (frame) {
      const done = () => {
        if (frame.clientHeight > 40) showLive(reel);
        else showFallback(reel);
      };
      frame.addEventListener("load", done, { once: true });
      frame.addEventListener("error", () => showFallback(reel), { once: true });
      setTimeout(done, 2500);
      return;
    }
    if (Date.now() - started > 7000) showFallback(reel);
    else setTimeout(tick, 400);
  };
  tick();
}

function mountInstagram(reel, url) {
  const stage = reel.querySelector(".stage");
  const quote = document.createElement("blockquote");
  quote.className = "instagram-media";
  quote.setAttribute("data-instgrm-permalink", url);
  quote.setAttribute("data-instgrm-version", "14");
  const link = document.createElement("a");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Ver en Instagram";
  quote.appendChild(link);
  stage.querySelector(".embed").appendChild(quote);
  loadInstagram()
    .then(() => {
      if (window.instgrm && window.instgrm.Embeds) window.instgrm.Embeds.process();
      watchInstagram(reel, stage);
    })
    .catch(() => showFallback(reel));
}

function mountYoutube(reel, url) {
  const id = youtubeId(url);
  if (!id) {
    showFallback(reel);
    return;
  }
  const frame = document.createElement("iframe");
  frame.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id);
  frame.title = reel.querySelector("figcaption").textContent.trim();
  frame.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
  frame.allowFullscreen = true;
  frame.addEventListener("load", () => showLive(reel), { once: true });
  frame.addEventListener("error", () => showFallback(reel), { once: true });
  reel.querySelector(".embed").appendChild(frame);
  setTimeout(() => {
    if (!reel.classList.contains("is-live")) showFallback(reel);
  }, 7000);
}

function mountFile(reel, url) {
  const video = document.createElement("video");
  video.src = url;
  video.controls = true;
  video.playsInline = true;
  video.preload = "metadata";
  video.addEventListener("loadeddata", () => showLive(reel), { once: true });
  video.addEventListener("error", () => showFallback(reel), { once: true });
  reel.querySelector(".embed").appendChild(video);
}

function prepareReel(reel) {
  const id = reel.dataset.video;
  const spec = VIDEOS[id] || { url: "" };
  const ratio = spec.ratio || reel.dataset.ratio || "";
  if (ratio) reel.style.setProperty("--ratio", ratio);
  const fallbackLink = reel.querySelector(".fallback a");
  if (!spec.url) {
    reel.classList.add("is-empty");
    if (fallbackLink) fallbackLink.remove();
    return;
  }
  if (fallbackLink) fallbackLink.href = spec.url;
  const kind = kindOf(spec.url);
  if (kind === "instagram") mountInstagram(reel, spec.url);
  else if (kind === "youtube") mountYoutube(reel, spec.url);
  else if (kind === "file") mountFile(reel, spec.url);
  else showFallback(reel);
}

function copyPrompt() {
  const button = document.querySelector("[data-copy]");
  const done = () => {
    const previous = button.textContent;
    button.textContent = "Copiado";
    setTimeout(() => {
      button.textContent = previous;
    }, 1600);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(PROMPT).then(done).catch(() => copyPromptFallback(done));
  } else {
    copyPromptFallback(done);
  }
}

function copyPromptFallback(done) {
  const area = document.createElement("textarea");
  area.value = PROMPT;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.left = "-999px";
  document.body.appendChild(area);
  area.select();
  document.execCommand("copy");
  area.remove();
  done();
}

document.getElementById("prompt-text").textContent = PROMPT;
document.querySelector("[data-copy]").addEventListener("click", copyPrompt);
document.querySelectorAll("[data-video]").forEach(prepareReel);
