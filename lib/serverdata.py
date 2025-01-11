import sqlite3
import os

class ServerDatabase():
  # Initialize the database connection
  def __init__(self, server):
    os.makedirs('data/users', exist_ok=True)
    self._db = sqlite3.connect(f'data/users/srv{server}.db')
    query = 'CREATE TABLE IF NOT EXISTS users(id INTEGER UNIQUE, name TEXT, pronouns TEXT, special TEXT, points REAL DEFAULT 0 NOT NULL, point_role TEXT)'
    self._db.execute(query)
    query = 'CREATE TABLE IF NOT EXISTS static_vars(id INTEGER UNIQUE, point_name TEXT)'
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
  
  # Initialize Column - set all values in a column to the same thing
  def initialize_column(self, column, value, table='users'):
    query = f'UPDATE {table} SET {column} = ?'
    self._db.execute(query, (value,))
    self._db.commit()  

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
    return self._db.execute(query, (id,)).fetchone() or (None, None)
  
  # Get pronouns for all users with a specific name (or None if not in db)
  def get_pronouns_for_name(self, name):
    query = 'SELECT pronouns FROM users WHERE name = ? COLLATE NOCASE'
    results = self._db.execute(query, (name,)).fetchall()
    return [x[0] for x in results]

  # Get a user with a specific flag (or None if not in db)
  def get_special_user(self, type, field = 'special'):
    query = f'SELECT id FROM users WHERE {field} = ?'
    val = self._db.execute(query, (type,)).fetchone()
    return val[0] if val else None
  
  # Add an amount to a value, or just store the value if it doesnt exist yet
  def add_to_value(self, id, column, amount, table='users'):
    try:
      query = f'UPDATE {table} SET {column} = {column} + ? WHERE id = ?'
      self._db.execute(query, (amount, id))
    except sqlite3.Error:
      query = f'INSERT INTO {table} (id, {column}) VALUES (?, ?)'
      self._db.execute(query, (amount, id))
    self._db.commit()  

  # Get all nonzero point totals for users in the table
  def get_points(self):
    query = 'SELECT id, points FROM users WHERE points <> 0'
    return self._db.execute(query).fetchall()

# Get all names that are stored in a server's db
def get_all_names(server):
  with ServerDatabase(server) as db:
    return db.get_all_values('name')

# Get the name and pronouns of a specific server
# Returns (Name, Pronouns), and both fields can be empty
def get_name_and_pronouns(server, id):
  with ServerDatabase(server) as db:
    return db.get_name_and_pronouns(id) or (None, None)

# Get the pronouns for a specific name in a given server
# Will return a comma seperated list of all pronouns the user uses
def get_pronouns_for_name(server, name):
  with ServerDatabase(server) as db:
    return db.get_pronouns_for_name(name)
  
# Get the id of a special user, optionally in a specific server
#   flag is a special text flag
#   related_to is a message context to fetch a user list from
def get_special_user(server, flag):
  with ServerDatabase(server) as db:
    user = db.get_special_user(flag)
  return user

# Set the name of a specific user in a given server
def set_name(server, id, name):
  with ServerDatabase(server) as db:
    db.set_value(id, 'name', name)

# Set the pronouns of a specific user in a given server
def set_pronouns(server, id, pronouns):
  with ServerDatabase(server) as db:
    db.set_value(id, 'pronouns', pronouns)

