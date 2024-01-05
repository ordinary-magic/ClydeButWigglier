from lib.nlpstuff import *
from lib.spellchecker import SpellChecker
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class PostRater():
  def __init__(self):
    self.spellchecker = SpellChecker()
    self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    # Target values for various scoring functions
    self.target_length = 20.0
    self.target_vocab_amt = 10
    self.target_vocab_pct = 0.20
    self.spelling_penalty = 0.10
    self.topicality_tgt = 0.50
  
  def get_rating(self, text, history):
    return get_point_report(self.calculate_scores(text, history)[0])
    
  def get_detailed_rating(self, text, history):
    return get_point_breakdown(self.calculate_scores(text, history))
  
  # Determine and return the score of a peice of text
  def calculate_scores(self, text, chat_history):
    # Determine the grades
      length      = self.get_word_score(text)
      grammar     = self.get_grammar_score(text)
      sentiment   = self.get_sentiment_score(text)

      # Need to instantiate a thread specific sqlite database
      with NlpDatabase() as nlpdb:
        vocab       = self.get_vocab_score(text, nlpdb)
        topicality  = self.get_topical_score(text, chat_history, nlpdb)
      
      scores = (.10 * length, .20 * grammar, .20 * vocab, .20 * sentiment, .30 * topicality)
      
      return (sum(scores),) + scores
  
  # Score the length of the text
  def get_word_score(self, text):
    return min(len(text.split(' ')) / self.target_length, 1.0)
    
  # Score the gramatical correctness of the text
  def get_grammar_score(self, text):
    issues = self.spellchecker.get_issues(text)
  
    # Deduct points for every incorrect thing
    return max(0, 1.0 - (len(issues) * self.spelling_penalty))
    
  # Score the vocabulary usage of the text
  def get_vocab_score(self, text, nlpdb):
    words = [strip_punctuation(x) for x in text.split(' ')]
    sat_words = list(filter(nlpdb.is_satword, words))
    
    # Compare vs the target percentage and amount, and average the results
    percentage_score = min((len(sat_words) / len(words)) / self.target_vocab_pct, 1.0)
    amt_score = min(len(set(sat_words)) / self.target_vocab_amt, 1.0)
    return (percentage_score + amt_score) / 2.0
    
    
  # Score the positivity of the text
  def get_sentiment_score(self, text):
    return self.sentiment_analyzer.polarity_scores(text)['pos']
    
  # Score how on topic the text was compared to the recent chat history
  def get_topical_score(self, text, chat_history, nlpdb):
    chat_topics = TopicData(chat_history, nlpdb)
    post_topics = TopicData([text], nlpdb)
    
    # Get the alikeness, and then weight it against the target value
    alikeness = chat_topics.alikeness(post_topics)
    return min(alikeness / self.topicality_tgt, 1.0)
  
def get_point_report(score):
  points = int(score*10000)
  return 'This post is worth {0} points.{1}'.format(points, get_bonus_text(points))
  
  
def get_bonus_text(points):
  if   points == 10000: return "A perfect score!!!!"
  elif points >= 9000: return " THATS INCREDIBLE!"
  elif points >= 7500: return " Amazing!"
  elif points >= 5000: return " Not bad!"
  elif points == 420: return " Dank."
  elif points == 69: return " OwO"
  elif points == 0: return " Lmao"
  elif points < 1000: return " Please try a little harder next time"
  else: return ""
  
def get_point_breakdown(grades):
  return 'Length: {1}\nGrammar: {2}\nVocab: {3}\nSentiment: {4}\nTopicality {5}\n**Total: {0}**'.format(*[int(x*10000) for x in grades])
  
  