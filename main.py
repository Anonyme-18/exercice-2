
import base64
import os
from pathlib import Path

import requests


BASE_URL = "https://api.rodiumai.io/v1"
CHAT_MODEL = "openai/gpt-4o-mini"
IMAGE_MODEL = ""
VIDEO_MODEL = ""


def load_env_file() -> None:
    """Charge les variables simples du fichier .env sans dépendance supplémentaire."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("'\""))


def api_error(response: requests.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    error = payload.get("error", payload) if isinstance(payload, dict) else {}
    error_code = error.get("error_code", error.get("code", "inconnu")) if isinstance(error, dict) else "inconnu"
    message = error.get("message", response.text) if isinstance(error, dict) else response.text
    print(f"Erreur HTTP {response.status_code} — error_code: {error_code} — {message}")


def post(path: str, payload: dict, timeout: int = 150) -> requests.Response | None:
    headers = {
        "Authorization": f"Bearer {os.environ['RODIUMAI_API_KEY']}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(f"{BASE_URL}{path}", headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        print(f"Erreur réseau : {exc}")
        return None
    if response.status_code != 200:
        api_error(response)
        return None
    return response


def chat() -> None:
    question = input("Votre question : ").strip()
    response = post("/chat/completions", {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": question}],
    })
    if response is None:
        return
    data = response.json()
    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Réponse vide")
    cost = data.get("usage", {}).get("cost_rodi", data.get("cost_rodi", "inconnu"))
    print(f"\n{answer}\nCoût : {cost} RODI")


def image() -> None:
    if not IMAGE_MODEL:
        print("Modèle image absent. Ajoutez RODIUMAI_IMAGE_MODEL dans .env avec un identifiant du catalogue RodiumAi.")
        return
    prompt = input("Décrivez l'image : ").strip()
    response = post("/images/generations", {"model": IMAGE_MODEL, "prompt": prompt, "n": 1, "response_format": "b64_json"})
    if response is None:
        return
    item = response.json().get("data", [{}])[0]
    encoded = item.get("b64_json")
    if not encoded:
        print("Réponse invalide : aucun champ b64_json reçu.")
        return
    filename = input("Nom du fichier (Entrée = image.png) : ").strip() or "image.png"
    Path(filename).write_bytes(base64.b64decode(encoded))
    print(f"Image enregistrée : {filename}")


def video() -> None:
    if not VIDEO_MODEL:
        print("Modèle vidéo absent. Ajoutez RODIUMAI_VIDEO_MODEL dans .env avec un identifiant du catalogue RodiumAi.")
        return
    prompt = input("Décrivez la vidéo courte : ").strip()
    response = post("/videos/generations", {"model": VIDEO_MODEL, "prompt": prompt, "duration_seconds": 4}, timeout=150)
    if response is None:
        return
    data = response.json()
    item = data.get("data", [{}])[0] if isinstance(data.get("data"), list) else data.get("data", {})
    video_url = item.get("url") or item.get("video_url") or data.get("url") or data.get("video_url")
    filename = input("Nom du fichier (Entrée = video.mp4) : ").strip() or "video.mp4"
    encoded = item.get("b64_json") or data.get("b64_json")
    if encoded:
        Path(filename).write_bytes(base64.b64decode(encoded))
        print(f"Vidéo enregistrée : {filename}")
        return
    if not video_url:
        print(f"Réponse vidéo non reconnue. Champs reçus : {', '.join(data.keys())}")
        return
    try:
        video_response = requests.get(
            video_url,
            headers={"Authorization": f"Bearer {os.environ['RODIUMAI_API_KEY']}"},
            timeout=150,
        )
        video_response.raise_for_status()
        Path(filename).write_bytes(video_response.content)
    except requests.RequestException as exc:
        print(f"Erreur lors du téléchargement de la vidéo : {exc}")
        return
    print(f"Vidéo enregistrée : {filename}")


def main() -> None:
    global BASE_URL, CHAT_MODEL, IMAGE_MODEL, VIDEO_MODEL
    load_env_file()
    BASE_URL = os.getenv("RODIUMAI_BASE_URL", BASE_URL).rstrip("/")
    CHAT_MODEL = os.getenv("RODIUMAI_CHAT_MODEL", CHAT_MODEL)
    IMAGE_MODEL = os.getenv("RODIUMAI_IMAGE_MODEL", "")
    VIDEO_MODEL = os.getenv("RODIUMAI_VIDEO_MODEL", "")
    if not os.getenv("RODIUMAI_API_KEY"):
        raise SystemExit("Clé absente : configurez RODIUMAI_API_KEY dans .env ou les variables d'environnement.")

    steps = [chat, image, video]
    index = 0
    while 0 <= index < len(steps):
        print(f"\n=== Étape {index + 1} : {['Chat', 'Image', 'Vidéo'][index]} ===")
        steps[index]()
        if index == 0:
            choices = {"r": index, "s": index + 1}
            prompt = "Rester sur cette étape (r) ou passer à la suivante (s) ? "
        elif index == len(steps) - 1:
            choices = {"b": index - 1, "r": index, "q": len(steps)}
            prompt = "Revenir en arrière (b), rester (r) ou quitter (q) ? "
        else:
            choices = {"b": index - 1, "r": index, "s": index + 1}
            prompt = "Revenir en arrière (b), rester (r) ou passer à la suivante (s) ? "
        choice = input(prompt).strip().lower()
        while choice not in choices:
            choice = input("Choix invalide. Réessayez : ").strip().lower()
        index = choices[choice]
    print("Programme terminé.")


if __name__ == "__main__":
    main()
