import math
import simpy
import numpy
from Job import Job
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import numpy as np
# disabling redundant warning
from pymoo.config import Config

Config.warnings['not_compiled'] = False

# simpy environment declaration
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.PreemptiveResource(env, capacity=1)  # Maschine zum Saegen
machine_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Drehen
machine_fz12 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Fräsen
machine_arbeitsplatz = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage

# global variables
PARTS_MADE = 0

# breaking probability
KAPUTT_WSK = 10
JAESPA_MZ = 0.98
GZ_200_MZ = 0.85
FZ12_MZ = 0  # TODO: get value
BROKEN_ZEIT = 60
REPAIR_ZEIT = 60
MTTR = 2 * 60  # TODO: setting it to one minute causes terminated processes to be interrupted

# machines for part creation
OBERTEIL_MACHINES = [machine_jaespa, machine_gz200, machine_fz12]
UNTERTEIL_MACHINES = [machine_jaespa, machine_gz200]
HALTETEIL_MACHINES = [machine_jaespa, machine_gz200]
RING_MACHINES = [machine_jaespa, machine_gz200, machine_arbeitsplatz, machine_gz200]

# instantiating jobs
# Oberteil creation jobs
Oberteil_Saegen = Job("Oberteil_Saegen", 34)
Oberteil_Drehen = Job("Oberteil_Drehen", 287)
Oberteil_Fraesen = Job("Oberteil_Fraesen", 376)
Oberteil_Saegen.set_job_before(None)
Oberteil_Saegen.set_job_after(Oberteil_Drehen)
Oberteil_Drehen.set_job_before(Oberteil_Saegen)
Oberteil_Drehen.set_job_after(Oberteil_Fraesen)
Oberteil_Fraesen.set_job_before(Oberteil_Drehen)
Oberteil_Fraesen.set_job_after(None)
Oberteil_Jobs = [Oberteil_Saegen, Oberteil_Saegen, Oberteil_Fraesen]

# Unterteil creation jobs
Unterteil_Saegen = Job("Unterteil_Saegen", 20)
Unterteil_Drehen = Job("Unterteil_Drehen", 247)
Unterteil_Saegen.set_job_before(None)
Unterteil_Saegen.set_job_after(Unterteil_Drehen)
Unterteil_Drehen.set_job_before(Unterteil_Drehen)
Unterteil_Drehen.set_job_after(None)
Unterteil_Jobs = [Unterteil_Saegen, Unterteil_Drehen]

# Halteteil creation jobs
Halteteil_Saegen = Job("Halteteil_Saegen", 4)
Halteteil_Drehen = Job("Halteteil_Drehen", 255)
Halteteil_Saegen.set_job_before(None)
Halteteil_Saegen.set_job_after(Halteteil_Drehen)
Halteteil_Drehen.set_job_before(Halteteil_Saegen)
Halteteil_Drehen.set_job_after(None)
Halteteil_Jobs = [Halteteil_Saegen, Halteteil_Drehen]

# Ring creation jobs
Ring_Saegen = Job("Ring_Saegen", 3)
Ring_Drehen = Job("Ring_Drehen", 185)
Ring_Senken_1 = Job("Ring_Senken_1", 10)
Ring_Senken_2 = Job("Ring_Senken_2", 10)
Ring_Saegen.set_job_before(None)
Ring_Saegen.set_job_after(Ring_Drehen)
Ring_Drehen.set_job_before(Ring_Saegen)
Ring_Drehen.set_job_after(Ring_Senken_1)
Ring_Senken_1.set_job_before(Ring_Drehen)
Ring_Senken_1.set_job_after(Ring_Senken_2)
Ring_Senken_2.set_job_before(Ring_Senken_1)
Ring_Senken_2.set_job_after(None)
Ring_Jobs = [Ring_Saegen, Ring_Drehen, Ring_Senken_1, Ring_Senken_2]

# Finishing jobs
Fertigstellung = Job("Kleben_Montage_Pruefen_Verpacken", 180)
Finishing_Jobs = [Fertigstellung]

# part names / working strings
OBERTEIL = "Oberteil"
UNTERTEIL = "Unterteil"
HALTETEIL = "Halteteil"
RING = "Ring"

# Unilokk definition
UNILOKK = [OBERTEIL, UNTERTEIL, HALTETEIL, RING]

