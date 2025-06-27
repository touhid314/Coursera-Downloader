import re
import rookiepy

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
                             'Malay': 'ml', 'Malayalam': 'ml',
                             'Portugese': 'pt',
                             'Russian': 'ru',
                             'Spanish': 'es',
                             'Tamil': 'ta', 'Telegu': 'te', 'Thai': 'th', 'Turkish': 'tr',
                             'Urdu': 'ur',
                             'Vietnamese': 'vi',
                             '-ALL AVAILABLE': 'all', '-NONE': ''}

ALLOWED_BROWSERS = ["edge", "firefox", "brave"]

# extract class name from course home page url
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
    cauth = ""

    if browser not in ALLOWED_BROWSERS:
        print(f"Browser not supported. Please login on one of these browsers: {', '.join(ALLOWED_BROWSERS)}")
        return cauth
    else:
        try:
            if browser == "firefox":
                # works even when script is run without admin access
                cookies = rookiepy.firefox([domain])
            elif browser == "edge":
                # works only when script is run with admin access
                cookies = rookiepy.edge([domain])
            elif browser == "brave":
                # works only when script is run with admin access
                cookies = rookiepy.brave([domain])
            # elif browser == "opera":
            #     # does not work, throws error
            #     cookies = rookiepy.opera([domain])
            # elif browser == "opera_gx":
            #     # does not work, throws error
            #     cookies = rookiepy.opera_gx([domain])
        except Exception as e:
            print(f"Error fetching cookies: {e}")
            print(f"Could not fetch authentication. Maybe run the app as administrator.")
            return cauth

    for cookie in cookies:
            if cookie['name'] == "CAUTH":
                cauth = cookie['value']
    
    return cauth


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
if __name__ == "__main__":
    ca = loadcauth('coursera.org', browser='opera_gx')
    print(ca)