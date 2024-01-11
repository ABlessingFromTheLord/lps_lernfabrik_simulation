import simpy

# global variables
PARTS_MADE = 0

# dummy values
KAPUTT_WSK = 10
SAEGEN_ZEIT = 10  # IN MINUTES
DREH_ZEIT = 10  # IN MINUTES
SENK_ZEIT = 10  # IN MINUTES
FRAESEN_ZEIT = 30  # IN MINUTES
MONTAGE_ZEIT = 10  # IN MINUTES
KLEBEN_ZEIT = 10  # IN MINUTES
PRUEFEN_ZEIT = 10  # IN MINUTES
VERPACKEN_ZEIT = 10  # IN MINUTES
JAESPA_MZ = 0.98
GZ_200_MZ = 0.85
FZ12_MZ = 0 # TODO: get value
REPAIR_ZEIT = 10
PROZESS_ZEIT = 10
MTTR = 10
# ACTUAL PRODUCED PARTS
OBERTEIL = 0
UNTERTEIL = 0
HALTETEIL = 0
RING = 0
# ORDERS
ORDERS = []


# global helper functions
def get_operation_time(machine):
    #  returns the time that a machine(s) performs a certain operation
    if machine == machine_jaespa:
        return SAEGEN_ZEIT
    elif machine == machine_gz200:
        return DREH_ZEIT
    elif machine == machine_fz12:
        return FRAESEN_ZEIT
    elif (machine[0] == machine_arbeitsplatz) & (machine[1] == machine_gz200):
        return SENK_ZEIT


# the factory implementation
def select_machines(machines):
    # receives an array of the machines in the factory
    # returns true if the required resources are free
    required_machines = []

    for machine in machines:
        if not machine.working:
            required_machines.append(machine)

    # TODO: check if the required machines are same as the machines available
    # TODO:: reformat into taking the shared resources


class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, env, time_run):
        self.env = env  # environment variable
        self.kaputt = False  # boolean for denoting when a machine is broken # TODO: check how to optimise
        self.previously_created = ""  # string to denote the previously created part
        self.next_created = ""  # string to denote the next created part
        self.time_run = time_run  # time in which the simulation is left to run

    # operation
    def operation(self, machine):
        #  simulates an operation, it is an abstract function
        #  to know the exact operation executing, look at the time used
        #  for example, if SAEGEN_ZEIT is used then the process is saegen
        while True:
            PROZESS_ZEIT = SAEGEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(get_operation_time(machine))

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(self.get_machine_broken_time(machine))  # broken time
                yield self.env.timeout(60)  # repair time
                # TODO: change factor to 60 in simulation time, and above to 1
                self.kaputt = False

    def saegen(self):
        #  simulates the "saegen" operation
        while True:
            PROZESS_ZEIT = SAEGEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def drehen(self):
        #  simulates the "drehen" operation
        while True:
            PROZESS_ZEIT = DREH_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def fraesen(self):
        #  simulates the "fraesen" operation
        while True:
            PROZESS_ZEIT = FRAESEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def senken(self):
        #  simulates the "senken" operation
        while True:
            PROZESS_ZEIT = SENK_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def kleben(self):
        #  simulates the "kleben" operation
        while True:
            PROZESS_ZEIT = KLEBEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def montage(self):
        # simulates the "assemble" operation
        while True:
            PROZESS_ZEIT = MONTAGE_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def pruefen(self):
        # simulates the "assemble" operation
        while True:
            PROZESS_ZEIT = PRUEFEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    def verpacken(self):
        # simulates the "assemble" operation
        while True:
            PROZESS_ZEIT = VERPACKEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except simpy.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

    # Helper functions
    # TODo: ruestung function; takes in previous process and
    def get_ruestung_zeit(self, machine):
        # returns the equipping time in minutes as integer
        if machine == machine_fz12:
            return 30

        elif machine == machine_gz200:
            if (self.previously_created == "Oberteil") and (self.next_created == "Oberteil"):
                return 0
            elif (self.previously_created == "Oberteil") and (self.next_created == "Unterteil"):
                return 45
            elif (self.previously_created == "Oberteil") and (self.next_created == "Halteteil"):
                return 40
            elif (self.previously_created == "Oberteil") and (self.next_created == "Ring"):
                return 45

            elif (self.previously_created == "Unterteil") and (self.next_created == "Oberteil"):
                return 45
            elif (self.previously_created == "Unterteil") and (self.next_created == "Unterteil"):
                return 0
            elif (self.previously_created == "Unterteil") and (self.next_created == "Halteteil"):
                return 40
            elif (self.previously_created == "Unterteil") and (self.next_created == "Ring"):
                return 45

            elif (self.previously_created == "Halteteil") and (self.next_created == "Oberteil"):
                return 40
            elif (self.previously_created == "Halteteil") and (self.next_created == "Unterteil"):
                return 40
            elif (self.previously_created == "Halteteil") and (self.next_created == "Halteteil"):
                return 0
            elif (self.previously_created == "Halteteil") and (self.next_created == "Ring"):
                return 45

            elif (self.previously_created == "Ring") and (self.next_created == "Oberteil"):
                return 45
            elif (self.previously_created == "Ring") and (self.next_created == "Unterteil"):
                return 45
            elif (self.previously_created == "Ring") and (self.next_created == "Halteteil"):
                return 45
            elif (self.previously_created == "Ring") and (self.next_created == "Ring"):
                return 0

        elif machine == machine_jaespa:
            return 0

    def get_machine_broken_time(self, machine):
        # returns the time that a machine is broken
        # it is calculated by 1 - Maschinenzuverlässigkeit * total simulation time
        # this is the downtime of a certain machine, repair time is set to a minute
        if machine == machine_jaespa:
            return (1 - JAESPA_MZ) * self.time_run
        elif machine == machine_gz200:
            return (1 - GZ_200_MZ) * self.time_run
        elif machine == machine_fz12:
            return (1 - FZ12_MZ) * self.time_run


# simulates the fulfillment of orders
def fulfill_orders(orders):
    for order in orders:
        return 0 # dummy to resolve the error


# simpy environment decleration
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.Resource(env)  # Maschine zum Säegen
machine_gz200 = simpy.Resource(env)  # Machine zum Drehen
machine_fz12 = simpy.Resource(env)  # Machine zum Fräsen
machine_arbeitsplatz = simpy.Resource(env)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.Resource(env)  # Machine zum Montage

# Instantiate LPS Lernfabrik
fabric = Lernfabrik(env)

# instantiate object of Lernfabrik class
# test ruestung_zeit
fabric = Lernfabrik(env)
fabric.previously_created = "Unterteil"
fabric.next_created = "Halteteil"

print(fabric.ruestung_zeit(machine_fz12))
# end of test ruestung_zeit

# running simulation
env.run()