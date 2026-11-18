export const FPS = 30;

export const NAVY = "#060F22";
export const NAVY_CARD = "#111D35";
export const BLUE = "#2E70F0";
export const TEXT = "#F4F7FB";
export const MUTED = "#9BA3B3";
export const LINE = "rgba(255,255,255,0.1)";

export const S = {
  open: 9 * FPS,
  what: 13 * FPS,
  pieces: 14 * FPS,
  flow: 40 * FPS,
  formats: 16 * FPS,
  install: 16 * FPS,
  prompt: 14 * FPS,
  end: 10 * FPS,
} as const;

export const DURATION =
  S.open + S.what + S.pieces + S.flow + S.formats + S.install + S.prompt + S.end;
