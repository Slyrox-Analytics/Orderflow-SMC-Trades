
import base64, json, time
import requests
from typing import Optional, Tuple

class GHStore:
    def __init__(self, token: str, owner: str, repo: str, branch: str = "main"):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.api = f"https://api.github.com/repos/{owner}/{repo}/contents"

    def _headers(self):
        return {"Authorization": f"token {self.token}", "Accept": "application/vnd.github+json"}

    def get_file(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        url = f"{self.api}/{path}"
        r = requests.get(url, headers=self._headers(), params={"ref": self.branch})
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            sha = data["sha"]
            return content, sha
        elif r.status_code == 404:
            return None, None
        else:
            raise RuntimeError(f"GitHub GET failed {r.status_code}: {r.text}")

    def put_file(self, path: str, content_str: str, message: str, sha: Optional[str] = None):
        url = f"{self.api}/{path}"
        b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        payload = {
            "message": message,
            "content": b64,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=self._headers(), json=payload)
        if r.status_code not in (200,201):
            raise RuntimeError(f"GitHub PUT failed {r.status_code}: {r.text}")
        return r.json()

    def upload_binary(self, path: str, data: bytes, message: str, sha: Optional[str] = None):
        url = f"{self.api}/{path}"
        b64 = base64.b64encode(data).decode("utf-8")
        payload = {
            "message": message,
            "content": b64,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=self._headers(), json=payload)
        if r.status_code not in (200,201):
            raise RuntimeError(f"GitHub PUT failed {r.status_code}: {r.text}")
        return r.json()
