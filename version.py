"""Versión de Control Celular y aviso de versión nueva.

Para buscar una versión nueva solo se consulta la página pública de "Releases" del proyecto en GitHub
(no se manda ningún dato tuyo). Se puede apagar desde el ícono: «Buscar versiones nuevas».
"""

import json
import re
import urllib.request

VERSION = "1.9.0"
REPO = "markbackend/CONTROL-CELULAR"
PAGINA_RELEASES = f"https://github.com/{REPO}/releases/latest"


def _numeros(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def version_nueva() -> str | None:
    """Devuelve la versión publicada si es más nueva que esta, o None (sin internet, repo privado, etc.)."""
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/latest",
                                     headers={"Accept": "application/vnd.github+json",
                                              "User-Agent": "ControlCelular"})
        with urllib.request.urlopen(req, timeout=8) as r:
            etiqueta = json.load(r).get("tag_name", "")
        return etiqueta.lstrip("vV") if _numeros(etiqueta) > _numeros(VERSION) else None
    except Exception:
        return None
