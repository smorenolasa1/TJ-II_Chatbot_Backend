import tj2services

r = tj2services.flux_car(config='100_44_64', x=1.7, y=0, z=0.05)

print(f'Value of the flux for (x={r["x"]}, y={r["y"]}, z={r["z"]}):', r['psi'])
