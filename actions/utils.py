import random
from datetime import datetime

def getTempFilename():
  now = datetime.now()
  return now.strftime('%Y%m%d%H%M%S') + '_' + str(random.randint(0,0xffff)) + '.tmp'
