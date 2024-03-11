class ProductionItem:
    # a tuple that defines an item in production as well as when it was produced
    # this could be an Unilokk or part of an Unilokk
    def __init__(self, amount, production_date):
        self.__amount = amount
        self.__production_date = production_date

    def get_amount(self):
        return self.__amount

    def get_production_date(self):
        return self.__production_date
