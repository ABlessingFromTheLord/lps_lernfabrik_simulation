import simpy
import random
import numpy

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

# part names / working strings
OBERTEIL = "Oberteil"
UNTERTEIL = "Unterteil"
HALTETEIL = "Halteteil"
RING = "Ring"

# Unilokk definition
UNILOKK = [OBERTEIL, UNTERTEIL, HALTETEIL, RING]

# parts produced
OBERTEIL_COUNT = 0
UNTERTEIL_COUNT = 0
HALTETEIL_COUNT = 0
RING_COUNT = 0

# unilokk created
UNILOKK_COUNT = 0

# rohmaterial
ROHMATERIAL = 1  # single 3000mm long rod

# orders
ORDERS = []


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


def increase_part_count(part_name):
    #  increase the respective part count after the machines for part
    #  creation have been successfully executed
    #  for a 3000mm Stange, 17 oberteil, 11 unterteil, 48 halteteil and 97
    #  Rings are created and hence they are incremented by these values
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT = OBERTEIL_COUNT + 17
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT = UNTERTEIL_COUNT + 11
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT = HALTETEIL_COUNT + 49
        case "Ring":
            global RING_COUNT
            RING_COUNT = RING_COUNT + 97


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
    else:
        return 0
    # TODO: FZ12 left, also the MZ in Ring production to be checked


class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, sim_env):
        self.process = None
        self.env = sim_env  # environment variable
        self.currently_broken = False  # boolean for denoting when a machine is broken
        self.done_part_creation = False
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
                yield self.env.timeout(5 * 60)  # TODO: adjust for real repair time
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
                return 45*60
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
            if machine != machine_arbeitsplatz or machine != machine_arbeitsplatz_2:
                break_or_not = random.random() > get_mz(machine)
                yield self.env.timeout(MTTR)  # Time between two successive machine breakdowns

                # if true then machine breaks down, else continues running
                if break_or_not:
                    with machine.request(priority=priority, preempt=preempt) as request:
                        assert isinstance(self.env.now, int), type(self.env.now)
                        yield request

                        assert isinstance(self.env.now, int), type(self.env.now)
                        if self.process is not None and not self.currently_broken:
                            # print(f"Machine {machine} broke down at {self.env.now}")
                            self.process.interrupt()
                            # yield self.env.timeout(50)
                            # print(f"Machine {machine} continued running at {self.env.now}")

    def part_creation(self, part_name):
        #  runs consequent operations to create Unilokk part
        self.next_creating = part_name
        required_machines = get_machines_for_part(part_name)

        for machine in required_machines:
            equipping_time = self.get_ruestung_zeit(machine)  # getting equipping time
            operating_time = self.get_operating_time(machine, part_name)  # getting operation time

            with machine.request(priority=1, preempt=False) as request:
                yield request
                # running operation
                yield self.env.timeout(equipping_time)  # equipping a machine
                self.process = self.env.process(self.operation(machine, operating_time))  # operating machine
                env.process(self.break_machine(machine, 2, True))  # starting breakdown function
                yield self.process

                # self.process = None

            if machine == machine_gz200:
                self.previously_created = part_name  # setting the control for get_ruestung_zeit function
                if part_name == "Ring":
                    self.done_once = not self.done_once  # setting control for get_operating_time function

        #  all machines required to produce a part have been operated
        # part is created
        increase_part_count(part_name)  # add newly created part
        print(part_name, "was created at ", self.env.now)

    def unilokk_parts_creation(self, raw_material):
        #  simulates the creation of Unilokk unit

        while raw_material > 0:
            #  basic parts creation
            for part in UNILOKK:
                yield self.env.process(self.part_creation(part))  # process to create a part
            raw_material = raw_material - 1

            global ROHMATERIAL
            ROHMATERIAL = ROHMATERIAL - 1

    def whole_process(self, raw_material):
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


def get_unilokk_parts(orders):
    # received orders as parameter and returns the total number of
    # parts needed for the entire order
    # these parts are saved in an array that is returned
    # index 0 = Oberteil, 1 = Unterteil, 2 = Halteteil, 3 = Ring
    parts = [0, 0, 0, 0]

    for order in orders:
        for part in parts:
            part += order
    return parts


def serve_orders_algorithm():
    # order fulfillment algorithm
    # empty for now
    return 0


# instantiate object of Lernfabrik class
fabric = Lernfabrik(env)
# simulates the assembling of the Unilokk parts into Unilokk
env.process(fabric.unilokk_parts_creation(ROHMATERIAL))  # creates the parts from raw materials
env.process(fabric.whole_process(ROHMATERIAL))

# running simulation

env.run(until=86400)

# analysis and results
print("OBERTEIL: ", OBERTEIL_COUNT)
print("UNTERTEIL: ", UNTERTEIL_COUNT)
print("HALTETEIL: ", HALTETEIL_COUNT)
print("RING: ", RING_COUNT)

print("created: ", UNILOKK_COUNT, " Unilokk")
print("remaining raw materials: ", ROHMATERIAL)