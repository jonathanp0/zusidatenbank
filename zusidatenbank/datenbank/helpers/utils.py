
def display_array(input, choices):
  choicedict = dict(choices)
  return map(choicedict.get, input)