from Order import Order


class OrderList:
    # this is how orders are submitted
    # first you receive the orders by calling receive_orders, since object is instantiated with None
    # then generate prioritized list by calling get_order_by_priority
    def __init__(self):
        self.list = None

    def receive_order(self, order_list):
        self.list = order_list

    def get_order_by_priority(self):
        delivery_dates = []
        new_list = []

        for order in self.list:
            delivery_dates.append(order.delivery_date)

        delivery_dates.sort()

        for date in delivery_dates:
            for order in self.list:
                if order.delivery_date == date:
                    new_list.append(order)
                    self.list.remove(order)
        return new_list
