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

# simpy environment decleration
env = simpy.Environment()

# machines as simpy resources
machine_jaespa = simpy.Resource(env)
machine_gz200_1 = simpy.Resource(env)
machine_gz200_2 = simpy.Resource(env)
machine_fz12 = simpy.Resource(env)
machine_arbeitsplatz_2 = simpy.Resource(env)


# the factory implementation
class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, env):
        self.env = env
        self.kaputt = False

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


    # TODo: ruestung function; takes in previous process and
    # returns the time needed till machines are equipped


# running simulation
env.run()