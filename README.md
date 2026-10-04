# Exercice 2 — API RodiumAi

Ce projet est un script Python interactif qui teste successivement le chat, la génération d'image et la génération de vidéo avec l'API RodiumAi. À chaque étape, l'utilisateur peut recommencer, revenir en arrière ou continuer.

## Installation

Python 3.10 ou supérieur est recommandé.

```bash
python -m venv .venv
```

Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuration

Copiez `.env.example` vers `.env`, puis remplacez la valeur par votre clé RodiumAi :

```powershell
Copy-Item .env.example .env
```

Le fichier `.env` est ignoré par Git et ne doit jamais être publié.

## Lancement

```powershell
python main.py
```

La vidéo demandée dure 4 secondes et la requête vidéo utilise un délai maximal de 150 secondes. Les modèles peuvent être remplacés avec `RODIUMAI_CHAT_MODEL`, `RODIUMAI_IMAGE_MODEL` et `RODIUMAI_VIDEO_MODEL`.
