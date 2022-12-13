from django.views.generic.base import TemplateView
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib import messages
from django.utils.safestring import mark_safe

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.parsers import FormParser, MultiPartParser, FileUploadParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from django.utils.encoding import smart_str

import jwt, logging, os, datetime, calendar, csv
from jwt import ExpiredSignatureError

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.utils import jwt_decode_handler

from .utils import Calendar
from .forms import CustomUserCreationForm, CustomUserChangeForm, HolidayForm, SchoolForm, CramSchoolSelectForm
from .models import User as UserModel
from .models import Attendance as AttendanceModel
from .models import CardScan as CardScanModel
from .models import Holiday as HolidayModel
from .models import School as SchoolModel
from attendance import services, pagination
from .serializers import UserSerializer, AttendanceSerializer, HolidaySerializer, CardLogSerializer, SchoolSerializer
from bot import constants

logger = logging.getLogger('general')

"""
    =================
    CLASS BASED VIEWS
    =================
    classes that connect the urls from urls.py and the services.py
    in charge of deciding which html pages go with what backend service
"""

class AllowStaffOnly(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class AllowSuperuserOnly(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class DontAllowStudents(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.exclude(name='Students').exists() \
                or self.request.user.is_staff or self.request.user.is_superuser
class IndexTemplateView(TemplateView):

    def get_template_names(self):
        template_name = "index.html"
        return template_name

class TimeoutPage(TemplateView):
    def get_template_names(self):
        template_name = "timeout"

class UserList(LoginRequiredMixin, generics.ListCreateAPIView,AllowSuperuserOnly):
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)
    pagination_class = pagination.BiggerPagination
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'attendance/user_list.html'

    def get_queryset(self):
        user_list = services.get_students_and_teachers_list(self.request.user)
        return self.paginate_queryset(user_list)

    def get(self, request, format = None):
        try:
            user_list = self.get_queryset()
            serializer = UserSerializer(user_list, many = True)
            return self.get_paginated_response(serializer.data)
        except ExpiredSignatureError as e:
            context = {'error' : constants.token_expiration }
            return Response(context)
    
    def post(self, request, format=None):
        print(request.POST.get('filter'))
        user_list = services.search_user(request.POST.get('query'), request.POST.get('filter'), self.request.user)
        paginated = self.paginate_queryset(user_list)
        serializer = UserSerializer(paginated, many = True)
        return self.get_paginated_response(serializer.data)

class UserImport(LoginRequiredMixin, AllowSuperuserOnly, APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes  = [TemplateHTMLRenderer]
    parser_classes = (MultiPartParser, FileUploadParser)
    template_name = 'attendance/csv_import.html'

    def get(self, request, format = None):
        form = CramSchoolSelectForm()
        return Response(status = status.HTTP_200_OK, data = {'form':form}) 

    def post(self, request, format = None):
        errors = ""
        form = CramSchoolSelectForm(request.POST)
        try:
            print(request.POST)
            csv_file = request.FILES['file']
            user_group = request.POST.get('user_group')
            cramschool_id = request.POST.get('cramschool')
        except MultiValueDictKeyError as e:
            csv_file = None
        if csv_file is None:
            messages.error(request, "ファイルをアップロードしてください。")
        elif not csv_file.name.endswith('.csv'):
            messages.error(request, "インポートされたファイルはCSVファイルではありませんでした。") 
        else:
            response = services.import_users(csv_file, user_group, cramschool_id)
            if response == True:
                messages.success(request, "CSVが正常にインポートされました.")
                return redirect('user-list')
            else:
                messages.error(request, response)
            # TODO: IF WANT TO BE ON BG, change to the celery task to use redis
            # err = services.import_users_csv(csv_file, user_group, request)
            # if err is None:
            #     messages.info(request, "インポートを処理しています。完了すると、メールで通知します。")
            #     return redirect('index')
            # else:
            #     messages.error(request, err)
        return Response(status = status.HTTP_200_OK, data = {'form':form})


class UserDetail(LoginRequiredMixin, AllowStaffOnly, APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes  = [TemplateHTMLRenderer]
    template_name = 'attendance/user.html'
    parser_classes = (FormParser, MultiPartParser)

    def get_object(self, id):
        try: 
            return services.get_user_restrict(id, self.request.user)
        except UserModel.DoesNotExist:
            raise Http404
    
    def get(self, request, id, format = None):
        user = self.get_object(id)
        if self.request.user.is_superuser:
            form = CustomUserChangeForm(instance=user, **{'user': self.request.user})
        else:
            form = CustomUserChangeForm(instance=user, initial = {'cramschool': self.request.user.cramschool}, **{'user': self.request.user} )

        user_group = user.groups.all()[0]
        print(f"userid:{user.id}")
        return Response(status = status.HTTP_200_OK, \
                template_name = 'registration/sign_up.html', data = {'form':form, 'user_group':user_group, 'changing_user_id': user.id})

    def post(self, request, id = None, format = None):
        if request.POST.get('delete'):
            self.delete(request, id)
            messages.success(request, "ユーザを削除しました。")
            return redirect('user-list')
        user = self.get_object(id)
        form = CustomUserChangeForm(request.POST, instance = user, **{'user': self.request.user})
        if form.is_valid():
            instance = form.save(commit = False)
            entered_school_id = str(form.cleaned_data.get('id_number')).zfill(7)
            if not self.request.user.is_superuser:
                instance.cramschool = self.request.user.cramschool
                instance.username = entered_school_id+str(self.request.user.cramschool.id)
            else:
                instance.username = entered_school_id+str(form.cleaned_data.get('cramschool'))
            instance.groups.clear()
            if not request.user.is_staff:
                instance.groups.add(Group.objects.get(name='Students'))
            else:
                instance.groups.add(Group.objects.get(name=form.cleaned_data.get('user_type')))
            instance.save()
            messages.success(request, "ユーザ情報を変更しました。")
            return redirect('user-list')
        else:
            print(form.errors)
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("An error in the form is found.")
                messages.error(request,"登録された情報は問題がありました。")
            return Response(status = status.HTTP_200_OK, template_name = 'registration/sign_up.html', data = {'form':form, 'changing_user_id': user.id})

    def delete(self, request, id, format = None):
        self.get_object(id).delete()

class UserRegister(LoginRequiredMixin, AllowStaffOnly,APIView):
    renderer_classes  = [TemplateHTMLRenderer]
    parser_classes = (FormParser, MultiPartParser)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if self.request.user.is_superuser:
            form = CustomUserCreationForm(**{'user': self.request.user})
        else:
            form = CustomUserCreationForm(initial = {'cramschool': self.request.user.cramschool}, **{'user': self.request.user} )
        return Response(status = status.HTTP_200_OK, template_name = 'registration/sign_up.html', data = {'form':form, 'changing_user_id': None})

    def post(self, request):
        form = CustomUserCreationForm(request.POST, **{'user': self.request.user})
        if form.is_valid():
            user = form.save(commit = False)
            # if not self.request.user.is_superuser:
            #     user.cramschool = self.request.user.cramschool
            # user.username = form.cleaned_data.get('id_number')
            entered_school_id = user.id_number.zfill(7)
            if not self.request.user.is_superuser:
                user.cramschool = self.request.user.cramschool
                user.username = entered_school_id+str(self.request.user.cramschool.id)
            else:
                user.username = entered_school_id+str(form.cleaned_data.get('cramschool'))
            user.password = make_password(settings.DEFAULT_PASS)
            user.save()
            if not request.user.is_staff:
                user.groups.add(Group.objects.get(name='Students'))
            else:
                user.groups.add(Group.objects.get(name=form.cleaned_data.get('user_type')))
            messages.success(request, "ユーザを登録しました。")
            user.save()
            return redirect('user-list')
        else:
            print(form.errors)
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("An error in the submitted user form is found.")
                logger.info(e)
                messages.error(request,"登録された情報は問題がありました。")
            return Response(status = status.HTTP_200_OK, template_name = 'registration/sign_up.html', data = {'form':form, 'changing_user_id': None})

class Attendance(LoginRequiredMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get_student(self, id):
        try:
            return services.get_user_restrict(id, self.request.user)
        except UserModel.ObjectDoesNotExist:
            raise Http404

    def get(self, request, id, format = None):
        student = self.get_student(id)
        attendance = AttendanceModel.objects.filter(user = student)
        serializer = AttendanceSerializer(attendance, many = True)
        return Response(serializer.data)

class CardScan(APIView):
    ### TODO: add shortname in url to indicate which cram school the card was scanned
    ### TODO: add cramschool field in CardLogs
    parser_classes = [FormParser]
    permission_classes = (AllowAny,)
    # permission_classes = (IsAuthenticated,)
    # authentication_classes = [BasicAuthentication, SessionAuthentication]

    def post(self, request, short_name= None, format = None):
        logger.info("=" * 20 + " SCANNING CARD " + "=" * 20)
        logger.info(f"DETECTED CARD ID:{request.data['cid']}")
        
        card = CardScanModel(request.POST.get('tid', None), request.data['cid'], request.POST.get('typ', None), request.data['tim'], request.POST.get('sts', None))

        if short_name is None:
            logger.info("Invalid cramschool short name. Check request URL.")
            return Response(status = status.HTTP_400_BAD_REQUEST)
        
        card_scan = services.scan_card(card, short_name)

        if card_scan:
            data = "res=00\r\nsnd=1001\r\nlmp=01\r\nfnc=00"
            content_type = "text/plain;charset=Shift_JIS"
            # Django's HttpResponse is used instead of DRF's Response because the new lines above 
            # do not render properly with the latter which resulted to an error in the reader 
            return HttpResponse(data, content_type = content_type)
        else:
            return Response(status = status.HTTP_400_BAD_REQUEST)


    def get(self, request, short_name= None,format = None):
        cards = services.get_latest_unregistered_card_scan_logs(self.request.user)
        serializer = CardLogSerializer(cards, many = True)
        return Response(serializer.data)

class HolidaysApi(LoginRequiredMixin, AllowSuperuserOnly, generics.RetrieveUpdateDestroyAPIView):
    parser_classes = (FormParser, MultiPartParser)
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = (IsAuthenticated,)
    pagination_class = pagination.BiggerPagination

    def get_object(self, id):
        try: 
            return HolidayModel.objects.get(pk = id)
        except HolidayModel.DoesNotExist:
            raise Http404

    def get_queryset(self):
        holidays = services.get_holidays()
        return self.paginate_queryset(holidays)

    def post(self, request, id = None, format = None):
        if request.POST.get('delete'):
            self.delete(request, id, format)
            messages.success(request, "祝日を削除しました。")
            return Response(status = status.HTTP_204_NO_CONTENT)
        holiday = self.get_object(id)
        form = HolidayForm(request.POST, instance = holiday)
        if form.is_valid():
            form.save()
            messages.success(request, "祝日を変更しました。")
            return redirect('holidays-list')
        else:
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("The error is something else.")
                messages.error(request,"すでに存在済み祝日です。")
            return render(request, 'attendance/holidays_page.html', {'form': form, 'error': True })
    
    def delete(self, request, id = None, format = None):
        if request.POST.get('deleteAll'):
            HolidayModel.objects.all().delete()
        else:
            self.get_object(id).delete()
        
    def get(self, request, id = None, format = None):
        logger.info("retrieving holidays")
        holidays = self.get_queryset()
        holidays_serializer = HolidaySerializer(holidays, many = True)
        return self.get_paginated_response(holidays_serializer.data)

class HolidaysPage(LoginRequiredMixin, AllowSuperuserOnly, generics.ListCreateAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    parser_classes = (FormParser, MultiPartParser)
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    template_name = 'attendance/holidays_page.html'

    def post(self, request):
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "祝日を追加しました。")
            return redirect('holidays-list')
        else:
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("An error in the submitted holiday form is found.")
                messages.error(request,"すでに存在済み祝日です。")
            return Response(status = status.HTTP_400_BAD_REQUEST, data = {'form':form, 'error': True})

    def get(self, format = None):
        form = HolidayForm()
        return Response(status = status.HTTP_200_OK, data = {'form':form})

class SchoolApi(LoginRequiredMixin, AllowStaffOnly, generics.RetrieveUpdateDestroyAPIView):
    parser_classes = (FormParser, MultiPartParser)
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = (IsAuthenticated,)
    pagination_class = pagination.BiggerPagination

    def get_object(self, id):
        try: 
            return SchoolModel.objects.get(pk = id)
        except SchoolModel.DoesNotExist:
            raise Http404

    def get_queryset(self):
        schools = services.get_schools()
        return self.paginate_queryset(schools)

    def post(self, request, id = None, format = None):
        if request.POST.get('delete'):
            self.delete(request, id, format)
            messages.success(request, "学校を削除しました。")
            return Response(status = status.HTTP_204_NO_CONTENT)
        school = self.get_object(id)
        form = SchoolForm(request.POST, instance = school)
        if form.is_valid():
            form.save()
            messages.success(request, "学校を変更しました。")
            return redirect('schools-list')
        else:
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("The error is something else.")
                messages.error(request,"すでに存在済み学校です。")
            return render(request, 'attendance/schools_page.html', {'form': form, 'error': True })
    
    def delete(self, request, id = None, format = None):
        if request.POST.get('deleteAll'):
            HolidayModel.objects.all().delete()
        else:
            self.get_object(id).delete()
        
    def get(self, request, id = None, format = None):
        logger.info("retrieving schools")
        schools = self.get_queryset()
        schools_serializer = SchoolSerializer(schools, many = True)
        return self.get_paginated_response(schools_serializer.data)
class SchoolPage(LoginRequiredMixin, AllowStaffOnly, generics.ListCreateAPIView):
    pass 

class HolidaysImport(LoginRequiredMixin, AllowSuperuserOnly, APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes  = [TemplateHTMLRenderer]
    parser_classes = (MultiPartParser, FileUploadParser)
    template_name = "attendance/csv_import.html"

    def get(self, request, format = None):
        if not request.user.is_authenticated:
            return redirect('login')
        return Response(status = status.HTTP_200_OK)

    def post(self, request, format = None):
        try:
            csv_file = request.FILES['file']
        except MultiValueDictKeyError as e:
            csv_file = None
        flag = request.POST.get('replace_all')
        flag = True if flag is not None and eval(flag) else False
        if csv_file is None:
            messages.error(request, "ファイルをアップロードしてください。")
        elif not csv_file.name.endswith('.csv'):
            messages.error(request, "インポートされたファイルはCSVファイルではありませんでした。")
        else:
            response = services.import_holidays(csv_file, flag)
            if response == True:
                messages.success(request, "CSVが正常にインポートされました.")
                return redirect('holidays-list')
            else:
                messages.error(request, response)
        return Response(status = status.HTTP_200_OK)

class AttendancePage(generics.ListAPIView):
    """
        Shows the attendance page of a user

        Prerequisites:  
            > an access token obtained through a request made in the is needed to access the page
    """
    authentication_classes = [JSONWebTokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = (AllowAny,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'attendance/attendance_list.html'

    def get(self, request, id, token = None, format = None):
        user_id = ""
        # allow access to the page if the users has:
        # a jwt token or is authenticated
        try:
            # if token is not None:
            #     decoded = jwt_decode_handler(token)
            #     user_id = decoded['user_id']
            #     got_user = services.get_user(pk = user_id)
            #     user = authenticate(username = got_user.username, password = settings.DEFAULT_PASS)
            #     if user is not None:
            #         login(request, user)
            #     else:
            #         raise PermissionDenied() 
            # elif request.user.is_authenticated:
            #     user_id = request.user.id
            # else:
            #     raise PermissionDenied()

            if token is not None:
                got_user = services.get_user(line_userid = token)
                user_id = got_user.id
                user = authenticate(username = got_user.username, password = settings.DEFAULT_PASS)
                if user is not None:
                    login(request, user)
                else:
                    raise PermissionDenied() 
            elif request.user.is_authenticated:
                user_id = request.user.id
            else:
                raise PermissionDenied()

            attendance_record = services.get_attendance_list(id, user_id).order_by('-date')
            queried_user = services.get_user_restrict(id, self.request.user)
            holidays = HolidayModel.objects.all().order_by('-date')
            month = int(request.GET.get('month', None)) if request.GET.get('month', None) is not None else None
            year = int(request.GET.get('year', None)) if request.GET.get('year', None) is not None else None
            
            if month is None and year is None:
                date_now = datetime.datetime.today()
            else:
                date_now = datetime.date(year, month, 1)
            
            nm = services.get_next_month(date_now)
            pm = services.get_prev_month(date_now)
            month_links = {'next_month':nm, 'prev_month':pm, 'now':date_now}
            
            cal = Calendar(date_now.year, date_now.month)
            html_cal = cal.formatmonth(withyear=True, attendance_records=attendance_record, holiday=holidays)
            
            return Response(status = status.HTTP_200_OK, data = {'calendar' : mark_safe(html_cal), 'month_data': month_links, 'queried_user':queried_user} )

        # except ExpiredSignatureError as e:
        #     logger.info(e)
        #     messages.error(request, constants.token_expiration)
        #     logout(request)
        #     return redirect('attendance_list', id_number=id_number)
        except ValueError as e:
            logger.info(e)
            raise Http404
        
            
        

class AttendanceStudentList(generics.ListAPIView):
    """
        Shows the list of students that a recipient is connected with.
        
        Prerequisites: 
            > an access token obtained through a request made in the bot is needed to access the page
    """
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = (AllowAny,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'attendance/recipient_linked.html'
    pagination_class = pagination.BasicPagination

    def get_queryset(self, user_id):
        student_list = services.get_student_list(user_id)
        return self.paginate_queryset(student_list)

    # def get(self, request, token, format = None):
    #     try:
    #         decoded = jwt_decode_handler(token)
    #         got_user = services.get_user(pk = decoded['user_id'])
    #         user = authenticate(username = got_user.username, password = settings.DEFAULT_PASS)
    #         if user is not None:
    #             login(request, user)
    #             student_list = self.get_queryset(decoded['user_id'])
    #             serializer = UserSerializer(student_list, many = True)
    #             return self.get_paginated_response(serializer.data)
    #         else:
    #             raise PermissionDenied()
    #     except ExpiredSignatureError as e:
    #         context = {'error' : constants.token_expiration }
    #         return Response(context)

    def get(self, request, line_userid, format = None):
        got_user = services.get_user(line_userid = line_userid)
        user = authenticate(username = got_user.username, password = settings.DEFAULT_PASS)
        if user is not None:
            login(request, user)
            student_list = self.get_queryset(got_user.id)
            serializer = UserSerializer(student_list, many = True)
            return self.get_paginated_response(serializer.data)
        else:
            raise PermissionDenied()


class AttendanceExport(LoginRequiredMixin, AllowStaffOnly, APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes  = [TemplateHTMLRenderer]
    parser_classes = (FormParser, MultiPartParser)
    template_name = 'attendance/csv_export.html'

    def get(self, request, id = None, format = None):
        if not request.user.is_authenticated:
            return redirect('login')
        if id is not None:
            try:
                user = UserModel.objects.get(pk = id)
                serializer = UserSerializer(user)
            except UserModel.DoesNotExist as e:
                logger.info(f"User does not exist: {e}")
                messages.error("ユーザが存在しません。")
                raise Http404
            return Response(status = status.HTTP_200_OK, data = {'user_data' : serializer.data} )
        else:
            raise Http404

    def post(self, request, id, format = None):
        string_year_month = request.POST.get('month_year', None)
        month_year = datetime.datetime.strptime(string_year_month, "%Y-%m")
        response = services.export_attendance(month_year, id)
        return response

class PasswordChange(AllowStaffOnly, LoginRequiredMixin, APIView):
    renderer_classes = [TemplateHTMLRenderer]
    parser_classes = (FormParser, MultiPartParser)
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    template_name = 'registration/change_password.html'

    # def test_func(self):
    #     return self.request.user.is_superuser

    def get_object(self, id_number):
        try: 
            return UserModel.objects.get(id_number = id_number)
        except UserModel.DoesNotExist:
            raise Http404

    def get(self, request, format = None):
        form = PasswordChangeForm(request.user)
        return Response(status = status.HTTP_200_OK, data = {'form': form})
    
    
    def post(self, request, format = None):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'パスワードを変更しました。')
            return redirect('index')
        else:
            messages.error(request, '下記のエラーを修正してください。')
        return Response(status = status.HTTP_200_OK, data = {'form': form})

class CardLogsView(AllowSuperuserOnly,generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = pagination.BiggerPagination
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'attendance/card_logs.html'

    def get_queryset(self):
        logs = services.get_card_logs()
        return self.paginate_queryset(logs)

    def get(self, request, format = None):
        logs = self.get_queryset()
        serializer = CardLogSerializer(logs, many = True)
        return self.get_paginated_response(serializer.data)
class SchoolList(LoginRequiredMixin, generics.ListCreateAPIView,AllowStaffOnly):
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)
    pagination_class = pagination.BiggerPagination
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'attendance/school_list.html'

    def get_queryset(self):
        schools = services.get_schools(self.request.user)
        return self.paginate_queryset(schools)

    def get(self, request, format = None):
        try:
            schools = self.get_queryset()
            serializer = SchoolSerializer(schools, many = True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            context = {'error' : "エラーがありました。" }
            return Response(context)
    
    def post(self, request, format=None):
        print(request.POST.get('filter'))
        user_list = services.search_user(request.POST.get('query'), request.POST.get('filter'), self.request.user)
        paginated = self.paginate_queryset(user_list)
        serializer = UserSerializer(paginated, many = True)
        return self.get_paginated_response(serializer.data)


class SchoolDetail(LoginRequiredMixin, AllowStaffOnly, APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes  = [TemplateHTMLRenderer]
    template_name = 'attendance/school.html'
    parser_classes = (FormParser, MultiPartParser)
    template_name = 'attendance/school.html'

    def get_object(self, code):
        try: 
            return SchoolModel.objects.get(pk = code)
        except SchoolModel.DoesNotExist:
            raise Http404
    
    def get(self, request, code=None, format = None):
        if code is not None:
            school = self.get_object(code)
            form = SchoolForm(instance=school, **{'user': self.request.user})
            changing_school_code = school.school_code
        else:
            changing_school_code = None
            if self.request.user.is_superuser:
                form = SchoolForm(**{'user': self.request.user})
            else:
                form = SchoolForm(**{'user': self.request.user}, initial = {'cramschool': self.request.user.cramschool})
        return Response(status = status.HTTP_200_OK, \
                template_name = 'attendance/school.html', data = {'form':form, 'changing_school_code': changing_school_code})

    def post(self, request, code = None, format = None):
        if request.POST.get('delete'):
            self.delete(request, code)
            messages.success(request, "学校を削除しました。")
            return redirect('schools-list')
        if code is not None:
            school = self.get_object(code)
            form = SchoolForm(request.POST, instance = school, **{'user': self.request.user})
            changing_school_code = school.school_code
            messages.success(request, "学校情報を変更しました。")
        else:
            print("creating new school...")
            changing_school_code = None
            form = SchoolForm(request.POST, **{'user': self.request.user})
            messages.success(request, "学校情報を登録しました。")
        if form.is_valid():
            print("saving school details...")
            if self.request.user.is_superuser:
                form.save()
            else: 
                school = form.save(commit = False)
                school.cramschool = self.request.user.cramschool
                school.save()
            return redirect('schools-list')
        else:
            print(form.errors)
            try:
                for field in form.errors:
                    form[field].field.widget.attrs['class'] += ' is-invalid'
            except KeyError as e:
                logger.info("An error in the form is found.")
            messages.error(request,"登録された情報は問題がありました。")
            return Response(status = status.HTTP_200_OK, template_name = 'attendance/school.html', data = {'form':form, 'changing_school_code': changing_school_code})

    def delete(self, request, code, format = None):
        self.get_object(code).delete()