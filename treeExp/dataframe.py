import csv
#this works!!!
class DataFrame:
  """
  we are simply going to store a list of dicts.
  This list will be written or loaded using 
  csv.DictWriter
  """
  def __init__(self,filename):            #(???????????)
    self.rows     = list()
    self.cols     = set()
    self.filename = filename

  def save(self):
    with open(self.filename, 'wb') as f:
      writer = csv.DictWriter(f,self.cols)
      # adding the header, 
      #writer.writeheader() only in 2.7

      # getting all headers
      ld = dict()
      for v in self.cols:
        ld[v]=v 
      # adding them at the top of the file
      writer.writerow(ld)

      for r in self.rows:
        writer.writerow(r)

  # go and read the file
  def load(self):
    with open(self.filename, 'rt') as f:
      reader = csv.DictReader(f)
      for row in reader:
        self.currentDict = row 
        self.rows.append(self.currentDict)

  def newRow(self):
    self.currentDict = dict()
    self.rows.append(self.currentDict)

  def getCurrentRow(self):
    return(self.currentDict)

  def __setitem__(self, item, value):
    self.cols.add(item)
    self.currentDict[item] = value
    

#d = dataframe()
#d.newRow()
#d["name"]="tibo"
#d["age"]=30
#d.newRow()
#d["name"]="sara"
#d["age"]=28
#
#d.save('test.csv')
