v1.0.0 - uses the coursera-dl script  
v2.0.0 - uses the fork by raffaem (https://github.com/raffaem/cs-dlp)  
v2.1.0 - solved the bug of permission error for chrome and edge.   
        authentication is now only possible from firefox and chrome.  
        added menu.  
        added error handling in maingui.py and general.py.  
        solved logical error in urltoclassname function.  
        also some minor changes.  

        unsolved problem:  
        * space in download path is still a problem  
        * add permission error handling for data.bin reading and writing

v2.1.1 - 
        * organized the repo, deleted the old code
        * fixed chinese subtitle code to zh-CN
        
v3.0.0 - 
        * stopped using tkinter and switched to pyqt
        * dowload path cannot contain space - bug solved
        * UI update
        * some minor UI bug solved
        * can check for app update
        * anonymously log user country and app open time to remote server for analyzing total app users
        * can show notification fetched from remote server
