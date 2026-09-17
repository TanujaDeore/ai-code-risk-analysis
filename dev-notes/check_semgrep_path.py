import shutil
import subprocess

path = shutil.which('semgrep')
print('Python can find semgrep at:', path)

result = subprocess.run(['where', 'semgrep'], capture_output=True, text=True, shell=True)
print('\n"where semgrep" says:')
print(result.stdout)