# optimization parameters
OBERTEIL_PRODUCTION = 17
UNTERTEIL_PRODUCTION = 11
HALTETEIL_PRODUCTION = 49
RING_PRODUCTION = 97

OBERTEIL_ORDER = 0
UNTERTEIL_ORDER = 0
HALTETEIL_ORDER = 0
RING_ORDER = 0

# parts produced
OBERTEIL_COUNT = 0
UNTERTEIL_COUNT = 0
HALTETEIL_COUNT = 0
RING_COUNT = 0

# ruestungszeit
RUESTUNGS_ZEIT = 0

# unilokk created
UNILOKK_COUNT = 0


# global helper functions
def get_machines_for_part(part_name):
    #  returns the machines required to create a certain part of Unilokk
    match part_name:
        case "Oberteil":
            return OBERTEIL_MACHINES
        case "Unterteil":
            return UNTERTEIL_MACHINES
        case "Halteteil":
            return HALTETEIL_MACHINES
        case "Ring":
            return RING_MACHINES


def increase_part_count(part_name, output):
    #  increase the respective part count after the machines for part by amount "output"
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT += output
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT += output
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT += output
        case "Ring":
            global RING_COUNT
            RING_COUNT += output


def decrease_part_count(part_name):
    #  decrease respective part count after a partis used for order fulfillment
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT = OBERTEIL_COUNT - 1
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT = UNTERTEIL_COUNT - 1
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT = HALTETEIL_COUNT - 1
        case "Ring":
            global RING_COUNT
            RING_COUNT = RING_COUNT - 1


def get_mz(machine):
    # returns the Machinezuverlässigkeit for a machine while producing a certain part
    if machine == machine_jaespa:
        return 0.98
    elif machine == machine_gz200:
        return 0.85
    elif machine == machine_fz12:
        return 0.98
    elif machine == machine_arbeitsplatz or machine == machine_arbeitsplatz_2:
        return 1
    else:
        return 1
    # TODO: FZ12 left, also the MZ in Ring production to be checked


def get_quality_grade(machine):
    # returns the quality grade of parts created by certain machine
    # i.e if quality grade is 98%, it means 98% of material produced are usable to the next stage
    # 2% are thrown away
    if machine == machine_jaespa:
        return 1
    elif machine == machine_gz200:
        return 0.98
    elif machine == machine_fz12:
        return 0.95
    elif machine == machine_arbeitsplatz_2:
        return 0.85
    else:
        return 1


def orders_fulfilled(orders, unilokk):
    return (unilokk / orders) * 100


def get_output_per_part(part_name):
    # returns amount of parts created from a 3000mm long rod of raw material
    match part_name:
        case "Oberteil":
            return 17
        case "Unterteil":
            return 11
        case "Halteteil":
            return 49
        case "Ring":
            return 97


def get_parts_by_sequence(sequence):
    # returns part names in the amount their machines are needed to be executed
    # to get a batch that can fulfill an order
    to_return = []

    for i in range(len(sequence)):
        match i:
            case 0:
                while sequence[i] > 0:
                    to_return.append("Oberteil")
                    sequence[i] -= 1
            case 1:
                while sequence[i] > 0:
                    to_return.append("Unterteil")
                    sequence[i] -= 1
            case 2:
                while sequence[i] > 0:
                    to_return.append("Halteteil")
                    sequence[i] -= 1
            case 3:
                while sequence[i] > 0:
                    to_return.append("Ring")
                    sequence[i] -= 1
    return to_return


def submit_order(orders):
    # receives orders and sets the universal variables OBERTEIL_ORDER,
    # UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER
    total_parts = 0

    for order in orders:
        total_parts += order

    global OBERTEIL_ORDER
    OBERTEIL_ORDER = total_parts
    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = total_parts
    global HALTETEIL_ORDER
    HALTETEIL_ORDER = total_parts
    global RING_ORDER
    RING_ORDER = total_parts


def adjust(genes):
    # if the machine capacity greater than order, genes are always zero
    # this method adjusts that to make sure if that's the case, then the
    # machine is run at least once
    # other use case of the method is to round up
    copy = []
    for i in range(len(genes)):
        if 0 < genes[i] < 1:
            genes[i] = 1
            copy.append(int(genes[i]))
        else:
            genes[i] = math.ceil(genes[i])
            copy.append(int(genes[i]))
    return copy


