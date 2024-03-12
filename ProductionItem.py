class ProductionItem:
    # a tuple that defines an item in production as well as when it was produced
    # this could be an Unilokk or part of an Unilokk
    def __init__(self, name, production_time):
        self.__name = name
        self.__production_time = production_time

    # getters
    def get_name(self):
        return self.__name

    def get_production_time(self):
        return self.__production_time

    # setters
    def set_name(self, value):
        self.__name = value

    def set_production_time(self, value):
        self.__production_time = value
