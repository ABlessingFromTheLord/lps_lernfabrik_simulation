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
KAPUTT_MACHINE_A = 10
KAPUTT_MACHINE_B = 10
KAPUTT_MACHINE_C = 10
KAPUTT_MACHINE_D = 10
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

# the factory implementation
class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, env):
        self.env = env # environment variable
        self.kaputt = False # boolean for denoting when a machine is broken # TODO: check how to optimise
        self.previously_created = "" # string to denote the previously created part
        self.next_created = " " # string to denote the next created part

    # processes
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
    def select_machines(self, machines):
        # receives an array of the machines in the factory
        # returns true if the required resources are free
        required_machines = []

        for machine in machines:
            if not machine.working:
                required_machines.append(machine)

        # TODO: check if the required machines are same as the machines available
        # TODO:: reformat into taking the shared resources


    # TODo: ruestung function; takes in previous process and
    def ruestung_zeit(self, machine):
        # returns the equipping time in minutes as integer
        if machine == machine_fz12:
            return 30

        elif (machine == machine_gz200_1) or (machine == machine_gz200_2):
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


# simulates the fulfillment of orders
def fulfill_orders(orders):
    for order in orders:
        return 0 # dummy to resolve the error


# simpy environment decleration
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.Resource(env)  # Maschine zum Säegen
machine_gz200_1 = simpy.Resource(env)  # Machine zum Drehen
machine_gz200_2 = simpy.Resource(env)  # Machine zum Drehen
machine_fz12 = simpy.Resource(env)  # Machine zum Fräsen
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