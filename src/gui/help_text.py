def get_help_text():
    # No colors here: the window takes them from the system light/dark theme.
    return """
    <h2>Quick start</h2>
    <ol>
      <li><b>Log in.</b> Follow the steps under <i>Logging in</i> below. The
          status turns green and shows <b>Logged in</b> when you are ready.</li>
      <li><b>Choose the course.</b> Pick one of your enrolled courses from the
          list, or paste a course link such as
          <i>https://www.coursera.org/learn/model-thinking</i>. You must be
          enrolled in the course.</li>
      <li><b>Choose your options.</b> Select a download folder, video resolution
          and subtitle language.</li>
      <li><b>Click Download.</b> Progress appears in the app, just below the
          buttons, and on the app's taskbar button.</li>
    </ol>

    <h2>Logging in</h2>
    <p><b>With the embedded browser (default):</b> keep <b>Embedded browser</b>
    selected, click <b>Open Coursera login</b> and sign in using the window that
    opens. You stay logged in the next time you open the app.</p>
    <p><b>With your browser (Firefox or Brave):</b> select the browser, click
    <b>Open Coursera login</b> and sign in there. The app notices the login by
    itself. If it does not, click <b>I've logged in</b>.</p>

    <h2>What gets downloaded</h2>
    <p>Videos, subtitles, readings, quizzes, notebooks and other course files.
    They are saved in a folder named after the course, organized week by week
    just like the course itself.</p>
    <p><b>Specializations and professional certificates:</b> paste the link,
    such as <i>https://www.coursera.org/specializations/deep-learning</i>, to
    download every course in it, one after another. They are saved together in
    a folder named after the specialization. You must be enrolled in each
    course.</p>
    <p>When the download finishes, click <b>Open folder</b> to see the
    files.</p>

    <h2>During a download</h2>
    <ul>
      <li>The app first reads the course syllabus. This can take a few minutes
          for large courses, and the bar keeps moving while it works.</li>
      <li>You then see the current file, overall progress, downloaded size and
          download speed.</li>
      <li>Files that fail are tried once more at the end of each course.</li>
      <li><b>Stop</b> ends the download. Closing the app offers to stop it
          for you.</li>
    </ul>

    <h2>Resuming a download</h2>
    <p>Click <b>Resume</b> with the same course, folder, resolution and subtitle
    language as before. Finished files are skipped, and the file you were on
    continues from where it stopped.</p>
    <p>Files ending in <b>.part</b> are unfinished downloads. Leave them in place
    so that they can be continued. They get their real name once complete.</p>

    <h2>Troubleshooting</h2>
    <ul>
      <li><b>Not logged in, or an HTTP error:</b> log in again, and check that
          you are enrolled in the course on coursera.org.</li>
      <li><b>Browser login does not work:</b> select <b>Embedded browser</b>
          instead.</li>
      <li><b>Embedded browser does not open:</b> install the
          <a href="https://developer.microsoft.com/microsoft-edge/webview2/">Microsoft
          Edge WebView2 Runtime</a>.</li>
      <li><b>Some files failed:</b> click <b>Resume</b> to try them again.</li>
      <li><b>Connection error:</b> check your internet connection, then click
          <b>Resume</b>.</li>
    </ul>

    <h2>Need more help?</h2>
    <p>Visit <a href="https://coursera-downloader.rf.gd/">the website</a>, or
    report a bug at
    <a href="mailto:touhid3.1416@gmail.com">touhid3.1416@gmail.com</a>.</p>
    """
