"""Run Again locally without printing credential values."""
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import uvicorn
if __name__ == '__main__':
    uvicorn.run('app.main:app',host='127.0.0.1',port=int(os.environ.get('PORT','7860')),access_log=False)
