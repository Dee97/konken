from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.forms import ModelForm
from .models import User, Holiday, YearLevel, School, SchoolDivision, CramSchool
from bot import constants

GROUP_CHOICES = [('Students', '生徒'), ('Teachers', '先生')]

DEFAULT_ERRORS = {
    'required': 'このフィールドは必須です。',
    'invalid': '有効な値を入力してください。',
    'unique': 'このID番号はすでに存在します。'
}

class SchoolForm(ModelForm):
    school_name = forms.CharField(max_length=100, required=True, help_text = "Required", label="学校名",widget=forms.TextInput(attrs={'placeholder': '学校名','class': 'form-control',}))
    # school_code = forms.IntegerField(max_value=99999, min_value=1, required=True, label="学校CD",widget=forms.TextInput(attrs={'placeholder': '学年CD','class': 'form-control',}))
    level_division = forms.ModelChoiceField(queryset = SchoolDivision.objects.all(), to_field_name = "division", empty_label = "学校区分を選択してください",label="学校区分",required = True, widget=forms.Select(attrs={'class':'form-control'}))
    cramschool = forms.ModelChoiceField(queryset = CramSchool.objects.all(), to_field_name = "id", empty_label = "塾を選択してください",label="塾名",required = True, widget=forms.Select(attrs={'class':'form-control'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(SchoolForm,self).__init__(*args, **kwargs)
        if user.is_superuser:
            self.fields['cramschool'].queryset = CramSchool.objects.all()
        else:
            print("called here")
            self.fields['cramschool'].queryset = CramSchool.objects.filter(id = user.cramschool.id)

    class Meta:
        model = School
        fields = ['school_name', 'level_division', 'cramschool']

class HolidayForm(ModelForm):
    

    date = forms.DateField(required=True, label="日付", widget=forms.DateInput(format=('%Y-%m-%d'), attrs={'class':'form-control', 'type':'date'}),)
    name = forms.CharField(max_length=50, required=True, help_text = "Required", label="祝日名",widget=forms.TextInput(attrs={'placeholder': '祝日名','class': 'form-control',}))
    remarks = forms.CharField(max_length=100, required=False, help_text = "Required", label="備考",widget=forms.TextInput(attrs={'placeholder': '備考','class': 'form-control',}))

    class Meta:
        model = Holiday
        fields = ['date', 'name', 'remarks']

class SchoolForm(ModelForm):
    school_code = forms.IntegerField(max_value=5000, min_value=1, required=True, label="学校CD",widget=forms.TextInput(attrs={'placeholder': '学校CD','class': 'form-control',}))
    school_name = forms.CharField(max_length=100, required=False, help_text = "必要", label="学校名",widget=forms.TextInput(attrs={'placeholder': '学校名','class': 'form-control',}))
    level_division = forms.ModelChoiceField(queryset = SchoolDivision.objects.all(), label="学年", empty_label = "学校区分を選択してください", required = True, widget=forms.Select(attrs={'class':'form-control'}))

    class Meta:
        model = Holiday
        fields = ['school_code', 'school_name', 'level_division']

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False, label='名',widget=forms.TextInput(attrs={'placeholder': '名','class': 'form-control',}))
    last_name = forms.CharField(max_length=50, required=False, label='姓',widget=forms.TextInput(attrs={'placeholder': '姓','class': 'form-control',}))
    first_name_kana = forms.CharField(max_length=50, required=False, label="名カナ",widget=forms.TextInput(attrs={'placeholder': '名カナ','class': 'form-control',}))
    last_name_kana = forms.CharField(max_length=50, required=False, label="姓カナ",widget=forms.TextInput(attrs={'placeholder': '姓カナ','class': 'form-control',}))
    id_number = forms.CharField(max_length=7, required=True, help_text = "必要", label="生徒番号",error_messages = DEFAULT_ERRORS, widget=forms.TextInput(attrs={'placeholder': '生徒番号','class': 'form-control',}))
    card_id = forms.CharField(max_length=100, required=True, help_text = "Required", label="カードID",widget=forms.TextInput(attrs={'placeholder': 'カードID','class': 'form-control'}))
    # year_level = forms.IntegerField(max_value=12, min_value=1, required=False, label="学年",widget=forms.TextInput(attrs={'placeholder': '学年','class': 'form-control',}))
    year_level = forms.ModelChoiceField(queryset = YearLevel.objects.all(), to_field_name = "year_level_name1", empty_label = "学年を選択してください",label="学年",required = False, widget=forms.Select(attrs={'class':'form-control'}))
    school = forms.ModelChoiceField(queryset=School.objects.all(), to_field_name = "school_code", label="学校", empty_label = "学校を選択してください",required = False,widget=forms.Select(attrs={'class':'form-control'}))
    postal_code = forms.CharField(max_length = 50, required=False,label = "郵便番号",widget=forms.TextInput(attrs={'placeholder': '郵便番号','class': 'form-control',}))
    address_1 = forms.CharField(max_length = 100, required=False,label="住所１",widget=forms.TextInput(attrs={'placeholder': '住所１','class': 'form-control',}))
    address_2 = forms.CharField(max_length = 100, required=False,label="住所2",widget=forms.TextInput(attrs={'placeholder': '住所２','class': 'form-control',}))
    telephone_num = forms.CharField(max_length = 50, required=False,label="電話番号",widget=forms.TextInput(attrs={'placeholder': '電話番号','class': 'form-control',}))
    mobile_num_1 = forms.CharField(max_length = 100, required=False,label="携帯番号１",widget=forms.TextInput(attrs={'placeholder': '携帯番号１','class': 'form-control',}))
    mobile_num_2 = forms.CharField(max_length = 100, required=False,label="携帯番号2",widget=forms.TextInput(attrs={'placeholder': '携帯番号２','class': 'form-control',}))
    email = forms.EmailField(required=False,label="メールアドレス",widget=forms.TextInput(attrs={'placeholder': 'メールアドレス','class': 'form-control',}))
    username = forms.CharField(max_length=150, required=False, label='username',widget=forms.TextInput(attrs={'placeholder': 'username','class': 'form-control',}))
    password1 = forms.CharField(max_length=32, widget=forms.PasswordInput(attrs={'id':'password1'}))
    password2 = forms.CharField(max_length=32, widget=forms.PasswordInput(attrs={'id':'password2'}))
    birthdate = forms.DateField(required=False, label="生年月日", widget=forms.DateInput(format=('%Y-%m-%d'), attrs={'class':'form-control', 'type':'date'}),)
    user_type = forms.CharField(label='ユーザタイプ', widget=forms.Select(choices=GROUP_CHOICES, attrs={'class':'form-control'}))
    sex = forms.ChoiceField(choices=constants.SEX_CHOICES, widget=forms.RadioSelect(attrs={'class': ''}))
    printed_card_id = forms.CharField(max_length=10, required=True, help_text = "必要", label="印刷したカードID",error_messages = DEFAULT_ERRORS, widget=forms.TextInput(attrs={'placeholder': '印刷したカードID','class': 'form-control',}))
    cramschool = forms.ModelChoiceField(queryset = CramSchool.objects.all(), to_field_name = "id", empty_label = "塾を選択してください",label="塾名",required = True, widget=forms.Select(attrs={'class':'form-control'}))
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'first_name_kana', 'id_number','card_id', 'last_name_kana', 'year_level', 'postal_code', 'address_1', 'address_2', 'telephone_num', 'mobile_num_1', 'mobile_num_2', 'email', 'username', 'password1', 'password2', 'birthdate', 'user_type', 'sex', 'school','printed_card_id', 'cramschool')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CustomUserCreationForm,self).__init__(*args, **kwargs)
        if user.is_superuser:
            self.fields['school'].queryset = School.objects.all()
        else:
            print("called here")
            self.fields['school'].queryset = School.objects.filter(cramschool = user.cramschool.id)


