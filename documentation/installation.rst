Install Natlink
===================================

- Install Dragon NaturallySpeaking (version 13, 14 or 15).

- Optionally install Python (32 bit) for your user and do not add to path. This is also done automatically by the inno setup installer. Currently only *python39-32* is supported.

- Download and run the latest [Natlink installer](https://github.com/dictation-toolbox/natlink/releases): choose the most recent release, at the top of the page, and then scroll down and choose the file natlink?.?.?-py3.9-32-setup.exe. 

- When you configure Natlink via the `natlinkconfig` GUI, as last step of the inno setup installer, and enable vocola and/or unimacro, these packages are installed via `pip` automatically. 


- When you use dragonfly, or other packages that need dragonfly, pip install these packages (e.g. `pip install dragonfly`). Do this in a 'Windows Powershell' or 'Command prompt', which you need to 'Run as administrator'. You may have to go to the `Scripts` directory of where your (32-bit) Python is installed. (In `Windows Powershell` type `.\\pip install dragonfly` etc.)

- When you start Dragon, the 'Messages from Natlink' window should show up, with the 'fallback' information.

- Proceed to Configure Natlink (Next).


You can also inspect [installation instructions on github](https://github.com/dictation-toolbox/natlink/) (scroll down a bit...)



