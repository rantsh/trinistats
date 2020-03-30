from django.shortcuts import render
from django.http import HttpResponse
from random import randint
from django.views.generic import TemplateView
from chartjs.views.lines import BaseLineChartView
from covid19 import models
from django.views.generic import ListView
import django_tables2 as tables
from dateutil.parser import parse
import json
from django.core import serializers
from django.http.response import JsonResponse
import logging
from django import forms
from django.db.models import F
from datetime import datetime
import dateutil
import traceback
from _datetime import timedelta
import pytz

class Covid19CasesTable(tables.Table):
    class Meta:
        model = models.Covid19Cases
        attrs = {"class":"djangotables"}
        fields = ('date','numtested','numpositive','numdeaths','numrecovered')
    
#CONSTANTS
alertmessage = "Sorry! An error was encountered while processing your request."

# Global variables?
logger = logging.getLogger(__name__)

# Create functions used by the views here

# Create your views here.
def cases(request):
    try:
        errors = ""
        logger.info("Cases page was called")
        recordedcases = models.Covid19Cases.objects.all()
        # Check if our request contains our GET variables
        if request.method == 'GET' and all(x in request.GET for x in ['startdate','enddate']):
            # Validate all input fields
            startdate = parse(request.GET.get('startdate'))
            if not startdate:
                errors += "Please enter a valid value for your start date."
            enddate = parse(request.GET.get('enddate'))
            if not enddate:
                errors += "Please enter a valid value for your end date."
            # Store values for all fields to repopulate the form
            enteredstartdate = startdate.strftime('%Y-%m-%d')
            enteredenddate = enddate.strftime('%Y-%m-%d')
            # Raise an error if the start date is after the end date
            if startdate > enddate:
                errors += "Your starting date must be before your ending date. Please recheck."
        else:
            logger.info("All required GET parameters were not found")
            # Put some default values into our form.
            # These will be overridden later on if the user has submitted input data
            enteredstartdate = (datetime.now()+dateutil.relativedelta.relativedelta(months=-1)).strftime('%Y-%m-%d')
            enteredenddate = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        if request.GET.get('sort'):
            orderby=request.GET.get('sort')
        else:
            orderby = '-date'
        if request.GET.get('selectedcasetype'):
            selectedcasetype = request.GET.get('selectedcasetype')
        else:
            selectedcasetype = 'numpositive'
        selectedfieldverbosename = models.Covid19Cases._meta.get_field(selectedcasetype).verbose_name
        # Fetch the records
        selectedrecords = models.Covid19Cases.objects.filter(date__gt=enteredstartdate).filter(date__lt=enteredenddate).values('date','numtested','numpositive','numdeaths','numrecovered').order_by('date')
        # Set up our table
        tabledata = Covid19CasesTable(selectedrecords, order_by=orderby)
        tabledata.paginate(page=request.GET.get("page", 1), per_page=10)
        # Set up our graph
        graphlabels = [obj['date'] for obj in selectedrecords]
        graphdataset = []
        # Add the composite totals
        graphdict = dict(data = [obj[selectedcasetype] for obj in selectedrecords],
                         borderColor = 'rgb(0, 0, 0)',
                         backgroundColor = 'rgb(255, 0, 0)',
                         label = selectedfieldverbosename)
        graphdataset.append(graphdict)
        # Set up the case type options for the dropdown select
        validcasetypes = [models.Covid19Cases._meta.get_field('numtested'),
                          models.Covid19Cases._meta.get_field('numpositive'),
                          models.Covid19Cases._meta.get_field('numdeaths'),
                          models.Covid19Cases._meta.get_field('numrecovered')]
    except Exception as ex:
        errors = alertmessage+str(ex)
        logging.critical(traceback.format_exc())
        logger.error(errors)    
    # Now add our context data and return a response
    context = {
        'errors':errors,
        'validcasetypes':validcasetypes,
        'selectedcasetypestr':selectedcasetype,
        'table':tabledata,
        'enteredstartdate':enteredstartdate,
        'enteredenddate':enteredenddate,
        'graphlabels':graphlabels,
        'graphdataset':graphdataset,
    }
    return render(request, "covid19/base_cases.html", context)