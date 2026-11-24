// Renders the banner at the top of every help page from the help config.
import defaults from '../../config/defaults.json' with { type: 'json' };
import pages from '../../config/help-pages.json' with { type: 'json' };
import palette from '../styles/palette.json' with { type: 'json' };

export function bannerStyle(pageId) {
  const name = pages[pageId]?.bannerColor ?? defaults.helpBannerColor;
  const colour = palette[name];
  if (!colour) throw new Error(`unknown banner colour: ${name}`);
  return { background: colour.background, color: colour.text };
}
