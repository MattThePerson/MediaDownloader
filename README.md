## Wrapper script for gallery-dl

### Configured to download from:

- Twitter
- Reddit
- Danbooru
- RedGifs


### Deps
- gallery-dl
- yt-dlp


### Installing and Running

- To install, execute `setup.sh` (chmod first)
- To run, execute `run.sh` (Add symlink to folder on path for convenience)


### Gallery-DL

- **repo**: https://github.com/mikf/gallery-dl
- **options**: https://github.com/mikf/gallery-dl/blob/master/docs/options.md
- **config help**: https://gdl-org.github.io/docs/configuration.html#extractor-specific-options

To run in package dir with local config:
`gallery-dl --config config/gallery-dl.conf <other-options> <url>`


### Notes

- config/yt-dlp.conf needs to exist for gallery-dl to be able to use the venvs yt_dlp
- yt-dlp only really for tiktok
