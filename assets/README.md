# Brand assets

| File | Use |
|------|-----|
| `socrates.svg` | The Socrates wordmark + reasoning-loop logo. Renders inline on GitHub and scales cleanly. Used as the banner in the root `README.md`. |
| `socrates.png` | *(optional)* The original particle-portrait artwork. |

## Adding the original portrait artwork

The repository ships with a self-contained vector logo (`socrates.svg`) so the
README always renders. If you want the original "constellation portrait"
artwork (the dark particle bust of Socrates with the QUESTION / REASON /
CRITIQUE / REFLECT loop), drop it here as:

```
assets/socrates.png
```

Then, if you'd like the README to use it instead of the SVG, change the image
line at the top of the root `README.md` from `assets/socrates.svg` to
`assets/socrates.png`.

Keep artwork under a few hundred KB where possible so clones stay light.
