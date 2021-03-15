from core.models import Condition
from django.db.models import Q


class CollectionService:
    """
    Business logic to handle building a query from a collection of conditions
    """

    def __init__(self, instance=None):
        self.instance = instance

    def get_products_filter(self):
        """
        Put simply, this method will loop through all conditions on a
        Collection and dynamically build the filter query to find products.

        Using the Condition Model and the constant _CHOICES variable, it will
        do the following:

        Loop all conditions on the Collection:
            Find the record in the Condition._CHOICE
            Build the filter List
                {f"{tag__name}{__contains}: 'Disney'"}
        """
        query = Q()
        conditions = Condition.objects.prefetch_related('collection').filter(
            collection__id=self.instance.id
        )

        for c in conditions:
            choice = next(item for item in Condition._CHOICES
                          if item["key"] == c.field_reference)
            if choice:
                dynamic_filter = {
                    f"{choice['field']}"
                    f"{choice['choices'][c.filter_type]['match']}": c.field_val
                }
                if choice['choices'][c.filter_type]['negation']:
                    query.add(~Q(dynamic_filter), self.instance.type)
                else:
                    query.add(Q(dynamic_filter), self.instance.type)
        return query
