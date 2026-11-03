import re
import rookiepy
import os
import shutil
import subprocess
import sys
import keyring
import requests

from ..core.define import OPENCOURSE_MEMBERSHIPS

# this dictionary holds language name as key and corresponding ISO language code as value
LANG_NAME_TO_CODE_MAPPING = {'Arabic': 'ar', 'Afrikaans': 'af',
                             'Bangla': 'bn', 'Burmese': 'my',
                             'Chinese (Simplified)': 'zh-Hans', 'Chinese (Traditional)': 'zh-Hant', 'Chinese': 'zh-CN',
                             'Dutch': 'nl',
                             'English': 'en',
                             'French': 'fr', 'Finnish': 'fi',
                             'Greek': 'el',
                             'Hindi': 'hi',
                             'Italian': 'it',
                             'Japanese': 'ja',
                             'Korean': 'ko',
                             'Malay': 'ms', 'Malayalam': 'ml',
                             'Portuguese': 'pt',
                             'Russian': 'ru',
                             'Spanish': 'es',
                             'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th', 'Turkish': 'tr',
                             'Urdu': 'ur',
                             'Vietnamese': 'vi',
                             '-ALL AVAILABLE': 'all', '-NONE': ''}

ALLOWED_BROWSERS = ["firefox", "brave"]
# Logging in through the app's own window (WebView2) instead of a browser.
EMBEDDED_LOGIN = "embedded"
# Pasting the CAUTH cookie by hand, for when no other method works.
MANUAL_LOGIN = "manual"
LOGIN_METHODS = [EMBEDDED_LOGIN] + ALLOWED_BROWSERS + [MANUAL_LOGIN]
AUTH_SERVICE = "CourseraDownloader"
EMBEDDED_AUTH_ACCOUNT = "embedded-cauth"
# Logins the app keeps itself, by login method. Browser logins stay in the browser.
SAVED_AUTH_ACCOUNTS = {
    EMBEDDED_LOGIN: EMBEDDED_AUTH_ACCOUNT,
    MANUAL_LOGIN: "manual-cauth",
}


def load_saved_auth(method):
    """Load a login saved in the OS credential vault for this login method."""
    try:
        return keyring.get_password(AUTH_SERVICE, SAVED_AUTH_ACCOUNTS[method]) or ""
    except Exception:
        return ""


def save_auth(method, cauth_cookie):
    """Store a login in the OS credential vault for this login method."""
    try:
        keyring.set_password(AUTH_SERVICE, SAVED_AUTH_ACCOUNTS[method], cauth_cookie)
        return True
    except Exception:
        return False


def clear_saved_auth(method):
    """Remove a saved login for this login method from the OS credential vault."""
    try:
        keyring.delete_password(AUTH_SERVICE, SAVED_AUTH_ACCOUNTS[method])
    except Exception:
        pass


def load_embedded_auth():
    """Load the embedded-browser session from the OS credential vault."""
    return load_saved_auth(EMBEDDED_LOGIN)


def save_embedded_auth(cauth_cookie):
    """Store the embedded-browser session in the OS credential vault."""
    return save_auth(EMBEDDED_LOGIN, cauth_cookie)


def normalize_pasted_cauth(text):
    """
    Return the CAUTH cookie value from what the user pasted.

    Accepts the bare value, "CAUTH=value", or a whole Cookie header that
    contains CAUTH. Returns '' if nothing usable was pasted.
    """
    text = (text or "").strip().strip('"').strip()
    match = re.search(r'(?:^|[;\s])CAUTH=([^;\s]+)', text)
    if match:
        return match.group(1).strip('"')
    # name=value means some other cookie; a trailing "=" is only padding.
    if re.search(r"=[^=]", text) or ";" in text or re.search(r"\s", text):
        return ""
    return text


# Lists only the user's own enrollments, so it is refused exactly when the login
# itself is not valid.
LOGIN_CHECK_URL = "https://api.coursera.org/api/memberships.v1?q=me&limit=1"


def check_cauth(cauth_cookie):
    """
    Ask Coursera whether a CAUTH login cookie is still valid.

    Returns True if it is, False if Coursera rejects it, and None if that could
    not be determined (for example while offline).
    """
    try:
        reply = requests.get(
            LOGIN_CHECK_URL, cookies={"CAUTH": cauth_cookie}, timeout=15
        )
    except requests.RequestException:
        return None
    if reply.status_code in (401, 403):
        return False
    return True if reply.ok else None


def clear_embedded_auth():
    """Remove a saved embedded-browser session from the OS credential vault."""
    clear_saved_auth(EMBEDDED_LOGIN)


