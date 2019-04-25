from rest_framework import routers, serializers, viewsets
from .models import Metric
from django.db.models import Sum, FloatField, F

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        fieldsStr = self.context['request'].query_params.get('fields')
        if fieldsStr:
            fields = fieldsStr.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)    


class MetricSerialiser(DynamicFieldsModelSerializer, serializers.HyperlinkedModelSerializer):
    cpi = serializers.SerializerMethodField('getCPI')

    def getCPI(self, metric):
        return metric['cpi']
    class Meta:
        model = Metric
        fields = ('country', 'date', 'os', 'channel', 'impressions', 'clicks', 'revenue','cpi', 'spend', 'installs')


class FilterObj(object):
    date_from = ""
    date_to = ""
    country = ""
    os = ""
    channel = ""

    # The class "constructor" - It's actually an initializer 
    def __init__(self, start_date, end_date, country, os, channel):
        self.date_from = start_date
        self.date_to = end_date
        self.country = country
        self.os = os
        self.channel = channel

class MetricViewSet(viewsets.ModelViewSet):
    serializer_class = MetricSerialiser
    


    def filterQuerySet(self, filterObj, queryset):
        """
            Search By date
        """
        if filterObj.date_from is not None and filterObj.date_to is not None:
            queryset = queryset.filter(date__range=[filterObj.date_from, filterObj.date_to])
        elif filterObj.date_from is not None:    
            queryset = queryset.filter(date__gte=filterObj.date_from)
        elif filterObj.date_to is not None:
            queryset = queryset.filter(date__lte=filterObj.date_to)      
        """
            Search By Channel
        """
        if filterObj.channel is not None:
            queryset = queryset.filter(channel=filterObj.channel)

        """
            Search By Channel
        """
        if filterObj.os is not None:
            queryset = queryset.filter(os=filterObj.os)


        """
            Search By Country
        """
        if filterObj.country is not None:
            queryset = queryset.filter(country=filterObj.country)    
     
        return queryset

    def get_queryset(self):
        queryset = Metric.objects.all()
        fields = self.request.query_params.get('sums', None)
        groupby = self.request.query_params.get('groupby', None)
        sort_value = self.request.query_params.get('sort_value', None)
        sort_direction = self.request.query_params.get('sort_direction', None)
        country = self.request.query_params.get('country', None)
        os = self.request.query_params.get('os', None)
        channel = self.request.query_params.get('channel', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        filterObj = FilterObj(date_from, date_to, country, os, channel)
       
        """
            perform filter operations
        """
        queryset = self.filterQuerySet(filterObj, queryset)
       
        """
            Group by fields
        """
        if groupby is not None:
            groupby = groupby.split(',')
            allowed = set(groupby)
            queryset = queryset.values(*allowed)

        """
            Sum by by fields
        """

        if fields is not None:
            fields = fields.split(',')
            allowed = set(fields)
            # existing = set(self.fields.keys())
            for field_name in allowed:
                # they already aggregtaed in the cpi calculation
                if(field_name != "installs" and field_name != "spend"):
                    queryset = queryset.annotate(**{field_name: Sum((field_name))})

        queryset = queryset.annotate(spend=Sum(
                'spend',
                output_field=FloatField()),
                installs=Sum(
                'installs',output_field=FloatField()),
            ).annotate(
                cpi=F('spend') / F('installs')
            )
        """
            Sort by and sort direction
        """
        if sort_value is not None:
            if sort_direction is None or sort_direction == "desc":
                queryset = queryset.order_by('-' +sort_value)
            else:
               queryset = queryset.order_by(sort_value)  
       
        print(queryset.query)
        return queryset