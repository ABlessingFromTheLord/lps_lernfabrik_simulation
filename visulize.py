import matplotlib.pyplot as plt
import csv

x = []
y = []

with open('set_up_time_growth.csv') as csvfile:
    plots = csv.reader(csvfile, delimiter=';')

    for row in plots:
        x.append(row[0])
        y.append(row[2])

plt.bar(x, y, color=(0, 0.447, 0.741), width=0.72, label="Set-up time")
plt.xlabel('Orders')
plt.ylabel('Time Units')
plt.xticks(fontsize=5.5)
plt.yticks(fontsize=6)
plt.title('Growth of set-up time with increasing order size')
plt.legend()

plt.savefig('set_up_time_growth.png')