def get_default_browser():
    """Return the supported Windows default browser name, when detectable."""
    if sys.platform != "win32":
        return None

    try:
        import winreg

        key_path = (
            r"Software\Microsoft\Windows\Shell\Associations"
            r"\UrlAssociations\https\UserChoice"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            prog_id = winreg.QueryValueEx(key, "ProgId")[0].lower()
    except (FileNotFoundError, OSError):
        return None

    browser_ids = {
        "firefox": "firefox",
        "brave": "brave",
    }
    return next((name for marker, name in browser_ids.items() if marker in prog_id), None)


def open_browser(browser, url):
    """Open a URL in a specific supported browser on Windows."""
    commands = {
        "firefox": "firefox.exe",
        "brave": "brave.exe",
    }
    executable_name = commands.get(browser)
    if not executable_name:
        return False

    candidates = [shutil.which(executable_name)]
    program_files = os.environ.get("ProgramFiles", "")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    if browser == "firefox":
        candidates.extend([
            os.path.join(program_files, "Mozilla Firefox", executable_name),
            os.path.join(program_files_x86, "Mozilla Firefox", executable_name),
        ])
    elif browser == "brave":
        candidates.extend([
            os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", executable_name),
            os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "Application", executable_name),
        ])

    executable = next((item for item in candidates if item and os.path.isfile(item)), None)
    if not executable:
        return False

    subprocess.Popen([executable, url])
    return True

# extract class name from course home page url
# Coursera link paths: a course, or a group of courses.
_COURSE_LINK = re.compile(
    r'coursera\.org/(learn|specializations|professional-certificates)/([^/?#]+)',
    re.IGNORECASE)


def parse_course_input(text):
    """
    Read what the user entered as the course.

    Returns (slug, is_specialization). The slug is '' if the text is not a
    Coursera course or specialization link, nor a bare course name.
    """
    text = text.strip()
    if re.fullmatch(r'[a-zA-Z0-9-]+', text):
        return text, False  # a bare name is taken as a course
    match = _COURSE_LINK.search(text)
    if not match:
        return '', False
    return match.group(2).lower(), match.group(1).lower() != 'learn'


def get_enrolled_courses(cauth_cookie):
    """Return the user's enrolled courses as (name, slug) pairs, by name."""
    reply = requests.get(
        OPENCOURSE_MEMBERSHIPS, cookies={"CAUTH": cauth_cookie}, timeout=20
    )
    reply.raise_for_status()
    courses = reply.json().get('linked', {}).get('courses.v1', [])
    found = {(course.get('name') or course['slug'], course['slug'])
             for course in courses if course.get('slug')}
    return sorted(found, key=lambda course: course[0].lower())


def urltoclassname(homepageurl):
    '''this function assumes that the url is of this possible format:
    1. https://www.coursera.org/learn/model-thinking
    2. https://www.coursera.org/learn/model-thinking/home/week/1
    3. https://www.coursera.org/learn/model-thinking?specialization=deep-learning

    if the url isn't in this format, program won't work'''

    classname = ''

    slug_pattern = r'^[a-zA-Z0-9-]+$' # if the input is a slug, and not a url, it will consists of alphanumeric and hyphen
    if re.search(slug_pattern, homepageurl):
        # it's a slug, not a url
        return homepageurl
    else:
        # it's a url
        classname = re.findall('coursera\.org/learn/([^/?]+)', homepageurl.lower())
        if len(classname) > 0:
            classname = classname[0]  # if multiple match, take only the first one
        else:
            # no match
            classname = ""
        return classname


def loadcauth(domain:str, browser:str):
    """this function returns the cauth code of browser for the specified domain.
    
    args:
        browser - must be in the ALLOWED_BROWSERS list
    
    example use: loadcauth('coursera.org'). 
    
    """
    cauth, _ = loadcauth_with_error(domain, browser)
    return cauth


def loadcauth_with_error(domain: str, browser: str):
    """Return the CAUTH cookie and a user-facing browser access error."""
    cauth = ""

    if browser not in ALLOWED_BROWSERS:
        return cauth, "Unsupported browser."

    try:
        browser_reader = getattr(rookiepy, browser)
        cookies = browser_reader([domain])
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        # rookiepy is written in Rust. When it fails badly, for example while
        # reading a locked cookie file straight from an NTFS disk, the Rust
        # panic reaches Python as pyo3_runtime.PanicException, which derives
        # from BaseException rather than Exception.
        print(f"Error fetching cookies from {browser}: {type(e).__name__}: {e}")
        error = str(e)
        if "appbound encryption" in error.lower() and "admin" in error.lower():
            return cauth, (
                f"{browser.title()} protects its cookies with app-bound encryption. "
                "Use the embedded browser, or select Firefox."
            )
        return cauth, (
            f"Could not read the Coursera login from {browser.title()}. "
            f"Close {browser.title()} and try again, or use the embedded browser."
        )

    for cookie in cookies:
            if cookie['name'] == "CAUTH":
                cauth = cookie['value']
    
    return cauth, ""


def move_to_first(dictionary, key):
    if key not in dictionary:
        return dictionary  # Key not found, no changes needed

    value = dictionary[key]
    # Create a new dictionary with the desired key-value pair as the first item
    new_dict = {key: value}

    for k, v in dictionary.items():
        if k != key:
            # Insert the remaining key-value pairs into the new dictionary
            new_dict[k] = v

    return new_dict

# testing urltoclassname function
# url = "https://www.coursera.org/learn/model-thinking"
# url = "https://www.coursera.org/learn/model-thinking/home/week/1"
# url = "https://www.coursera.org/learn/neural-networks-deep-learning?specialization=deep-learning"
# url = "https://www.coursera.org/learn/java-programming-recommender/home/week/1https://www.coursera.org/learn/java-programming-recommender/home/week/1"
# url = "model-thinking-hell"
# url = "model-thinking?"
# cn = urltoclassname(url)
# print(cn)
