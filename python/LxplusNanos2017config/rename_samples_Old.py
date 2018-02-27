'''Quick macro to rename samples from old sample_nosplit.ini to be used by the new folder system'''
import os

fi = open('samples_nosplit.ini','r')
fo = open('samples_nosplit_NewDirStruct.ini','w')

for line in fi:
  if line.find("__RunIISpring15DR74") != -1 and not line.startswith('infile'):
      print 'oldline was', line
      line = line.split('__')[0]
      line += ']'
      print 'newline was', line
      fo.write(line + '\n')
  else: fo.write(line)







