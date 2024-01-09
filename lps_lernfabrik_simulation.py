import simpy
import simpy as sp

# global variables
PARTS_MADE = 0

# dummy values
KAPUTT_WSK = 10
SAEGEN_ZEIT = 10
DREH_ZEIT = 10
SENK_ZEIT = 10
ASSEMBLE_ZEIT = 10
KAPUTT_MACHINE_A = 10
KAPUTT_MACHINE_B = 10
KAPUTT_MACHINE_C = 10
KAPUTT_MACHINE_D = 10
REPAIR_ZEIT = 10
PROZESS_ZEIT = 10
MTTR = 10


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
        # this methods simulates the "saegen" operation
        while True:
            PROZESS_ZEIT = SAEGEN_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except sp.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

        # was sollte zurückgegeben werden?

    def drehen(self):
        # this methods simulates the "drehen" operation
        while True:
            PROZESS_ZEIT = DREH_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except sp.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

        # was sollte zurückgegeben werden?

    def senken(self):
        # this methods simulates the "senken" operation
        while True:
            PROZESS_ZEIT = SENK_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except sp.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

        # was sollte zurückgegeben werden?

    def assemble(self):
        # this methods simulates the assemble operation
        while True:
            PROZESS_ZEIT = ASSEMBLE_ZEIT
            start = self.env.now
            try:
                yield self.env.timeout(PROZESS_ZEIT)

            except sp.Interrupt:
                self.kaputt = True
                PROZESS_ZEIT -= (self.env.now - start)

                # repairing
                yield self.env.timeout(REPAIR_ZEIT)
                self.kaputt = False

        # was sollte zurückgegeben werden?

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