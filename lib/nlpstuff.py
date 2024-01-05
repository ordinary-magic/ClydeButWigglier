import sqlite3
import string
from collections import Counter
from itertools import filterfalse

# Database management class
class NlpDatabase():
  # Initialize the database connection
  def __init__(self):
    self._db = sqlite3.connect('data/nlpstuff.db')
    
  # Close the database
  def close(self):
    self._db.close()
  
  # instantiation method when used in 'with' block  
  def __enter__(self):
    return self
  
  # destruction method when used in 'with' block  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
    
  # Check if a word is a stopword
  def is_stopword(self, word):
    query = 'SELECT COUNT(*) FROM stopwords WHERE word = ?'
    result = self._db.execute(query, (word.lower(),)).fetchone()
    return result[0] > 0
    
  # Check if a word is an SAT word
  def is_satword(self, word):
    query = 'SELECT COUNT(*) FROM satwords WHERE word = ?'
    result = self._db.execute(query, (word.lower(),)).fetchone()
    return result[0] > 0

# Class to track topics for a given set of sentences
class TopicData():
  # Create the topic analyzer object for a set of sentences
  def __init__(self, sentences, nlpdb):
    self.sentences = sentences
    self.individual_topics = [determine_topics(x, nlpdb) for x in sentences]
    self.net_topics = Counter()
    for sentence_topics in self.individual_topics:
      self.net_topics += sentence_topics
    
  # Return the top n topics, and how often they were mentioned
  def top_n(self, n):
    return self.net_topics.most_common(n)
    
  # Compare the alikeness of both topic sets, returning a value from (0.0-1.0)
  def alikeness(self, other):
    # Determine what values exist in both sets
    projection = self.net_topics & other.net_topics
    
    # Sum the weights of the intersected topics
    count = 0
    for key in projection:
      count += self.net_topics[key]

    # Determine an alikeness value by comparing the total weighted topic counts
    other_count = _total(self.net_topics)
    
    if other_count > 0:
      return count / other_count
    else:
      return 0
  
  # Printable version of class really only cares about net topics
  def __str__(self):
    return "{0}".format(self.net_topics)

# Remove capitilizatioon and leading/tailing punctuation from word (eg. "Didn't," becomes "didn't")
def strip_punctuation(word):
  return word.strip(string.punctuation).lower()

# Determine the topics in a given sentence
def determine_topics(sentence, nlpdb):
  words = map(strip_punctuation, sentence.split(' '))
  topics = filterfalse(nlpdb.is_stopword, words)
  return Counter(topics)
      
# Equivalent of Counter.total() (the sum of all counts)
def _total(counter):
  return sum(dict(counter).values())