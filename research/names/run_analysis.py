import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


THIS_DIR = Path(__file__).parent
RESEARCH_DIR = THIS_DIR.parent
PROJECT_DIR = RESEARCH_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'


print('Loading data...')
with open(DATA_DIR / 'primary.csv', 'r') as f:
    names = [l for l in map(str.strip, f) if len(l) > 0]
print('Loaded', len(names), 'names')


print('Calculating name lengths...')
name_lengths = [len(n) for n in names]


print('Calculating statistics...')
with open(THIS_DIR / 'stats.txt', 'w') as f:
    f.write(f'Mean: {np.mean(name_lengths):.2f}\n')
    f.write(f'Median: {np.median(name_lengths)}\n')
    f.write(f'Std: {np.std(name_lengths):.2f}\n')
    f.write(f'Min: {np.min(name_lengths)}\n')
    f.write(f'Max: {np.max(name_lengths)}\n')

    for q in [90, 95, 99, 99.9, 99.99]:
        f.write(f'Q{q}: {np.percentile(name_lengths, q)}\n')


print('Making plots...')
plt.boxplot(name_lengths)
plt.savefig(THIS_DIR / 'box.png')
plt.close()
plt.hist(name_lengths, bins=np.arange(0, 100, 1))
plt.savefig(THIS_DIR / 'hist.png')


print('Done')
