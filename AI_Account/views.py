import requests
from django.shortcuts import render
# Django Libraries
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404
from django.views.decorators.csrf import csrf_exempt
# Rest framework import
import json
import langid
import langdetect as lang_det
from langdetect import DetectorFactory
from collections import Counter
import os
from django.views import View
from django.http import HttpResponse, JsonResponse
from .sansbury_pdf import sansbury_main
from .woolworths_pdf import woolworths_main
from .magnum_pdf import magnum_main
from .mondelez_docx import mondelez_main
from .kelloggs_excel import kelloggs_main
from .fontem_excel import fontem_main

class ai_hub(View):
    account, files, pages, sheets, location = None, None, None, None, None
    def get(self,request) :
        final_output = {}
        self.account = request.GET.get('account', None)
        self.files = request.GET.getlist('file', None)
        self.sheets = request.GET.getlist('sheet', None)
        self.pages = request.GET.getlist('pages', None)
        self.location = request.GET.get('location', None)
        excel_count, pdf_count = 0, 0
        print(self.files)
        for index, file in enumerate(self.files):
            output_response = {}
            doc_format = os.path.splitext(file)[1].lower()
            if doc_format == ".pdf":
                output_response = self.pdf_processing(file, self.pages[pdf_count])
                pdf_count = pdf_count + 1
            if doc_format == ".docx":
                output_response = self.docx_processing(file)
            if doc_format in (".xlsx", ".xlsm", ".xls"):
                output_response = self.excel_processing(file,self.sheets[excel_count])
                excel_count = excel_count + 1
            final_output[file] = output_response
        return JsonResponse(final_output)

    def pdf_processing(self, file, pages):
        pdf_accounts = {'sansbury':sansbury_main, 'woolworths':woolworths_main, 'magnum':magnum_main}
        try:
            function = pdf_accounts[self.account.lower()]
        except:
            raise NotImplementedError(F"This {self.account} account is not yet implemented in single url functionality")
        return function(file, pages)

    def excel_processing(self, file, sheets):
        excel_accounts = {'kelloggs':kelloggs_main, 'fontem':fontem_main}
        try:
            function = excel_accounts[self.account.lower()]
        except:
            raise NotImplementedError(F"This {self.account} account is not yet implemented in single url functionality")
        return function(file, sheets)

    def docx_processing(self,file):
        docx_accounts = {'mondelez':mondelez_main}
        try:
            function = docx_accounts[self.account.lower()]
        except:
            raise NotImplementedError(F"This {self.account} account is not yet implemented in single url functionality")
        return function(file)