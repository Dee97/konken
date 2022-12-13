from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from .models import Question, Answer, Attendance, PushRecipients, Holiday, CardLog, School, SchoolDivision, YearLevel, CramSchool
from .models import User as CustomUser

"""
    Register other models in the app
"""

admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(CardLog)

admin.site.site_header = "Konken Administration"
admin.site.site_title = "Konken Attendance Administration"
admin.site.index_title = "Konkenへようこそ"

"""
    Customizes and registers the model in the super admin view.
"""

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
    class Meta:
        model = CustomUser
        fields = ('username', 'id_number')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(label=("パスワード"),
        help_text=("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"../password/\">this form</a>."))
    
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['year_level'].required = False
        self.fields['school'].required = False
        self.fields['cramschool'].required = False

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'is_active', 'is_staff','is_superuser', 'id_number', 'card_id','first_name', 'last_name','first_name_kana', 'last_name_kana', 'birthdate', 'year_level', 'postal_code', 'address_1', 'address_2', 'telephone_num', 'mobile_num_1', 'mobile_num_2', 'email','line_userid', 'line_username', 'sex', 'school', 'cramschool' )

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class CustomUserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('get_groups','id_number', 'card_id', 'last_name', 'first_name', 'birthdate', 'cramschool','line_username','is_active')
    list_filter = ('is_active', 'is_staff', 'groups', 'sex', 'cramschool')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('個人情報', {'fields': ('last_name', 'first_name', 'last_name_kana', 'first_name_kana', 'birthdate', 'sex' )}),
        ('学校情報', {'fields': ('id_number', 'card_id','year_level', 'school', 'cramschool')}),
        ('連絡情報', {'fields': ('postal_code', 'address_1', 'address_2', 'telephone_num', 'mobile_num_1', 'mobile_num_2', 'email')}),
        ('LINE情報', {'fields': ('line_username', 'line_userid')}),
        ('許可', {'fields': ('groups', 'is_staff', 'is_active', 'is_superuser', 'user_permissions')})
    )

    search_fields = ('username',)
    ordering = ('id_number',)
    filter_horizontal = ()

    def get_groups(self, obj):
        if obj.groups.first() is not None:
            return obj.groups.first().name
        else:
            ""
    get_groups.short_description = 'Groups'

# Now register the new UserAdmin...
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'time_in', 'time_out')

@admin.register(PushRecipients)
class PushRecipientsAdmin(admin.ModelAdmin):
    list_display = ('trigger', 'recipient')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')

@admin.register(SchoolDivision)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('division', 'division_name')

@admin.register(YearLevel)
class YearLevelAdmin(admin.ModelAdmin):
    list_display = ('year_level', 'level_division', 'year_level_name1', 'year_level_name2', 'year_level_name3')

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('school_code', 'school_name', 'level_division')

@admin.register(CramSchool)
class CramschoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'address', 'contact_number')