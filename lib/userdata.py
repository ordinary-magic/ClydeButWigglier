from datetime import datetime
import sqlite3
import os

class UserDatabase():
  # Initialize the database connection
  def __init__(self, channel):
    os.makedirs('data/users', exist_ok=True)
    self._db = sqlite3.connect(f'data/users/{channel}.db')
    query = 'CREATE TABLE IF NOT EXISTS users(id INTEGER UNIQUE, name TEXT, pronouns TEXT, flag TEXT)'
    self._db.execute(query)
    query = 'CREATE TABLE IF NOT EXISTS prompts(id INTEGER UNIQUE, prompt TEXT, context INTEGER)'
    self._db.execute(query)
    
  # Close the database
  def close(self):
    self._db.close()
  
  # instantiation method when used in 'with' block  
  def __enter__(self):
    return self
  
  # destruction method when used in 'with' block  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

  # Get all values that have data in a specific column
  def get_all_values(self, column):
    query = f'SELECT {column} FROM users WHERE {column} IS NOT NULL'
    results = self._db.execute(query).fetchall()
    return [x[0] for x in results] 

  # Get a given field from the table for a given user id
  def get_value(self, id, column, table='users'):
    query = f'SELECT {column} FROM {table} WHERE id = ?'
    val = self._db.execute(query, (id,)).fetchone()
    return val[0] if val else None
  
  # Set a given field to the specified value for the input user id.
  #   Will create a new entry if needed
  def set_value(self, id, column, value, table='users'):
    try:
      query = f'INSERT INTO {table} (id, {column}) VALUES (?, ?)'
      self._db.execute(query, (id, value))
    except sqlite3.Error:
      query = f'UPDATE {table} SET {column} = ? WHERE id = ?'
      self._db.execute(query, (value, id))
    self._db.commit()  

  # Get (Name, Pronouns) for a given ID. Either or both can be none.
  def get_name_and_pronouns(self, id):
    query = 'SELECT name, pronouns FROM users WHERE id = ?'
    return self._db.execute(query, (id,)).fetchone()
  
  # Get pronouns for all users with a specific name (or None if not in db)
  def get_pronouns_for_name(self, name):
    query = 'SELECT pronouns FROM users WHERE name = ? COLLATE NOCASE'
    results = self._db.execute(query, (name,)).fetchall()
    return [x[0] for x in results]

  # Get a user with a specific flag (or None if not in db)
  def get_special_user(self, flag):
    query = 'SELECT id FROM users WHERE flag = ?'
    val = self._db.execute(query, (flag,)).fetchone()
    return val[0] if val else None

# Get all names that are stored in a server's db
def get_all_names(server):
  with UserDatabase(server) as db:
    return db.get_all_values('name')

# Get the name and pronouns of a specific server
# Returns (Name, Pronouns), and both fields can be empty
def get_name_and_pronouns(server, id):
  with UserDatabase(server) as db:
    return db.get_name_and_pronouns(id) or (None, None)

# Get the prompt for a channel in a server
# Will return the current prompt, or None
def get_prompt(server, channel):
  with UserDatabase(server) as db:
    return db.get_value(channel, 'prompt', 'prompts')
  
# Get the context amount for a channel in a server
# Will return the current context, or None if the row doesnt exist yet
def get_context(server, channel):
  with UserDatabase(server) as db:
    return db.get_value(channel, 'context', 'prompts')

# Get the pronouns for a specific name in a given server
# Will return a comma seperated list of all pronouns the user uses
def get_pronouns_for_name(server, name):
  with UserDatabase(server) as db:
    return db.get_pronouns_for_name(name)
  
# Get the id of a special user, optionally in a specific server
#   flag is a special text flag
#   related_to is a message context to fetch a user list from
def get_special_user(server, flag):
  with UserDatabase(server) as db:
    user = db.get_special_user(flag)
  return user

# Set the name of a specific user in a given server
def set_name(server, id, name):
  with UserDatabase(server) as db:
    db.set_value(id, 'name', name)

# Set the prompt for a channel in a server
def set_prompt(server, channel, prompt):
  with UserDatabase(server) as db:
    db.set_value(channel, 'prompt', prompt, 'prompts')

# Set the context amount for a channel in a server
def set_context(server, channel, context):
  with UserDatabase(server) as db:
    if context >= 0:
      db.set_value(channel, 'context', context, 'prompts')

# Set the pronouns of a specific user in a given server
def set_pronouns(server, id, pronouns):
  with UserDatabase(server) as db:
    db.set_value(id, 'pronouns', pronouns)

