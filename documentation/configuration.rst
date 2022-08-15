Configure Natlink
=================

Location of 'natlink.ini'
-------------------------

The config file `natlink.ini` will by default be in `~\\.natlink`, so a subdirectory of your home directory, typically `C:\\Users\\Name`.
- When you want another directory for your file `natlink.ini` to be in, you can set this in the environment variable 'NATLINK_USERDIR'. When you want your `.natlink` directory in your Documents directory, you can specify 'NATLINK_USERDIR' to '~\\Documents\\.natlink'. Note, this directory should be a local directory.



When running the `natlinkconfig` program (automatically done as last step of the inno setup installer), next step is automatically performed:

- copy the file `natlink.ini` from the 'fallback' location  into your home directory, subdirectory `.natlink`. (So: "C:\\Program Files (x86)\\Natlink\\DefaultConfig\\natlink.ini" is copied into "C:\\Users\\Name\\.natlink\\natlink.ini".)


Adding directories to the configuration
---------------------------------------

Natlink will load all python grammar files that are specified in the '[directories]' section of 'natlink.ini'.

- Some directories are needed by a package, especially Unimacro and Vocola.
- Directories where your Dragonfly grammars, grammars from packages relying on Dragonfly, such as Caster, and user defined grammar files will be.

- The directories for user input of Vocola and Unimacro need another place, see below.

The directories will easiest be set with the config program, (`natlinkconfig`). A GUI program is being worked on. It is not completely clear when 'elevated mode' is required. When you want to (re)run the config program in elevated mode, you can always rerun the 'inno setup program'! In the last step, the config program is started, and this is in elevated mode.

- In 'natlinkconfig', you can type `I` for opening the 'natlink.ini' file in Notepad, for manual editing.

- And press `u` for usage instructions.

For manually adding directories, see examples below. As these examples show, you can use a shared (eg Dropbox, OneDrive) folder for the directories, where you can put your own input files.  

- Add Dragonfly (option 'd'), a directory where your Dragonfly scripts are to be found, for example:

::

   [directories]
   dragonflyuserdirectory = ~\Dropbox\NatlinkUser\DragonflyUser

or

::

   [directories]
   dragonflyuserdirectory = ~\Documents\DragonflyUser



- Add UserDirectory (option 'n'), Note: Dragonfly users can choose between 'Add Dragonfly' or this option, for example:

::

   [directories]
   userdirectory = ~\Dropbox\NatlinkUser\UserDir

Vocola
------
- Via the option 'v' in `natlinkconfig`, this goes easiest, and vocola2 is installed via pip.
- When you type 'V', Vocola is disabled, when you type `v` again (specify the same directory), vocola2 is also upgraded if necessary!

- When you want to enable vocola, manually, enter something like the following lines in 'natlink.ini':

::

   [directories]
   vocoladirectory = vocola2
   vocolagrammarsdirectory = natlink_userdir\VocolaGrammars

   [vocola]
   vocolauserdirectory = ~\Documents\vocola_qh

Unimacro
--------

- Via the option 'o' in `natlinkconfig`, this goes easiest, and Unimacro is installed via pip.
- When you type 'O', Unimacro is disabled, when you type `o` again (specify the same directory), Unimacro is also upgraded if necessary!

- When you want to enable Unimacro, manually, enter something like the following lines in 'natlink.ini':


::

    [directories]
    unimacrodirectory = unimacro
    unimacrogrammarsdirectory = natlink_userdir\UnimacroGrammars
    
    [unimacro]
    unimacrouserdirectory = ~\Documents\unimacro_qh


Set the log_level
-------------------

You can set the log_level, controlling the abundance of information messages in the "Messages from Natlink" window with the following option (choices are DEBUG, INFO, WARNING).

::

    [settings]
    log_level = INFO


