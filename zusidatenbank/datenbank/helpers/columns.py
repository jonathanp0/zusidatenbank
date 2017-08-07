import django_tables2 as tables

class ArrayBooleanColumn(tables.BooleanColumn):
     
     def _get_bool_value(self, record, value, bound_column):
         return bool(len(value) > 0)

class ArrayListColumn(tables.BooleanColumn):
     
     def render(self, value):
         return ', '.join(value)