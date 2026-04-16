import sqlite3
import os
import time
import sys
import msvcrt
import glob

DB_NAME = 'AnimeWatchList'
TABLE_NAME = 'ANIME' 
NORMAL_FLAG = True;  #set to True for normal operation, False to bypass and test dedicated functions

"""
To create .exe from this code:
- open cmd in the same directory of this code
- run "pyinstaller --onefile <file name>.py"
- extract the .exe and put it in the same directory of the .db
"""

#è possibile mettere più table nello stesso db

def create_db(db_name):
    conn = sqlite3.connect(f'{db_name}.db')
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        season TEXT,
        status TEXT,
        last INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def __init__():
    file = glob.glob("*.db") #find if there is a .db file in the folder
    try:
        test = file[0] #test operation to se if "file" is empty (empty == no .db file founded)
    except IndexError:
        print("Anime list database not found.. \n")
        s = input("You want to create a new one? (Y/n) ::: ")
        if s == "Y" or s == "y":
            create_db(DB_NAME)  #create database
        else:
            print("please place the .db file in the same folder as the .exe and retry...")
            input() #press any key to abort the execution
            exit() #abort the execution
            

    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable) #save path directiory as text (works when on .exe)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))#save path directiory as text (works running the code on terminal)

    db_files = [file for file in os.listdir(current_dir) if file.endswith('.db')] #save .db file name
    
    db_name = db_files[0]
    conn = sqlite3.connect(db_name) #connection to the database
    cursor = conn.cursor()          #opening cursor to move insede the database
    l = [cursor, conn]              #create array to pass cursor and connection variable to the functios
    return l

def add_new_anime(cursor,conn):
    """Function to add a single anime to the database.""" 

    flag = False
    title = input('Add anime name: ')   #add anime title
    season = input('Add season: ')      #add season number of the anime

    while(flag == False):
        status = input('Add watching status: ')
        if status == 'on going' or status == 'finished': #wrong words execption check function
            flag = True
        else:
            print("invalid status")

    if(status == 'finished'): #if anime is finished, no need to add episode
        last = '#'
    else:
        last = input('Add last watched episode: ')


    try:
        #adding anime to the database, if not already inside
        cursor.execute('''
            INSERT INTO anime (title, season,status, last) 
            VALUES (?, ?, ?, ?)
            ''', 
        (title.strip(), season.strip(), status.strip(), last.strip()))
        conn.commit()
        print(f'Successfully added')

    except sqlite3.IntegrityError: 
        print(f'Notice: {title} is already in the database!')

def show_all_anime(cursor, conn):
    """Function to display everything currently in the database."""

    cursor.execute('SELECT id, title, season, status, last FROM anime') #tell the cursor what to select
    results = cursor.fetchall() #fetching function

    #printing values
    print("\n--- My Anime Database ---")
    print(f'   {str():<10}{"Title":<50}{"Season":<10}  {"Status"} \n')
    for row in results:
        print(f'ID {str(row[0]):<10}{str(row[1]):<50}s.{str(row[2]):<10}{row[3]}')
    print("----------------------\n")

def show_finished(cursor, conn):
    """Function to display finished anime only."""

    cursor.execute('SELECT id, title, status, season FROM anime') #tell the cursor what to select
    results = cursor.fetchall() #fetching function

    #printing values
    print("\n--- Finished anime ---\n")
    for row in results:
        if(row[2] == 'finished'):
            print(f'ID {str(row[0]):<10} {row[1]}  s.{str(row[3]):<10}')
        else:
            pass
    print("----------------------\n")

def show_ongoing(cursor, conn):
    """Function to display on going anime only."""

    cursor.execute('SELECT id, title, status, season ,last FROM anime') #tell the cursor what to select
    results = cursor.fetchall() #fetching function

    #printing values
    print("\n--- On going anime ---\n")
    for row in results:
        if(row[2] == 'on going'):
            print(f'ID {str(row[0]):<10} {row[1]} s.{str(row[3]):<10} ep.{row[4]}')
        else:
            pass
    print("----------------------\n")

def clear_screen():
    """Function to clear display."""
    if(os.name == 'nt'):
        os.system('cls')
    else:
        os.system('clear')

def selection(options, title):
    """General function for interactive menu selection with cursor."""

    current_idx = 0
    clear_screen()

    while(True):
        print(title) #print the title of the menu

        for row in enumerate(options):
            pointer = "->" if row[0] == current_idx  else "  " #print the pointer only on the current selected choice
            print(f'{pointer} {row[1]}')
            
        print(f'\033[H\033[2K', end='') #alternative clear function to prevent annoying refresh-flickering of the screen while moving the cursor up and down

        key = get_key()
        if key == 'up':
            current_idx -= 1
        elif key == 'down':
            current_idx += 1
        elif key == 'enter':
            return options[current_idx] #return the choice where the cursor is pointing
        elif key == 'q': #shortcut to close selection menu
            clear_screen()
            exit()
        
        #pack-man effect condition
        if current_idx < 0:
            current_idx = len(options)-1
        elif current_idx >= len(options):
            current_idx = 0

