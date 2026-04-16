## === Instructions to generate the setup.exe === ##

[ Generating files to be installed ]

1. Open cmd and run "auto-py-to-exe"  (if not installed "pip install auto-py-to-exe")
2. Select the script "AniDex.py"
3. Click on "One directory"
4. Click on "Window based"
5. Under "Icon menu", select the ".ico" file (currently is "ramen.ico")
6. Under "Additional Files menu", select the ".ico" and the ".db"
7. Under "Advanced", search for "--contents-directory". Write "." in the box
8. clik on "Convert .py to .exe"
9. From the "output" folder, extract the "AniDex" folder
10. zip the "AniDex" folder into "AniDex.zip"

[ Generating the setup.exe ]

1. Open cmd and run "auto-py-to-exe"  (if not installed "pip install auto-py-to-exe")
2. Select the script "setup.py"
3. Click on "One File"
4. Click on "Window based"
5. Under "Additional Files menu", select the "AniDex.zip"
6. Under "Advanced", search for "--uac-admin" and enable it
7. clik on "Convert .py to .exe"
8. From the "output" folder, extract the "setup.exe"
