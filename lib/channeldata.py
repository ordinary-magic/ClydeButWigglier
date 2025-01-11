import sqlite3
import os

class ChannelDatabase():
  # Initialize the database connection
  def __init__(self, channel):
    os.makedirs('data/users', exist_ok=True)
    self._db = sqlite3.connect(f'data/users/ch{channel}.db')
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

  # Get a given field from the table for a given user id
  def get_value(self, id, column, table):
    query = f'SELECT {column} FROM {table} WHERE id = ?'
    val = self._db.execute(query, (id,)).fetchone()
    return val[0] if val else None
  
  # Set a given field to the specified value for the input user id.
  #   Will create a new entry if needed
  def set_value(self, id, column, value, table):
    try:
      query = f'INSERT INTO {table} (id, {column}) VALUES (?, ?)'
      self._db.execute(query, (id, value))
    except sqlite3.Error:
      query = f'UPDATE {table} SET {column} = ? WHERE id = ?'
      self._db.execute(query, (value, id))
    self._db.commit()  

# Get the prompt for a channel in a server
# Will return the current prompt, or None
def get_prompt(server, channel):
  with ChannelDatabase(server) as db:
    return db.get_value(channel, 'prompt', 'prompts')
  
# Get the context amount for a channel in a server
# Will return the current context, or None if the row doesnt exist yet
def get_context(server, channel):
  with ChannelDatabase(server) as db:
    return db.get_value(channel, 'context', 'prompts')

# Set the prompt for a channel in a server
def set_prompt(server, channel, prompt):
  with ChannelDatabase(server) as db:
    db.set_value(channel, 'prompt', prompt, 'prompts')

# Set the context amount for a channel in a server
def set_context(server, channel, context):
  with ChannelDatabase(server) as db:
    if context >= 0:
      db.set_value(channel, 'context', context, 'prompts')
