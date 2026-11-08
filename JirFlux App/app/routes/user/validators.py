# app/routes/user/validators.py  (new file)
# Plain helper functions for checking user input. Not a blueprint.
import re
from urllib.parse import urlparse

MAX_URL_LENGTH = 300
_GITHUB_HOSTS = ('github.com', 'www.github.com')
_OWNER = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$')   # GitHub user / organisation name
_REPO = re.compile(r'^[A-Za-z0-9_.-]{1,100}$')                  # repository name


def clean_github_url(raw):
    """Check a GitHub repository link and return (clean_url, error_message).

    - empty input     -> (None, None)    meaning "remove the link"
    - valid input     -> ("https://github.com/owner/repo", None)
    - invalid input   -> (None, "message to show the user")
    """
    raw = (raw or '').strip()
    if not raw:
        return None, None

    bad = "That doesn't look like a GitHub repository link. Use https://github.com/owner/repo"

    if len(raw) > MAX_URL_LENGTH:
        return None, "That link is too long."
    if re.search(r'\s', raw):
        return None, bad

    # no scheme typed (github.com/a/b)? assume https
    if not re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw):
        raw = 'https://' + raw

    try:
        parsed = urlparse(raw)
        port = parsed.port
    except ValueError:
        return None, bad

    if parsed.scheme not in ('http', 'https'):
        return None, bad
    if parsed.username or parsed.password or port:
        return None, bad
    if (parsed.hostname or '').lower() not in _GITHUB_HOSTS:
        return None, "Only github.com links are allowed."

    parts = [p for p in parsed.path.split('/') if p]
    if len(parts) < 2:
        return None, bad

    owner, repo = parts[0], parts[1]
    if repo.lower().endswith('.git'):
        repo = repo[:-4]
    if not _OWNER.match(owner) or not _REPO.match(repo) or repo in ('.', '..'):
        return None, bad


    return f"https://github.com/{owner}/{repo}", None