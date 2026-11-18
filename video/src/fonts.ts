import {continueRender, delayRender} from "remotion";
import {loadFont as loadJakarta} from "@remotion/google-fonts/PlusJakartaSans";
import {loadFont as loadSerif} from "@remotion/google-fonts/DMSerifDisplay";

const jakarta = loadJakarta("normal", {
  weights: ["500", "600", "700", "800"],
  subsets: ["latin"],
});

const serif = loadSerif("italic", {
  weights: ["400"],
  subsets: ["latin"],
});

const handle = delayRender("Fuentes");
Promise.all([jakarta.waitUntilDone(), serif.waitUntilDone()]).then(() => {
  continueRender(handle);
});

export const sans = jakarta.fontFamily;
export const clave = serif.fontFamily;