class CustomUserChangeForm(UserChangeForm):
    first_name = forms.CharField(max_length=50, required=False, label='名',widget=forms.TextInput(attrs={'placeholder': '名','class': 'form-control',}))
    last_name = forms.CharField(max_length=50, required=False, label='姓',widget=forms.TextInput(attrs={'placeholder': '姓','class': 'form-control',}))
    first_name_kana = forms.CharField(max_length=50, required=False, label="名カナ",widget=forms.TextInput(attrs={'placeholder': '名カナ','class': 'form-control',}))
    last_name_kana = forms.CharField(max_length=50, required=False, label="姓カナ",widget=forms.TextInput(attrs={'placeholder': '姓カナ','class': 'form-control',}))
    id_number = forms.CharField(max_length=7, required=True, help_text = "Required", label="生徒番号", error_messages = DEFAULT_ERRORS, widget=forms.TextInput(attrs={'placeholder': '生徒番号','class': 'form-control',}))
    card_id = forms.CharField(max_length=100, required=True, help_text = "Required", label="カードID",widget=forms.TextInput(attrs={'placeholder': 'カードID','class': 'form-control'}))
    # year_level = forms.IntegerField(max_value=12, min_value=1,required=False, label="学年",widget=forms.TextInput(attrs={'placeholder': '学年','class': 'form-control',}))
    postal_code = forms.CharField(max_length = 50, required=False,label = "郵便番号",widget=forms.TextInput(attrs={'placeholder': '郵便番号','class': 'form-control',}))
    address_1 = forms.CharField(max_length = 100, required=False,label="住所１",widget=forms.TextInput(attrs={'placeholder': '住所１','class': 'form-control',}))
    address_2 = forms.CharField(max_length = 100, required=False,label="住所2",widget=forms.TextInput(attrs={'placeholder': '住所２','class': 'form-control',}))
    telephone_num = forms.CharField(max_length = 50, required=False,label="電話番号",widget=forms.TextInput(attrs={'placeholder': '電話番号','class': 'form-control',}))
    mobile_num_1 = forms.CharField(max_length = 100, required=False,label="携帯番号１",widget=forms.TextInput(attrs={'placeholder': '携帯番号１','class': 'form-control',}))
    mobile_num_2 = forms.CharField(max_length = 100, required=False,label="携帯番号2",widget=forms.TextInput(attrs={'placeholder': '携帯番号２','class': 'form-control',}))
    email = forms.EmailField(required=False,label="メールアドレス",widget=forms.TextInput(attrs={'placeholder': 'メールアドレス','class': 'form-control',}))
    username = forms.CharField(max_length=150, required=False, label='username',widget=forms.TextInput(attrs={'placeholder': 'username','class': 'form-control',}))
    password1 = forms.CharField(max_length=32, widget=forms.PasswordInput(attrs={'id':'password1'}))
    password2 = forms.CharField(max_length=32, widget=forms.PasswordInput(attrs={'id':'password2'}))
    birthdate = forms.DateField(required=False, label="生年月日", widget=forms.DateInput(format=('%Y-%m-%d'), attrs={'class':'form-control', 'placeholder':'Select a date', 'type':'date'}),)
    user_type = forms.CharField(label='ユーザータイプ', widget=forms.Select(choices=GROUP_CHOICES, attrs={'class':'form-control'}))
    sex = forms.ChoiceField(choices=constants.SEX_CHOICES, widget=forms.RadioSelect(attrs={'class': ''}))

    year_level = forms.ModelChoiceField(queryset = YearLevel.objects.all(), label="学年", empty_label = "学年を選択してください", required = False, widget=forms.Select(attrs={'class':'form-control'}))
    school = forms.ModelChoiceField(queryset=School.objects.all(), to_field_name = "school_code", label="学校", empty_label="学校を選択してください", required = False, widget=forms.Select(attrs={'class':'form-control'}))
    printed_card_id = forms.CharField(max_length=10, required=True, help_text = "必要", label="印刷したカードID",error_messages = DEFAULT_ERRORS, widget=forms.TextInput(attrs={'placeholder': '印刷したカードID','class': 'form-control',}))
    cramschool = forms.ModelChoiceField(queryset = CramSchool.objects.all(), to_field_name = "id", empty_label = "塾を選択してください",label="塾名",required = True, widget=forms.Select(attrs={'class':'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'first_name_kana', 'id_number','card_id', 'last_name_kana', 'year_level', 'postal_code', 'address_1', 'address_2', 'telephone_num', 'mobile_num_1', 'mobile_num_2', 'email', 'username', 'password1', 'password2', 'birthdate', 'user_type', 'sex', 'school', 'printed_card_id', 'cramschool')


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CustomUserChangeForm,self).__init__(*args, **kwargs)
        if user.is_superuser:
            self.fields['school'].queryset = School.objects.all()
        else:
            print("called here")
            self.fields['school'].queryset = School.objects.filter(cramschool = user.cramschool.id)

class CramSchoolSelectForm(forms.Form):
    cramschool = forms.ModelChoiceField(queryset = CramSchool.objects.all(), to_field_name = "id", empty_label = "塾を選択してください",label="塾名",required = True, widget=forms.Select(attrs={'class':'form-control'}))

        