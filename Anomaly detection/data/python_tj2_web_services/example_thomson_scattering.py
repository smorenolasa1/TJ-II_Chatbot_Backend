import tj2services

import matplotlib.pyplot as plt

r_rho = tj2services.getprof(shot=50000, signal='PerfilRho_')
r_ne = tj2services.getprof(shot=50000, signal='PerfilNe_')
r_dne = tj2services.getprof(shot=50000, signal='PerfildNe_')

x = r_rho['prof']
y = r_ne['prof']
yerr = r_dne['prof']

plt.errorbar(x, y, yerr=yerr, marker='o', lw=0, elinewidth=1)

plt.show()
