import django_tables2 as tables

from .utils import display_array

class ArrayBooleanColumn(tables.BooleanColumn):
     
     def _get_bool_value(self, record, value, bound_column):
         return bool(len(value) > 0)

class ArrayListColumn(tables.Column):

    def __init__(self, *args, **kwargs):
        self.display_choices = kwargs.pop('choices', None)
        super(ArrayListColumn, self).__init__(*args, **kwargs)
     
    def render(self, value):
        if self.display_choices:
             value = list(display_array(value, self.display_choices))
        return ', '.join(value)

class SpeedColumn(tables.Column):
     
     def render(self, value):
         return '{0} km/h'.format(value)