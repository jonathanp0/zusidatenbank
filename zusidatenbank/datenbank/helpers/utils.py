
def display_array(input, choices):
  choicedict = dict(choices)
  print(choicedict)
  return map(choicedict.get, input)