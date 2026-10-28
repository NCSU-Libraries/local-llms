<div align="center">

<a href="https://www.lib.ncsu.edu/" aria-label="NC State University Libraries"><img src="site/images/lib_logo_whiteBG.svg" width="400" alt="NC State University Libraries logo" /></a>

<h2>Working with Local LLMs</h2>

<a href="https://www.lib.ncsu.edu/workshops"><img alt="NC State Libraries Workshops" src="https://img.shields.io/badge/NC%20State%20Libraries-Workshops-red"></a>
<a href="https://www.lib.ncsu.edu/staff/department/data-science-services"><img alt="Data Science Services" src="https://img.shields.io/badge/Data%20Science%20Services-Libraries-red"></a>
<a href="https://go.ncsu.edu/getdatahelp"><img alt="Get Data Help" src="https://img.shields.io/badge/Get%20Data%20Help-go.ncsu.edu%2Fgetdatahelp-red"></a>

</div>

A 60-minute online workshop from NC State University Libraries' Data Science Services, part of Data Science Special
Topics. It's a hands-on introduction to running AI models on your own computer with [Ollama](https://ollama.com):
install it, pull a first model, chat with it, and choose a second that fits your machine to see how models differ.
No coding needed.

**Workshop site:** <https://ncsu-libraries.github.io/local-llms/>, or go.ncsu.edu/local-llms

## What's here

| Path | What it is |
| --- | --- |
| `site/` | The Quarto website, with the Setup page |
| `site/slides/anim/_shared/` | The animation framework for the slide deck |
| `tools/` | A link checker and screenshot tools |

## Build it locally

You need [Quarto](https://quarto.org) 1.10 or later. RStudio ships one at
`/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto`.

```bash
quarto render site            # builds site/_site
quarto preview site           # or serve it locally while editing
python3 tools/check_links.py  # checks every link and image in site/_site
```

## Publishing

Pushing to `main` runs `.github/workflows/deploy-pages.yml`, which renders the site and deploys it to GitHub Pages. Set
**Settings → Pages → Source** to **GitHub Actions** *before* the first push. The first push of a root commit doesn't
trigger the paths-filtered workflow, so run it once from the **Actions** tab.

## License

Content is licensed [CC BY 4.0](LICENSE-CC-BY-4.0.md) and code is [MIT](LICENSE).
