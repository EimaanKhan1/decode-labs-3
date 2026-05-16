import os
print('cwd:', os.getcwd())
for f in os.listdir('.'):
    print(f, os.path.getsize(f))
