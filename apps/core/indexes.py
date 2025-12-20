from django.contrib.postgres.indexes import GinIndex


class UpperGinIndex(GinIndex):

    def create_sql(self, model, schema_editor, using='', **kwargs):
        statement = super().create_sql(model, schema_editor, using=using)
        quote_name = statement.parts['columns'].quote_name

        def upper_quoted(column):
            return f'UPPER({quote_name(column)})'
        statement.parts['columns'].quote_name = upper_quoted
        return statement