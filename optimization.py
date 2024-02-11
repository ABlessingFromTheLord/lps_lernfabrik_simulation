from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import numpy as np

# Define constants
OBERTEIL_PRODUCTION = 17
UNTERTEIL_PRODUCTION = 11
HALTETEIL_PRODUCTION = 49
RING_PRODUCTION = 97

OBERTEIL_ORDER = 0
UNTERTEIL_ORDER = 0
HALTETEIL_ORDER = 0
RING_ORDER = 0

OBERTEIL_COUNT = 0
UNTERTEIL_COUNT = 0
HALTETEIL_COUNT = 0
RING_COUNT = 0


def set_test_values(oberteil_order, unterteil_order, halteteil_order, ring_order,
                    rem_oberteil, rem_unterteil, rem_halteteil, rem_ring):
    # sets the values for checking what machines should be executed to fulfill order
    # the rem values are set to the count values for test purposes
    global OBERTEIL_ORDER
    OBERTEIL_ORDER = oberteil_order
    global OBERTEIL_COUNT
    OBERTEIL_COUNT = rem_oberteil

    if OBERTEIL_COUNT >= OBERTEIL_ORDER:
        # fulfillment function will have enough at the end even without producing more
        OBERTEIL_ORDER = 0
    else:
        OBERTEIL_ORDER -= OBERTEIL_COUNT  # get the amount needed

    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = unterteil_order
    global UNTERTEIL_COUNT
    UNTERTEIL_COUNT = rem_unterteil

    if UNTERTEIL_COUNT >= UNTERTEIL_ORDER:
        # fulfillment function will have enough at the end even without producing more
        UNTERTEIL_ORDER = 0
    else:
        UNTERTEIL_ORDER -= UNTERTEIL_COUNT  # get the amount needed

    global HALTETEIL_ORDER
    HALTETEIL_ORDER = halteteil_order
    global HALTETEIL_COUNT
    HALTETEIL_COUNT = rem_halteteil

    if HALTETEIL_COUNT >= HALTETEIL_ORDER:
        # fulfillment function will have enough at the end even without producing more
        HALTETEIL_ORDER = 0
    else:
        HALTETEIL_ORDER -= HALTETEIL_COUNT  # get the amount needed

    global RING_ORDER
    RING_ORDER = ring_order
    global RING_COUNT
    RING_COUNT = rem_ring

    if RING_COUNT >= RING_ORDER:
        # fulfillment function will have enough at the end even without producing more
        RING_ORDER = 0
    else:
        RING_ORDER -= RING_COUNT  # get the amount needed


order = 17

set_test_values(order, order, order, order, 0, 0, 0, 0)


class JobShopScheduling(Problem):
    def __init__(self):
        super().__init__(n_var=4, n_obj=1, n_constr=0, xl=np.array([0, 0, 0, 0]),
                         xu=np.array([OBERTEIL_ORDER, UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER]))

    def _evaluate(self, x, out, *args, **kwargs):
        total_oberteil = np.zeros(len(x))
        total_unterteil = np.zeros(len(x))
        total_halteteil = np.zeros(len(x))
        total_ring = np.zeros(len(x))

        for i in range(len(x)):
            if OBERTEIL_COUNT == 0 and x[i, 0] == 0:
                total_oberteil[i] = 1
            elif x[i, 0] > 0:
                total_oberteil[i] = OBERTEIL_PRODUCTION * x[i, 0]

            if UNTERTEIL_COUNT == 0 and x[i, 1] == 0:
                total_oberteil[i] = 1
            elif x[i, 1] > 0:
                total_unterteil[i] = UNTERTEIL_PRODUCTION * x[i, 1]

            if HALTETEIL_COUNT == 0 and x[i, 2] == 0:
                total_halteteil[i] = 1
            elif x[i, 2] > 0:
                total_halteteil[i] = HALTETEIL_PRODUCTION * x[i, 2]

            if RING_COUNT == 0 and x[i, 3] == 0:
                total_ring[i] = 1
            elif x[i, 3] > 0:
                total_ring[i] = RING_PRODUCTION * x[i, 3]

        fitness = (np.abs(total_oberteil - OBERTEIL_ORDER) + np.abs(total_unterteil - UNTERTEIL_ORDER) +
                   np.abs(total_halteteil - HALTETEIL_ORDER) + np.abs(total_ring - RING_ORDER))

        out["F"] = fitness[:, None]  # Reshape to match the expected shape
        out["G"] = np.zeros((len(x), 0))  # No constraints for now


problem = JobShopScheduling()

algorithm = NSGA2(
    pop_size=100,
    n_offsprings=50,
    eliminate_duplicates=True
)

res = minimize(problem,
               algorithm,
               ('n_gen', 100),
               seed=1,
               verbose=True)

print("Best solution found: %s" % res.X)
print(round(res.X[0]))
print(round(res.X[1]))
print(round(res.X[2]))
print(round(res.X[3]))