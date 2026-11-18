import {continueRender, delayRender} from "remotion";
import {loadFont as loadJakarta} from "@remotion/google-fonts/PlusJakartaSans";
import {loadFont as loadPlayfair} from "@remotion/google-fonts/PlayfairDisplay";

const jakarta = loadJakarta("normal", {
  weights: ["500", "600", "700", "800"],
  subsets: ["latin"],
});

const playfair = loadPlayfair("italic", {
  weights: ["800"],
  subsets: ["latin"],
});

const handle = delayRender("Fuentes de la marca");
Promise.all([jakarta.waitUntilDone(), playfair.waitUntilDone()]).then(() => {
  continueRender(handle);
});

export const sans = jakarta.fontFamily;
export const serif = playfair.fontFamily;
