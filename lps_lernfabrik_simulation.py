import simpy as sp

# global variables
PARTS_MADE = 0
# dummy values
SAEGEN_ZEIT = 10
DREH_ZEIT = 10
SENK_ZEIT = 10
ASSEMBLE_ZEIT = 10
KAPUTT_ZEIT = 10
REPAIR_ZEIT = 10
PROZESS_ZEIT = 0



class Lernfabrik:
    def __init__(self, env):
        self.env = env
        self.kaputt = False


    def saegen(self):
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

