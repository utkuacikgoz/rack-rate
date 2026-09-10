# Nimbus Sans L

Self-hosted here as WOFF2 (converted from the source OTF files with
`fonttools`, no hinting or glyph changes).

- Family: Nimbus Sans L (Regular, Italic, Bold, Bold Italic)
- Copyright 2014, (URW)++ Design & Development GmbH
- Metric-compatible with Helvetica

## License

The OTF source files carry no embedded license text (only copyright and
manufacturer name in their `name` table). This is the same "Nimbus Sans L"
family that [Font Squirrel documents as free for web embedding](https://www.fontsquirrel.com/license/nimbus-sans-l),
tracing back to URW's 1996 GPL/AFPL release of the core Ghostscript fonts,
later versions under LPPL. That determination is what this repo relies on,
not a license file bundled with these specific font files.

This is a different release from the current `urw-base35-fonts` Debian
package (`NimbusSans`, no "L"), which ships under AGPL-3 with a font
exception scoped to PDF/PostScript output only, not general web embedding.
Do not substitute one for the other without re-checking this note.

If you are a maintainer and can source a copy with clearer bundled licensing
terms, replacing these files is welcome.
