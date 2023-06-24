from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askdirectory
import subprocess
import os
import pickle
from varname import nameof
import general
from coursera_dl import main_f
import webbrowser


class main:
    def __init__(self):

        # window
        self.window = Tk()
        self.window.title("Coursera Downloader")
        self.window.resizable(False, False)

        # @variables
        cauth = StringVar()
        classname = StringVar()
        path = StringVar()
        vidres = StringVar()
        sllangs = StringVar()  # subtitle languages

        self.shouldResume = False

        # @
        self.inputvardict = {'ca': cauth, 'classname': classname,
                             'path': path, 'video_resolution': vidres,
                             'sl': sllangs}

        # load argument's value
        self.argdict = self.loadargdict()

        # set input variable's values
        for key, value in self.inputvardict.items():
            value.set(self.argdict[key])

        # Load UI
        self.loadUI()

        # start mainloop
        self.window.mainloop()

    def loadUI(self):

        # frame
        frame1 = Frame(self.window)
        frame1.pack()

        LW = 20  # LABEL WIDTH
        EW = 50  # ENTRY WIDTH

        # info message frame
        infoMsgFrame = Frame(frame1, padx=0, pady=6)
        infoMsgFrame.grid(row=1, column=1, columnspan=2)

        msg = '''You must be logged in in coursera.org in Chrome or Firefox.\
                Browser don't have to be opened though.\
                    \nYou can only download courses that you are enrolled in\
                    \n* Make sure that your download path don't include any space.\
                    \ni.e. "C:\Test User" will generate error. '''
        infoMsg = Message(infoMsgFrame, text=msg, width=400)
        infoMsg.grid(row=1)

        # course name row
        Label(frame1,
              text="Course Home Page URL: ",
              width=LW,
              anchor='w').grid(row=4, column=1)

        name_entry = Entry(frame1,
                           textvariable=self.inputvardict['classname'],
                           width=EW)
        name_entry.grid(row=4, column=2)
        name_entry.focus_set()

        # download folder row
        Label(frame1, text="Download Folder: ", width=LW,
              anchor='w').grid(row=5, column=1, sticky='W')
        Button(frame1, text="Select Folder", command=self.getPath).grid(
            row=5, column=2, sticky='W')
        Message(frame1, textvariable=self.inputvardict['path'], width=300, anchor='w').grid(
            row=6, column=2, sticky='w')

        # video resolution row
        Label(frame1,
              text="Video Resolution: ",
              width=LW,
              anchor='w').grid(row=7, column=1, sticky='W')

        innerframe = Frame(frame1)
        innerframe.grid(row=7, column=2, sticky='W')

        Radiobutton(innerframe,
                    text="720p",
                    variable=self.inputvardict['video_resolution'],
                    value='720p').grid(row=1, column=1)

        Radiobutton(innerframe,
                    text="540p",
                    variable=self.inputvardict['video_resolution'],
                    value='540p').grid(row=1, column=2)

        Radiobutton(innerframe,
                    text="360p",
                    variable=self.inputvardict['video_resolution'],
                    value='360p').grid(row=1, column=3)

        self.inputvardict['video_resolution'].set('720p')

        # subtitle language row
        Label(frame1,
              text='Subtitle Language: ',
              width=LW,
              anchor='w').grid(row=10, column=1)

        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        self.inputvardict['sl'].set('English')

        ttk.Combobox(frame1,
                     textvariable=self.inputvardict['sl'],
                     values=sorted(list(self.sllangschoices.keys())),
                     state='readonly').grid(row=10, column=2, sticky='W')

        # transcript row

        # download and resume button row
        btnFrame = Frame(frame1)
        btnFrame.grid(row=11, column=2, sticky='E')

        downloadBtn = Button(btnFrame,
                             text="Download",
                             command=self.downloadBtnHandler)
        downloadBtn.grid(row=11, column=2, sticky='E')

        resumeBtn = Button(btnFrame,
                           text='Resume',
                           command=self.resumeBtnHandler)
        resumeBtn.grid(row=11, column=1, sticky='E')

        # website link
        label = Label(frame1, text="For usage guide go to")
        link = Label(frame1, text="http://coursera-downloader.rf.gd/",
                     fg="blue", cursor="hand2")
        link.bind("<Button-1>", lambda event: open_url())

        frame1.grid_rowconfigure(12, weight=1)
        frame1.grid_columnconfigure(0, weight=1)

        label.grid(row=12, column=1)
        link.grid(row=12, column=2)

    def downloadBtnHandler(self):
        # load cauth code automatically and store it in inputvardict
        self.inputvardict['ca'].set(general.loadcauth('coursera.org'))

        # make argdict from inputvarlist
        self.argdict = {}
        for key, value in self.inputvardict.items():
            # do necessary processing

            # process classname variable which actually stores course home page url
            # convert the home page url to classname
            if key == 'classname':
                courseurl = self.inputvardict['classname'].get()
                cname = general.urltoclassname(courseurl)
                self.argdict[key] = cname
                continue

            if key == 'sl':
                langcode = self.sllangschoices[self.inputvardict['sl'].get()]
                if langcode == '':
                    self.argdict['ignore-formats'] = "srt"
                    self.argdict[key] = 'en'
                    continue
                else:
                    self.argdict[key] = langcode
                    continue

            self.argdict[key] = value.get()

        # save the argdict to data.bin
        self.saveargdic()

        # create command from argumentdict
        cmd = []

        self.argdict = general.move_to_first(self.argdict, 'ca')
        for item in self.argdict.items():
            # convert ca to -cauth and u to -u
            if (item[0] == 'video_resolution') or (item[0] == 'path'):
                flag = '--' + item[0]
            else:
                flag = '-' + item[0]

            # convert video_resolution to video-resoltion
            flag = flag.replace('_', '-')

            # now append to cmd
            # @ FILTER ARGUMENTS THAT DON'T NEED FLAG LIKE, classname, resume etc.
            if not 'classname' in flag:
                cmd.append(flag)
            cmd.append(item[1])

        # append additional commands
        cmd.append('--download-quizzes')
        cmd.append('--download-notebooks')
        cmd.append('--disable-url-skipping')
        cmd.append('--unrestricted-filenames')
        cmd.append('--combined-section-lectures-nums')
        cmd.append('--jobs')
        cmd.append('1')

        if self.shouldResume == True:
            cmd.append("--resume")

        # # run cmd
        cmd = ' '.join(cmd)

        main_f(cmd)

    def resumeBtnHandler(self):
        self.shouldResume = True
        self.downloadBtnHandler()

    def loadargdict(self):
        # dic = {'username':'', 'password':'', 'cauth': '', 'path':''}
        dic = {}
        for i in self.inputvardict.keys():
            dic[i] = ''

        # if data.bin doesn't exist make it return the empty dic
        if not os.path.isfile("data.bin"):
            f = open("data.bin", 'wb')
            pickle.dump(dic, f)
            f.close()

            return dic
        # else load dic from data.bin
        else:
            f = open("data.bin", 'rb')
            dic = pickle.load(f)
            return dic

    def saveargdic(self):
        # dic = {'username': self.argdict['username'],
        #         'password': self.argdict['password'],
        #         'cauth': self.argdict['cauth'],
        #         'path': self.argdict['path']} #tkinter variable are saved. get method has to be used to get their value

        f = open("data.bin", 'wb')
        pickle.dump(self.argdict, f)
        f.close()

    def getPath(self):
        dir = askdirectory()
        dir = '"{}"'.format(dir)
        self.inputvardict['path'].set(dir)

# global functions


def open_url():
    url = "http://coursera-downloader.rf.gd/"
    webbrowser.open(url)


main()