# optimization
# submit order

# submit order and run algorithm
submit_order([1, 3, 4, 2, 6, 1])  # each index is a customer number


# optimization problem definition
class ExecutionAmounts(Problem):
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


# instantiating problem and algorithm
problem = ExecutionAmounts()
algorithm = NSGA2(
    pop_size=100,
    n_offsprings=50,
    eliminate_duplicates=True
)

# executing the optimization algorithm
# returns the sequence to execute machines to fulfill current order
res = minimize(problem,
               algorithm,
               ('n_gen', 100),
               seed=1,
               verbose=False)

# result for execution sequence
EXECUTION_SEQUENCE = adjust(res.X)
EXECUTION_SEQUENCE_IN_PARTS = get_parts_by_sequence(EXECUTION_SEQUENCE)

print("Best solution found: %s" % EXECUTION_SEQUENCE_IN_PARTS)


# simulation class
class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, sim_env):
        self.process = None
        self.env = sim_env  # environment variable
        self.currently_broken = False  # boolean for denoting when a machine is broken
        self.previously_created = ""  # string to denote the previously created part
        self.next_creating = ""  # string to denote the next created part
        self.done_once = False  # if true means the machine GZ200 in Ring creation has already been operated once

    # operation
    def operation(self, machine, operating_time):
        #  simulates an operation, it is an abstract function

        # operating machine after equipping
        while operating_time:
            start = self.env.now
            try:
                print(f"execution time is {operating_time} seconds, started execution at {self.env.now}")
                yield self.env.timeout(operating_time)  # running operation
                self.process = None
                operating_time = 0
                print(f"finish time is {self.env.now} seconds")

            except simpy.Interrupt as interrupt:
                self.currently_broken = True

                print(f"Machine{machine} got PREEMPTED at {self.env.now}")  # TODO: comment out after proving
                operating_time -= (self.env.now - start)  # remaining time from when breakdown occurred

                # producing random repair time in the gaussian distribution with mean 60 seconds and standard
                # deviation of 30 seconds
                repair_time = abs(numpy.floor(numpy.random.normal(60, 30, 1).item()).astype(int).item())
                yield self.env.timeout(repair_time)
                print(f"remaining time for operation {operating_time} seconds, continues at {self.env.now}")

                self.currently_broken = False

    # Helper functions
    def get_ruestung_zeit(self, machine):
        # returns the equipping time in minutes as integer
        if machine == machine_fz12:
            return 30 * 60

        elif machine == machine_gz200:
            if self.previously_created == "":
                return 0
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Oberteil"):
                return 0
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Unterteil"):
                return 45 * 60
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Halteteil"):
                return 40 * 60
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Unterteil") and (self.next_creating == "Oberteil"):
                return 45 * 60
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Unterteil"):
                return 0
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Halteteil"):
                return 40 * 60
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Halteteil") and (self.next_creating == "Oberteil"):
                return 40 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Unterteil"):
                return 40 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Halteteil"):
                return 0 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Ring") and (self.next_creating == "Oberteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Unterteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Halteteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Ring"):
                return 0

        elif machine == machine_jaespa:
            return 0

        elif (machine == machine_arbeitsplatz) or (machine == machine_arbeitsplatz_2):
            return 0

    def get_operating_time(self, machine, part_name):
        #  returns the operating time for a certain machine on a specific Unilokk part
        match part_name:
            case "Oberteil":
                if machine == machine_jaespa:
                    return 34
                elif machine == machine_gz200:
                    return 287
                elif machine == machine_fz12:
                    return 376

            case "Unterteil":
                if machine == machine_jaespa:
                    return 20
                elif machine == machine_gz200:
                    return 247

            case "Halteteil":
                if machine == machine_jaespa:
                    return 4
                elif machine == machine_gz200:
                    return 255

            case "Ring":
                if machine == machine_jaespa:
                    return 3
                elif machine == machine_gz200:
                    match self.done_once:
                        case True:
                            return 10
                        case False:
                            return 185
                elif machine == machine_arbeitsplatz:
                    return 10

    def break_machine(self, machine, priority, preempt):
        #  breaks down a certain machine based on it's break probability or Maschinenzuverlässigkeit
        while True:
            break_or_not = numpy.around(numpy.random.uniform(0, 1), 2) < (1 - get_mz(machine))
            yield self.env.timeout(MTTR)  # Time between two successive machine breakdowns

            # if true then machine breaks down, else continues running
            if break_or_not:
                with machine.request(priority=priority, preempt=preempt) as request:
                    assert isinstance(self.env.now, int), type(self.env.now)
                    yield request
                    assert isinstance(self.env.now, int), type(self.env.now)

                    if self.process is not None and not self.currently_broken:
                        self.process.interrupt()

    def part_creation(self, part_name):
        #  runs consequent operations to create Unilokk part
        self.next_creating = part_name
        required_machines = get_machines_for_part(part_name)
        output = get_output_per_part(part_name)  # expected yield of this part from raw material

        for machine in required_machines:
            equipping_time = self.get_ruestung_zeit(machine)  # getting equipping time
            operating_time = self.get_operating_time(machine, part_name)  # getting operation time
            global RUESTUNGS_ZEIT
            RUESTUNGS_ZEIT += equipping_time

            with machine.request(priority=1, preempt=False) as request:
                yield request
                # running operation
                yield self.env.timeout(equipping_time)  # equipping a machine
                self.process = self.env.process(self.operation(machine, operating_time))  # operating machine
                env.process(self.break_machine(machine, 2, True))  # starting breakdown function
                yield self.process

                self.process = None

            if machine == machine_gz200:
                self.previously_created = part_name  # setting the control for get_ruestung_zeit function
                if part_name == "Ring":
                    self.done_once = not self.done_once  # setting control for get_operating_time function

            output *= get_quality_grade(machine)

        #  all machines required to produce a part have been operated
        # part is created
        increase_part_count(part_name, math.floor(output))  # add newly created part
        print(math.floor(output), part_name, "(s) was created at ", self.env.now)

    def unilokk_parts_creation_for_order(self, sequence):
        #  simulates the creation of Unilokk unit

        #  basic parts creation
        for part in sequence:
            yield self.env.process(self.part_creation(part))  # process to create a part

    def whole_process(self, execution_sequence):
        # simulates the assembling of the Unilokk parts into Unilokk
        # each raw material is assumed to be a 300cm long rod, so 3 means 3 300cm rods
        # execution sequence is the sequence of part creations necessary for creating
        # parts that will fulfill orders, determined by the optimization algorithm above
        yield env.process(fabric.unilokk_parts_creation_for_order(
            execution_sequence))  # creates the parts from raw materials

        i = 1
        # then assemble them into Unilokk
        while True:
            if OBERTEIL_COUNT > 0 and UNTERTEIL_COUNT > 0 and HALTETEIL_COUNT > 0 and RING_COUNT > 0:
                self.process = self.env.process(self.operation(machine_arbeitsplatz_2, 180))
                yield self.process  # assembling parts to create Unilokk

                # decrement for the parts used above to create a whole Unilokk
                decrease_part_count(OBERTEIL)
                decrease_part_count(UNTERTEIL)
                decrease_part_count(HALTETEIL)
                decrease_part_count(RING)

                # increase Unilokk count for the one that is created
                global UNILOKK_COUNT
                UNILOKK_COUNT = UNILOKK_COUNT + 1

                print("unilokk ", i, " was created at ", self.env.now)
                i = i + 1

            else:
                break


# instantiate object of Lernfabrik class
SIM_TIME = 86400
fabric = Lernfabrik(env)
env.process(fabric.whole_process(EXECUTION_SEQUENCE_IN_PARTS))

env.run(until=SIM_TIME)

# analysis and results
print("\nOBERTEIL: ", OBERTEIL_COUNT)
print("UNTERTEIL: ", UNTERTEIL_COUNT)
print("HALTETEIL: ", HALTETEIL_COUNT)
print("RING: ", RING_COUNT, "\n")

print("produced: ", UNILOKK_COUNT, " Unilokk")
print("orders fulfilled: ", orders_fulfilled(OBERTEIL_ORDER, UNILOKK_COUNT), "%")
print("unilokk remaining: ", UNILOKK_COUNT - OBERTEIL_ORDER)
print("total ruestungszeit: ", RUESTUNGS_ZEIT)
