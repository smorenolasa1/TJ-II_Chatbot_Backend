import tj2services

import matplotlib.pyplot as plt

r = tj2services.getdata(shot=50000, signal='ACTON275')

plt.plot(r['time'], r['data'])
plt.show()
