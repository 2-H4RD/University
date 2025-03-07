def qZ(x, y):
    return (x - 3 * y + 1) / (3 * x ** 2 + y ** 2 + 1)
def qSumZ(Z):
    return sum(Z)


def exchangeScheme(oldX, oldY, sortedId):
    x = [0 for i in range(4)]
    y = [0 for i in range(4)]

    x[2] = oldX[sortedId[2]]
    x[3] = oldX[sortedId[2]]

    x[0] = oldX[sortedId[0]]

    x[1] = oldX[sortedId[1]]

    y[0] = oldY[sortedId[2]]
    y[1] = oldY[sortedId[2]]

    y[2] = oldY[sortedId[0]]

    y[3] = oldY[sortedId[1]]
    return x, y
def sorting(Z):
    sortedId = sorted(range(len(Z)), key=lambda k: Z[k])
    return sortedId


def evoStep(x, y, z):
    _, minId = min((value, id) for (id, value) in enumerate(z))
    x = x[:]
    y = y[:]
    z = z[:]

    x.pop(minId)
    y.pop(minId)
    z.pop(minId)

    return x, y, z


def evoSteps(x, y, steps_num=4):
    results = []

    for i in range(steps_num):
        arrZ = [qZ(k, y[i]) for i, k in enumerate(x)]

        x, y, z = evoStep(x, y, arrZ)

        x, y = exchangeScheme(x, y, sorting(z))

        results.append([x, y, qSumZ(arrZ), arrZ])

    return x, y, results

x = [-2, -1, 0, 2]
y = [-2, 0, -1, 1]

results = evoSteps(x, y)
for i in range(len(results[2])):
    print(f'max_{i + 1}_step: {results[2][i][2]}')
qualityArrZ = []
for i in range(len(results[2])):
    qualityArrZ += results[2][i][3]

print(f'max Z: {max(qualityArrZ)}')