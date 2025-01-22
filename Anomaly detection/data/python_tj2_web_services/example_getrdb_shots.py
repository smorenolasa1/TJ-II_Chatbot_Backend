import tj2services


r1 = tj2services.getrdb_shots(variables='CONFIGURACION', shots=49999)

print('First query:')
print(r1['info'])


print()

r2 = tj2services.getrdb_shots(variables=['NDES', 'CONFIGURACION'], shots=(50000, 50002))

print('Second query:')
print(r2['info'])
