# Python 3.4 and up
#import language_check

# Python 3.6 and up
import language_tool_python

class SpellChecker:
  def __init__(self):
    # Pyton 3.4 and up
    #self.spellchecker = language_check.LanguageTool('en-US') # Also checks Grammar
    
    # Python 3.6
    self.spellchecker = language_tool_python.LanguageTool('en-US') # Also checks Grammar
    
  # Get a list of spelling/grammar errors for the input text
  def get_issues(self, text):
    return self.spellchecker.check(text)