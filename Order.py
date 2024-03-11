class Order:
    # a tuple that defines an order amount and its priority/delivery date
    def __init__(self, amount, delivery_date):
        self.__amount = amount
        self.__delivery_date = delivery_date

    def get_amount(self):
        return self.__amount

    def get_delivery_date(self):
        return self.__delivery_date
