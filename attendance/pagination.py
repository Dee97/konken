from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict 

class BasicPagination(pagination.PageNumberPagination):
    """
        Pagination scheme used in the Attendance List page.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10

    def get_paginated_response(self, data):
        return Response(OrderedDict([
             ('links', OrderedDict([
                ('count', self.page.paginator.count),
                ('current', self.page.number),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('total_pages', self.page.paginator.num_pages),
             ])),
             ('results', data)
         ]))

class BiggerPagination(BasicPagination):
    page_size = 40