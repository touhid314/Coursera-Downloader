import re
import browser_cookie3 as bc

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


def loadcauth(domain):
    '''this function returns the cauth code of browser for the specified domain.
    example use: loadcauth('coursera.org'). the function searches only in the cookie
    files of chrome and firefox. if there is no cauth for the domain function returns
    an empty string'''

    cauth = -1 

    # first try to load cauth from firefox
    from locked_cookie import fetch_locked_cookies
    try:
        cj_ffox = bc.firefox(domain_name=domain)
        for cookie in cj_ffox:
            if (cookie.name == "CAUTH"):
                cauth = cookie.value
                print('>> FETCHED AUTHENTICATION FROM FIREFOX\n')    
    except:
            cauth = -1
            print('>> failed to load authentication from firefox\n')
    
    # failed to load cauth from firefox, try chrome
    if (cauth == -1):
        try:
            cj_chrome = fetch_locked_cookies(domain='coursera.org')

            for cookie in cj_chrome:
                if(cookie.name == "CAUTH"):
                    cauth = cookie.value
                    print('>> FETCHED AUTHENTICATION FROM CHROME\n')
        except:
            cauth = -1           
            print('>> failed to load authentication from chrome\n')    
    
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