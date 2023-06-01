from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import constants as keys
import psycopg2

## THIS FILE IS FOR THE POSTGRESQL DATABASE ON ELEPHANTSQL##

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="birthdays",
    user="postgres",
    password="xayxay1710"
)

# Create a cursor object to interact with the database
cur = conn.cursor()

# Create a table (if it doesn't exist)
create_table_query = '''
    CREATE TABLE IF NOT EXISTS credentials (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50),
        password VARCHAR(50)
    )
'''
cur.execute(create_table_query)
conn.commit()




# Define conversation states
USERNAME, CHECK_USERNAME, PASSWORD, AUTHENTICATED, LOGIN_OPTION, LOGIN, CREATE, CREATE2 = range(8)

def start(update, context):
    keyboard_options = [['Log In'], ['New User']]
    reply_markup = ReplyKeyboardMarkup(keyboard_options, one_time_keyboard=True)
    update.message.reply_text('Welcome to the bot! Please choose an option. Please press /cancel if the bot gets stuck :)', reply_markup=reply_markup)
    return LOGIN_OPTION

def login_option(update, context):
    
    if update.message.text == 'Log In':
        update.message.reply_text('Please enter your username:')
        return CHECK_USERNAME
    elif update.message.text == 'New User':
        update.message.reply_text('Please enter your new username.')
        return CREATE
    
def create(update, context):
    global new_username
    new_username = update.message.text

    
    # Check if username is taken; check if username string is inside database
    search_string = new_username
    select_query = "SELECT EXISTS(SELECT 1 FROM credentials WHERE username = %s)"
    cur.execute(select_query, (search_string,))
    result = cur.fetchone()[0]
    if result:
        # Re type username
        update.message.reply_text('This username is taken. Please enter a new username!')
        return CREATE
    
    else:
        # Insert new username into database
        insert_query = '''
          INSERT INTO credentials (username) VALUES (%s)
        '''
        data = [
           (new_username), 
        ]
        cur.execute(insert_query, data)
        conn.commit()

        update.message.reply_text("Please enter your new password!")
        return CREATE2

def create2(update, context):
    new_password = update.message.text
    update.message.reply_text("Your account has been added to our database! Press /start to log in with your new account!")
    # Insert new password into database
    update_query = "UPDATE credentials SET password = %s WHERE username = %s"
    username = new_username
    password = new_password
    cur.execute(update_query, (password, username))
    conn.commit()

    return ConversationHandler.END
    

def login(update, context):
    update.message.reply_text('Please enter your username:')
    return CHECK_USERNAME

def check_username(update,context):
    search_string = update.message.text
    select_query = "SELECT EXISTS(SELECT 1 FROM credentials WHERE username = %s)"
    cur.execute(select_query, (search_string,))
    result = cur.fetchone()[0]

    if result:
        username = update.message.text

        # Extract password from username in table
        select_query = "SELECT password FROM credentials WHERE username = %s"
        username = username
        cur.execute(select_query, (username,))
        result = cur.fetchone()
        global expected_password
        expected_password = result[0]
        
        update.message.reply_text('Please enter your password:')
        return PASSWORD
    
    else:
        update.message.reply_text('Wrong username. Enter /start again to retry.')
        return ConversationHandler.END


def handle_password(update, context):
    password = update.message.text

    if password == expected_password:
        context.user_data['authenticated'] = True
        update.message.reply_text('Authentication successful! You are now logged in.')
        return ConversationHandler.END
    else:
        update.message.reply_text('Authentication failed. Please enter /start to try again.')
        return ConversationHandler.END



# def authenticated_command(update, context):
#     if context.user_data.get('authenticated'):
#         # Handle the command for authenticated users
#         update.message.reply_text('This is an authenticated command.')
#     else:
#         update.message.reply_text('You are not authenticated. Please log in first.')

def cancel(update, context):
    update.message.reply_text('Cancelling the conversation.')
    return ConversationHandler.END


def main():
    updater = Updater(keys.API_KEY, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOGIN_OPTION: [MessageHandler(Filters.text & (~ Filters.command), login_option)],
            LOGIN: [MessageHandler(Filters.text & (~ Filters.command), login)],
            CREATE: [MessageHandler(Filters.text & (~ Filters.command), create)],
            CREATE2: [MessageHandler(Filters.text & (~ Filters.command), create2)],
            CHECK_USERNAME: [MessageHandler(Filters.text & (~ Filters.command), check_username)],
            PASSWORD: [MessageHandler(Filters.text & (~ Filters.command), handle_password)],
            # AUTHENTICATED: [
            #     CommandHandler('command', authenticated_command),
            #     # Add more handlers for authenticated users here
            
            # ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
