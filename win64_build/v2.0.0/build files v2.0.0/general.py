import re
import browser_cookie3 as bc

# this dictionary holds language name as key and corresponding ISO language code as value
LANG_NAME_TO_CODE_MAPPING = {'Arabic': 'ar', 'Afrikaans': 'af',
                             'Bangla': 'bn', 'Burmese': 'my',
                             'Chinese (Simplified)': 'zh-Hans', 'Chinese (Traditional)': 'zh-Hant', 'Chinese': 'zh',
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
    '''this function assumes that the url is of this format:
    coursera.org/learn/CLASSNAME/more thing...
    if the url isn't in this format, program won't work'''

    classname = ''

    if ('/' in homepageurl) or ('\\' in homepageurl):
        classname = re.findall(
            'coursera.org/learn/(.+?)/', homepageurl.lower())
        classname = ''.join(classname)  # convert list to string
    else:
        # if homepageurl doesn't contain slash treat it as just a string
        # 'python-network-data' would output 'python-network-data'
        classname = homepageurl

    return classname


def loadcauth(domain):
    '''this function returns the cauth code of browser for the specified domain.
    example use: loadcauth('coursera.org'). the function searches only in the cookie
    files of chrome and firefox. if there is no cauth for the domain function returns
    an empty string'''
    cj = bc.load(domain_name=domain)

    strcookie = str(cj)
    cauth = re.findall('CAUTH=(.*?)\s', strcookie)

    # print(strcookie)
    # print(len(cauth))
    if len(cauth) > 0:
        cauth = cauth[0]
    else:
        cauth = ''

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
