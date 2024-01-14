import simpy

# simpy environment declaration
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.Resource(env, capacity=1)  # Maschine zum Saegen
machine_gz200 = simpy.Resource(env, capacity=1)  # Machine zum Drehen
machine_fz12 = simpy.Resource(env, capacity=1)  # Machine zum Fräsen
machine_arbeitsplatz = simpy.Resource(env, capacity=1)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.Resource(env, capacity=1)  # Machine zum Montage

# global variables
PARTS_MADE = 0

# dummy values
KAPUTT_WSK = 10
SAEGEN_ZEIT = 10 * 60  # IN MINUTES
DREH_ZEIT = 10 * 60  # IN MINUTES
SENK_ZEIT = 10 * 60  # IN MINUTES
FRAESEN_ZEIT = 10 * 60  # IN MINUTES
KLEBEN_ZEIT = 10 * 60  # IN MINUTES
MONTAGE_ZEIT = 10 * 60  # IN MINUTES
PRUEFEN_ZEIT = 10 * 60  # IN MINUTES
VERPACKEN_ZEIT = 10 * 60  # IN MINUTES
JAESPA_MZ = 0.98
GZ_200_MZ = 0.85
FZ12_MZ = 0  # TODO: get value
REPAIR_ZEIT = 10
MTTR = 10

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
def get_operation_time(machine):
    #  returns the time that a machine(s) performs a certain operation
    if machine == machine_jaespa:
        return SAEGEN_ZEIT
    elif machine == machine_gz200:
        return DREH_ZEIT
    elif machine == machine_fz12:
        return FRAESEN_ZEIT
    elif machine == machine_arbeitsplatz:
        return SENK_ZEIT
    elif machine == machine_arbeitsplatz_2:
        return KLEBEN_ZEIT + MONTAGE_ZEIT + PRUEFEN_ZEIT + VERPACKEN_ZEIT


# the factory implementation
def machines_available(machines):
    # receives an array of the machines in the factory
    # returns true if the required resources are free
    required_machines = []

    for machine in machines:
        if not machine.working:
            required_machines.append(machine)

    # TODO: check if the required machines are same as the machines available
    # TODO:: reformat into taking the shared resources
    # since we wait for a resource(machine) to be available, is this really a useful function?


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


def increment_part_count(part_name):
    #  adds the newly created part to the globally available count of its parts type
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT = OBERTEIL_COUNT + 17
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT = UNTERTEIL_COUNT + 11
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT = HALTETEIL_COUNT + 48
        case "Ring":
            global RING_COUNT
            RING_COUNT = RING_COUNT + 97


class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, sim_env):
        self.env = sim_env  # environment variable
        self.kaputt = False  # boolean for denoting when a machine is broken # TODO: check how to optimise
        self.previously_created = ""  # string to denote the previously created part
        self.next_creating = ""  # string to denote the next created part

    # operation
    def operation(self, machine):
        #  simulates an operation, it is an abstract function
        #  to know the exact operation executing, look at the time used
        #  for example, if SAEGEN_ZEIT is used then the process is saegen
        operation_zeit = get_operation_time(machine)
        request = machine.request()
        start = self.env.now
        try:
            yield request  # requesting a machine for running operation
            yield self.env.timeout(operation_zeit)  # running operation
            machine.release(request)  # releasing resource for other operations

        except simpy.Interrupt:
            self.kaputt = True
            operation_zeit -= (self.env.now - start)  # remaining time from when breakdown occurred

            # repairing
            yield self.env.timeout(self.get_machine_broken_time(machine))  # broken time
            yield self.env.timeout(60)  # repair time
            # TODO: change factor to 60 in simulation time, and above to 1
            self.kaputt = False

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

    def get_machine_broken_time(self, machine):
        # returns the time that a machine is broken TODO: fix this is broken
        # it is calculated by 1 - Maschinenzuverlässigkeit * total simulation time
        # this is the downtime of a certain machine, repair time is set to a minute
        if machine == machine_jaespa:
            return (1 - JAESPA_MZ) * self.time_run
        elif machine == machine_gz200:
            return (1 - GZ_200_MZ) * self.time_run
        elif machine == machine_fz12:
            return (1 - FZ12_MZ) * self.time_run

    def part_creation(self, part_name):
        #  runs consequent operations to create Unilokk part
        self.next_creating = part_name
        required_machines = get_machines_for_part(part_name)

        for machine in required_machines:
            equipping_time = self.get_ruestung_zeit(machine)
            yield self.env.timeout(equipping_time)  # equipping machine
            yield self.env.process(self.operation(machine))  # operating machine

        #  all machines required to produce a part have been operated
        # part is created
        increment_part_count(part_name)  # add newly created part
        self.previously_created = part_name

    def unilokk_parts_creation(self, raw_material):
        #  simulates the creation of Unilokk unit

        while raw_material > 0:
            #  basic parts creation
            for part in UNILOKK:
                yield self.env.process(self.part_creation(part))  # process to create a part
            raw_material = raw_material - 1

    def unilokk_parts_assembly(self, raw_material):
        # simulates the assembling of the Unilokk parts into Unilokk
        yield self.env.process(self.unilokk_parts_creation(raw_material))  # first create the parts

        # then assemble them into Unilokk
        while True:
            if (OBERTEIL_COUNT > 0) & (UNTERTEIL_COUNT > 0) & (HALTETEIL_COUNT > 0) & (RING_COUNT > 0):
                yield self.env.process(self.operation(machine_arbeitsplatz_2))
                global UNILOKK_COUNT
                UNILOKK_COUNT = UNILOKK_COUNT + 1


# instantiate object of Lernfabrik class
fabric = Lernfabrik(env)
env.process(fabric.unilokk_parts_assembly(ROHMATERIAL))

# running simulation
env.run(until=100000)

# analysis and results
print("OBERTEIL: ", OBERTEIL_COUNT)
print("UNTERTEIL: ", UNTERTEIL_COUNT)
print("HALTETEIL: ", HALTETEIL_COUNT)
print("RING: ", RING_COUNT)

print("created: ", UNILOKK_COUNT, " Unilokks")