def main_screen(l):
    """Main screen of the .exe ."""

    cursor = l[0]
    conn = l[1]
    options = ["Add new", "Show all", "Show finished", "Show on-going", "Update", "Exit"] #options to display throw the selection function
    clear_screen()

    while(True):
        choice = selection(options, "=== ANIME TRACKER MENU ===")
    
        if choice == options[0]:
                clear_screen()
                add_new_anime(cursor, conn)
                input('\nPress any key to return to menu....')
        elif choice == options[1]:
                clear_screen()
                show_all_anime(cursor, conn)
                input('\nPress any key to return to menu....')
        elif choice == options[2]:
                clear_screen()
                show_finished(cursor, conn)
                input('\nPress any key to return to menu....')
        elif choice == options[3]:
                clear_screen()
                show_ongoing(cursor, conn)
                input('\nPress any key to return to menu....')
        elif choice == options[4]:
                clear_screen()
                update(cursor, conn)
        elif choice == options[5]:
                clear_screen()
                print('closing....')
                conn.close()
                time.sleep(1) #little delay before closing .exe
                clear_screen()
                break

def get_key():
        key = msvcrt.getch()
        if key in (b'\xe0', b'\x00'): # Arrow key prefix
            key = msvcrt.getch()
            if key == b'H': return 'up'
            if key == b'P': return 'down'
        elif key == b'\r': return 'enter'
        elif key.lower() == b'q': return 'q'
        elif key.lower() == b'w': return 'up'
        elif key.lower() == b's': return 'down'
        return None

def selection_update_menu(cursor, conn):
    """dedicated function for interactive menu selection with cursor (for database values seletion)."""

    current_idx = 1

    cursor.execute('SELECT id, title, status FROM anime') #tell the cursor what to select
    results = cursor.fetchall() #fetching function

    
    while(True):
        print(f'   {str():<10}{"Title":<50}{"Status"} \n') #print title
    
        for row in results:
            pointer = "->" if row[0] == current_idx else "  " #print the pointer only on the current selected choice
            print(f'{pointer}ID {str(row[0]):<10}{str(row[1]):<50}{row[2]}')
            
        print(f'\033[H\033[2K', end='') #alternative clear function to prevent annoying refresh-flickering of the screen while moving the cursor up and down

        key = get_key()
        if key == 'up':
            current_idx -= 1
        elif key == 'down':
            current_idx += 1
        elif key == 'enter':
            return str(results[current_idx-1][0]) # Return the ID as a string
        
        #pack-man effect condition
        if current_idx <= 0:
            current_idx = len(results)
        elif current_idx > len(results):
            current_idx = 1

def update(cursor, conn):
    """Function to update values of anime inside the database."""

    id = selection_update_menu(cursor, conn)
    options = ["title", "season", "status", "episode", "exit"] #options to display throw the selection function
    last = '#'
    clear_screen()

    while(True):
        update = selection(options,'What do you want to change? \n')

        if update == options[0]: #update the title
            clear_screen()
            title = input('Update title: ')
            cursor.execute('''
                UPDATE ANIME 
                SET title = ? 
                WHERE id = ?''',
                (title.strip(), id.strip())
            )

        elif update == options[1]: #update the season
            clear_screen()
            season = input('Update season: ')
            cursor.execute('''
                UPDATE ANIME 
                SET season = ? 
                WHERE id = ?''',
                (season.strip(), id.strip())
            )

        elif update == options[2]: #update the status
            clear_screen()
            status = input('Update status: ')
            cursor.execute('''
                UPDATE ANIME 
                SET status = ?
                WHERE id = ?''',
                (status.strip(),id.strip())
            )
            if status == 'finished':
                cursor.execute('''
                    UPDATE ANIME
                    SET last = ?
                    WHERE id = ?''',
                    ('#',id.strip())
                )

        elif update == options[3]: #update the episode
            clear_screen()
            cursor.execute('''
                SELECT status FROM ANIME
                WHERE id = ?''',
                (id.strip(),)
            )
            status = cursor.fetchone()

            #preventing to update episode on a finished anime
            if status[0] == 'finished': 
                print("current status is finished..can't update last episode.. \n")
            else:
                last = input('Update last ep.: ')
            cursor.execute('''
                UPDATE ANIME 
                SET last = ? 
                WHERE id = ?''',
                (last.strip(), id.strip())
            )

        elif update == options[4]: #exit
            clear_screen()
            break

        conn.commit()
        if update != options[4]:
            input('press any key...')



if __name__ == '__main__':
    if NORMAL_FLAG == True:
        main_screen(__init__())
    else:
        """
        add below function to test
        """
       

             