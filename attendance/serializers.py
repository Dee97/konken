from rest_framework import serializers
from .models import User, Attendance, Holiday, CardLog, YearLevel, School, SchoolDivision

class YearLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearLevel

class SchoolDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolDivision

class UserSerializer(serializers.ModelSerializer):
    year_level_name = serializers.CharField(source='year_level.year_level_name1', read_only=True)
    class Meta:
        model = User
        fields = [
                    'id',
                    'id_number',
                    'first_name',
                    'last_name', 
                    'line_userid',
                    'line_username',
                    'card_id',
                    'birthdate',
                    'year_level_name',             
                ]

class SchoolSerializer(serializers.ModelSerializer):
    level_division_name = serializers.CharField(source='level_division.division_name', read_only=True)
    class Meta:
        model = School
        fields = [
                    'school_code',
                    'school_name',
                    'level_division_name',
                    'level_division'
                ]

class RegisterUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = [
                    'id_number',
                    'first_name',
                    'last_name', 
                    'line_userid',
                    'line_username',
                    'card_id',
                    'birthdate',              
                ]

class AttendanceSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Attendance
        fields = [
                    'date',
                    'time_in',
                    'time_out',
                    'user',
                    'remarks'
                ]

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = [
                    'id',
                    'date',
                    'name',
                    'remarks'
                ]

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['school_code', 'school_name', 'level_division']
class CardLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardLog
        fields = [  
                    'date',
                    'time',
                    'card_id'
                ]