import sqlite3
import os
import time
import sys
import msvcrt
import glob

DB_NAME = 'AnimeWatchList'
table_name = 'ANIME' 
normal_flag = True;  #set to True for normal operation, False to bypass and test dedicated functions

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
        CREATE TABLE IF NOT EXISTS {table_name}(
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
        test = file[0] #test operation to se if "file" is empty
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
        current_dir = os.path.dirname(sys.executable) #for when running as .exe
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    db_files = [file for file in os.listdir(current_dir) if file.endswith('.db')] #for when running on terminal
    
    db_name = db_files[0]
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    l = [cursor, conn]
    return l

def add_new_anime(cursor,conn):
    """Function to add a single anime to the database.""" 
    flag = False
    title = input('Add anime name: ')
    season = input('Add season: ')
    while(flag == False):
        status = input('Add watching status: ')
        if status == 'on going' or status == 'finished':
            flag = True
        else:
            print("invalid status")
    if(status == 'finished'):
        last = '#'
    else:
        last = input('Add last watched episode: ')
        

    
    try:
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
    cursor.execute('SELECT id, title, season, status, last FROM anime')
    results = cursor.fetchall()
    print("\n--- My Anime Database ---")
    print(f'   {str():<10}{"Title":<50}{"Season":<10}  {"Status"} \n')
    for row in results:
        print(f'ID {str(row[0]):<10}{str(row[1]):<50}s.{str(row[2]):<10}{row[3]}')
    print("----------------------\n")

def show_finished(cursor, conn):
    cursor.execute('SELECT id, title, status, season FROM anime')
    results = cursor.fetchall()
    print("\n--- Finished anime ---\n")
    for row in results:
        if(row[2] == 'finished'):
            print(f'ID {str(row[0]):<10} {row[1]}  s.{str(row[3]):<10}')
        else:
            pass
    print("----------------------\n")

def show_ongoing(cursor, conn):
    cursor.execute('SELECT id, title, status, season ,last FROM anime')
    results = cursor.fetchall()
    print("\n--- On going anime ---\n")
    for row in results:
        if(row[2] == 'on going'):
            print(f'ID {str(row[0]):<10} {row[1]} s.{str(row[3]):<10} ep.{row[4]}')
        else:
            pass
    print("----------------------\n")

def clear_screen():
    if(os.name == 'nt'):
        os.system('cls')
    else:
        os.system('clear')

def main_screen(l):
    cursor = l[0]
    conn = l[1]

    while(True):
        clear_screen()
        print("=== ANIME TRACKER MENU ===")
        print("1. Add new")
        print("2. Show all")
        print("3. Show finished")
        print("4. Show on-going")
        print("5. Update")
        print("6. Exit")
        print("==========================")
        print("\n\n")

        choice = int(input('Select options:'))

        match choice:
            case 1:
                clear_screen()
                add_new_anime(cursor, conn)
                input('\nPress any key to return to menu....')
            case 2:
                clear_screen()
                show_all_anime(cursor, conn)
                input('\nPress any key to return to menu....')
            case 3:
                clear_screen()
                show_finished(cursor, conn)
                input('\nPress any key to return to menu....')
            case 4:
                clear_screen()
                show_ongoing(cursor, conn)
                input('\nPress any key to return to menu....')
            case 5:
                clear_screen()
                update(cursor, conn)
                input('\nPress any key to return to menu....')
            case 6:
                clear_screen()
                print('closing....')
                conn.close()
                time.sleep(1)
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

def moving(cursor, conn):
    current_idx = 1
    window_size = 50 # max anime to display in one page

    cursor.execute('SELECT id, title, status FROM anime')
    results = cursor.fetchall()
    output = f''
    
    while(True):
        print(f'   {str():<10}{"Title":<50}{"Status"} \n')

        start_idx = current_idx
        end_idx = window_size
    
        for row in results:
            pointer = "->" if row[0] == current_idx else "  "
            print(f'{pointer}ID {str(row[0]):<10}{str(row[1]):<50}{row[2]}')
            
        print(f'\033[H\033[2K', end='')

        key = get_key()
        if key == 'up':
            current_idx -= 1
        elif key == 'down':
            current_idx += 1
        elif key == 'enter':
            return str(results[current_idx-1][0]) # Return the ID as a string
        
        if current_idx <= 0:
            current_idx = len(results)
        elif current_idx > len(results):
            current_idx = 1

def update(cursor, conn):
    id = moving(cursor, conn)
    
    while(True):
        clear_screen()
        print('What do you want to change? \n')
        print('-> 1. title\n')
        print('-> 2. season\n')
        print('-> 3. status\n')
        print('-> 4. episode\n')
        print('-> 5. exit\n')
        update = int(input(':::: '))

        match update:
            case 1:
                title = input('Update title: ')
                cursor.execute('''
                    UPDATE ANIME 
                    SET title = ? 
                    WHERE id = ?''',
                    (title.strip(), id.strip())
                )
            case 2:
                season = input('Update season: ')
                cursor.execute('''
                    UPDATE ANIME 
                    SET season = ? 
                    WHERE id = ?''',
                    (season.strip(), id.strip())
                )
            case 3:
                status = input('Update status: ')
                cursor.execute('''
                    UPDATE ANIME 
                    SET status = ? 
                    WHERE id = ?''',
                    (status.strip(), id.strip())
                )
            case 4:
                cursor.execute('''
                    SELECT status FROM ANIME
                    WHERE id = ?''',
                    (id.strip(),)
                )
                status = cursor.fetchone()
                if status == 'finished':
                    last = '#'
                else:
                    last = input('Update last ep.: ')
                cursor.execute('''
                    UPDATE ANIME 
                    SET last = ? 
                    WHERE id = ?''',
                    (last.strip(), id.strip())
                )
            case 5:
                break

        conn.commit()
        input('press any key...')

def txt_to_db(l, filename):
    cursor = l[0]
    conn = l[1]
    print("Starting migration...\n")
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines or lines without our arrow separator
            if not line or '->' not in line:
                continue
            
            # Split the line wherever there is a '->'
            parts = line.split('->')
            
            # 1. Extract the Title (First part)
            title = parts[0].strip()
            
            
            # 2. Extract the Status (Second part)
            status = parts[1].strip()
            
            # 3. Extract the Season/Last Ep (Third part, ONLY if it exists)

            season = parts[2].strip()

            last = '#'
                
            # Insert into the database
            try:
                # We are inserting the 'season' into your 'last' column
                cursor.execute('''
                    INSERT INTO anime (title, season, status, last) 
                    VALUES (?, ?, ?, ?)
                ''', (title, season, status, last))
            except sqlite3.IntegrityError:
                print(f"Skipped: '{title}' (Already in database)")
                
    conn.commit()
    conn.close()
    print("\n--- Migration Complete! ---")


if __name__ == '__main__':
    if normal_flag == True:
        main_screen(__init__())
    else:
        """
        add below function to test
        """
       
             